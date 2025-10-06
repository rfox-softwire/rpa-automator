import asyncio
from playwright.async_api import async_playwright

# --- Monitoring Code (Injected) ---
from playwright.sync_api import sync_playwright
from backend.services.playwright_monitor import monitor_playwright
import sys
import os
# Add the backend directory to the path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# Wrap the script in a monitoring context
if __name__ == '__main__':
    with monitor_playwright() as context:
        # rpa_wikipedia_population.py
        #
        # This script uses Playwright to open Wikipedia, search for "France",
        # and scrape the current population figure from the infobox.
        #
        # Requires:
        #   pip install playwright
        #   playwright install  # downloads browser binaries



        async def main():
            async with async_playwright() as p:
                # Launch a headless Chromium browser
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # 1️⃣ Open Wikipedia home page
                await page.goto("https://www.wikipedia.org/")

                # 2️⃣ Type "France" into the search input and press Enter
                await page.fill('input#searchInput', 'France')
                await page.press('input#searchInput', 'Enter')

                # 3️⃣ Wait for the article page to load
                await page.wait_for_selector('#mw-content-text', timeout=15000)

                # 4️⃣ Locate the population value in the infobox
                #    Wikipedia uses a table with class "infobox" and rows like
                #    <th>Population</th><td>~65,000,000</td>
                #    We'll search for the row that contains "Population"
                population_selector = (
                    "//table[contains(@class,'infobox')]//tr["
                    "contains(translate(.//th/text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'population')]/td[1]"
                )
                element_handle = await page.wait_for_selector(population_selector, timeout=10000)
                population_text = await element_handle.inner_text()

                # 5️⃣ Clean up the extracted text
                population_value = population_text.split('[')[0].strip()  # remove footnote refs

                print(f"Population of France (as shown on Wikipedia): {population_value}")

                await browser.close()


        if __name__ == "__main__":
            asyncio.run(main())