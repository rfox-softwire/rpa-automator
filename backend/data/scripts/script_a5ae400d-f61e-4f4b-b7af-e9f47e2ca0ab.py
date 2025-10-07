#!/usr/bin/env python3
# Requires Playwright: pip install playwright && playwright install

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Launch a headless Chromium browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. Open Wikipedia homepage
        await page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search input and press Enter
        await page.fill("input#searchInput", "France")
        await page.keyboard.press("Enter")

        # 3. Wait for the France article to load
        await page.wait_for_selector("h1#firstHeading")

        # 4. Locate the population value in the infobox.
        #    The population is usually inside a table row that contains
        #    a cell with text "Population" (or its local translation).
        #
        #    We'll use XPath to find the first <td> that follows a <th>
        #    containing "Population" and extract its text content.
        #
        #    This may return multiple numbers; we pick the one that
        #    contains digits and no commas in the middle (the most recent figure).
        population_xpath = (
            "//table[contains(@class,'infobox')]"
            "//tr[th[contains(.,'Population')]]/td[1]"
        )
        element = await page.query_selector(population_xpath)

        if element:
            text = await element.text_content()
            # Clean up the extracted text
            population_text = text.strip().split('\n')[0]  # take first line
            print(f"Population of France (from Wikipedia infobox): {population_text}")
        else:
            print("Could not find the population value on the page.")

        await browser.close()

asyncio.run(main())