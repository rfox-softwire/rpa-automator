# rpa_wikipedia_population.py
# This script uses Playwright to open Wikipedia,
# search for "France", and scrape the country's population.

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Launch browser (headless=True is default)
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Go to Wikipedia homepage
        await page.goto("https://www.wikipedia.org/")

        # 2. Enter "France" in the search box and submit
        await page.fill("input[name='search']", "France")
        await page.press("input[name='search']", "Enter")

        # 3. Wait for navigation to France article page
        await page.wait_for_selector("#firstHeading", state="visible")

        # 4. Locate the population field in the infobox.
        #    Wikipedia uses a table with class 'infobox'.
        #    The row containing "Population" usually has a span with
        #    text starting with "Population".
        try:
            # Try to find the cell that contains "Population (2023)" or similar
            population_cell = await page.query_selector(
                "//table[contains(@class,'infobox')]//tr[th[contains(.,'Population')]]/td"
            )
            if not population_cell:
                # Fallback: look for any td containing a number with "million" or "billion"
                population_cell = await page.query_selector(
                    "//table[contains(@class,'infobox')]//td[contains(text(),'million') or contains(text(),'billion')]"
                )

            if population_cell:
                population_text = await population_cell.inner_text()
                print(f"Population of France: {population_text.strip()}")
            else:
                print("Could not locate the population information.")
        except Exception as e:
            print(f"Error while extracting population: {e}")

        # 5. Clean up
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())