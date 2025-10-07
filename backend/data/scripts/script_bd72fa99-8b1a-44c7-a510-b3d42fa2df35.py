# rpa_wikipedia_population.py
# This script uses Playwright (Python) to navigate Wikipedia,
# search for "France", and extract the population figure from the infobox.

import asyncio
from playwright.async_api import async_playwright

async def main():
    # Launch a headless browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. Go to Wikipedia homepage
        await page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search box and submit
        # The search input has id 'searchInput'
        await page.fill("#searchInput", "France")
        await page.press("#searchInput", "Enter")

        # 3. Wait for the page to load (the title contains "France - Wikipedia")
        await page.wait_for_selector("h1#firstHeading >> text=France")

        # 4. Locate the population field in the infobox.
        # The infobox is a table with class 'infobox'
        # Population is typically inside a <span> or <div> that contains "Population" label
        # We'll use XPath to find the row containing "Population" and get its value.
        population_selector = "//table[contains(@class,'infobox')]//tr[td[1][contains(.,'Population')]]/td[last()]"
        await page.wait_for_selector(population_selector)

        # Extract the text content of that cell
        population_text = await page.inner_text(population_selector)
        print(f"Population of France (as displayed on Wikipedia): {population_text}")

        await browser.close()

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())