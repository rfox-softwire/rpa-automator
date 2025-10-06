# -*- coding: utf-8 -*-
"""
Playwright script that opens Wikipedia, searches for "France",
opens the France page and extracts the population figure from the infobox.
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    # Launch browser (headless by default)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Go to Wikipedia home page
        await page.goto("https://www.wikipedia.org/")

        # 2. Type "France" in the search box and press Enter
        await page.fill("input#searchInput", "France")
        await page.press("input#searchInput", "Enter")

        # 3. Wait for the France article to load
        await page.wait_for_selector("#mw-content-text")

        # 4. Locate the population value in the infobox.
        #    Wikipedia infoboxes are tables with class .infobox
        #    The population is usually inside a <span> or <td> with "Population"
        #    We'll use XPath to find the row containing "Population" and then grab the following sibling.
        population_xpath = (
            "//table[contains(@class,'infobox')]//tr["
            "normalize-space(td/text())='Population' "
            "or normalize-space(th/text())='Population']/td[2]"
        )
        # If not found, try a more relaxed approach (some pages use different labels)
        element_handle = await page.query_selector(population_xpath)

        if element_handle:
            population_text = await element_handle.inner_text()
            print(f"Population of France: {population_text.strip()}")
        else:
            print("Could not locate the population value in the infobox.")

        # Close browser
        await context.close()
        await browser.close()

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())