# playwright-wikipedia-population.py
#
# This script uses the Playwright Python library to:
# 1. Open https://www.wikipedia.org/
# 2. Search for "France"
# 3. Click on the first search result (the France article)
# 4. Extract the population figure from the infobox
#
# Requirements:
#   pip install playwright
#   playwright install

import asyncio
from playwright.async_api import async_playwright


async def get_france_population():
    async with async_playwright() as p:
        # Launch a headless browser (set headless=False to see it)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Go to Wikipedia
        await page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search box and press Enter
        await page.fill("input#searchInput", "France")
        await page.keyboard.press("Enter")

        # 3. Wait for navigation to the France article
        await page.wait_for_selector("h1#firstHeading")  # ensures page loaded

        # 4. Locate the population value in the infobox.
        #    Wikipedia uses a table with class "infobox" and rows like:
        #    <tr><th scope="row">Population</th> ... </tr>
        #
        #    We'll look for a row where the header contains "Population"
        #    and then grab the text from the corresponding data cell.

        # XPath to find the table row with header containing "Population"
        population_row_xpath = (
            "//table[contains(@class, 'infobox')]//tr[th[contains(translate(text(), "
            "'POPULATION', 'population', 'Population'), 'Population')]]"
        )
        # Wait for that row to appear
        await page.wait_for_selector(population_row_xpath)

        # Extract the population cell text
        population_text = await page.inner_text(f"{population_row_xpath}/td")

        print("France population (as per Wikipedia infobox):")
        print(population_text.strip())

        await browser.close()


if __name__ == "__main__":
    asyncio.run(get_france_population())