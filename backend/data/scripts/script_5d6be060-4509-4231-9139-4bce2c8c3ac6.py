#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: wikipedia_population_france.py

Description:
    Uses Playwright (Python) to navigate https://www.wikipedia.org/,
    search for "France", open the French page, and extract the population figure
    from the infobox. The result is printed to stdout.

Prerequisites:
    pip install playwright
    playwright install
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    # Launch a headless browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Go to Wikipedia homepage
        await page.goto("https://www.wikipedia.org/")

        # 2. Search for "France"
        await page.fill('input[name="search"]', 'France')
        await page.press('input[name="search"]', 'Enter')

        # 3. Wait until the article loads (use heading selector)
        await page.wait_for_selector('h1#firstHeading')

        # 4. Extract population from infobox
        # The infobox is a table with class "infobox". Population usually appears in
        # a row where the header contains "Population" or similar.
        infobox = await page.query_selector('.infobox')
        if not infobox:
            print("Infobox not found.")
            return

        # Find all rows in the infobox
        rows = await infobox.query_selector_all('tr')

        population_text = None
        for row in rows:
            header = await row.query_selector('th')
            data = await row.query_selector('td')
            if header and data:
                header_text = (await header.inner_text()).strip().lower()
                # Look for common population labels
                if 'population' in header_text or 'populatio' in header_text:
                    population_text = (await data.inner_text()).strip()
                    break

        if population_text:
            print(f"Population of France (as per Wikipedia infobox): {population_text}")
        else:
            print("Could not find population information in the infobox.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())