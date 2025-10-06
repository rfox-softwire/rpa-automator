# playwright_population_france.py
import asyncio
from playwright.async_api import async_playwright

async def main():
    # Launch browser (headless by default)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Go to Wikipedia
        await page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search box and submit
        await page.fill('input#searchInput', 'France')
        await page.press('input#searchInput', 'Enter')

        # 3. Wait for the France article to load
        await page.wait_for_selector('#mw-content-text h1')  # ensures article header loaded

        # 4. Find the population value in the infobox
        # The population is usually inside a table row with span class "infobox-data" or directly under
        # We'll locate the first occurrence of 'Population' label and grab its following sibling.
        # This selector works for most current Wikipedia pages:
        population_selector = (
            "//th[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'population')]/following-sibling::td"
        )
        element = await page.query_selector(population_selector)
        if element:
            population_text = await element.inner_text()
            print(f"Population of France (as per Wikipedia): {population_text}")
        else:
            print("Could not find the population information.")

        # Close browser
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())