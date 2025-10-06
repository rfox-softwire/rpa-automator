import asyncio
from playwright.async_api import async_playwright

# --- Monitoring Code (Injected) ---
from playwright.sync_api import sync_playwright
from playwright_monitor import monitor_playwright


# --- Original Script ---
# -*- coding: utf-8 -*-
"""
Playwright script that opens Wikipedia, searches for "France",
and extracts the population figure from the infobox on the France page.
"""


async def main():
    # Launch a headless browser (set headless=False if you want to see it)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Go to Wikipedia
        await page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search box and submit
        await page.fill("input#searchInput", "France")
        await page.press("input#searchInput", "Enter")

        # 3. Wait for the France article to load
        await page.wait_for_selector("#firstHeading")

        # 4. Locate the population field in the infobox.
        #    Wikipedia uses a table with class 'infobox' and rows like:
        #    <th>Population</th><td>...<sup>...</sup></td>
        #    We'll extract the text from the first matching row that contains "Population".
        population_text = await page.evaluate("""
            () => {
                const infobox = document.querySelector('.infobox');
                if (!infobox) return null;
                const rows = Array.from(infobox.rows);
                for (const row of rows) {
                    const header = row.cells[0];
                    if (header && /Population/i.test(header.innerText)) {
                        // Return the text content of the second cell (the value)
                        return row.cells[1].innerText.trim();
                    }
                }
                return null;
            }
        """)

        # 5. Print the result
        if population_text:
            print(f"Population of France (as shown on Wikipedia): {population_text}")
        else:
            print("Could not find population data in the infobox.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())