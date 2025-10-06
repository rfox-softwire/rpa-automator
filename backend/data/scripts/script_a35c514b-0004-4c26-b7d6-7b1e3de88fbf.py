# playwright_population_france.py
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Launch a headless browser (set headless=False to see the UI)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1️⃣ Go to Wikipedia's homepage
        await page.goto("https://www.wikipedia.org/")

        # 2️⃣ Type "France" into the search box and submit
        await page.fill('input[name="search"]', 'France')
        await page.press('input[name="search"]', 'Enter')

        # 3️⃣ Wait for the France article to load
        await page.wait_for_selector('#firstHeading', state='visible')

        # 4️⃣ Locate the population value in the infobox.
        #    Wikipedia's infobox rows have a <th> with the label and a following <td>.
        #    The population row usually contains "Population" or "Population (2023)" etc.
        #    We'll look for a cell containing the word "population" (case‑insensitive)
        #    and then grab its sibling <td> text.

        # Find the header that contains "Population"
        header_selector = "//th[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'population')]"
        header_element = await page.query_selector(header_selector)

        if not header_element:
            print("Could not find a population row in the infobox.")
            await browser.close()
            return

        # Get the sibling <td> that contains the value
        td_element = await header_element.evaluate_handle('node => node.parentElement?.querySelector("td")')
        if not td_element:
            print("Could not locate the population data cell.")
            await browser.close()
            return

        population_text = await td_element.inner_text()

        # Clean up the text: remove references like [1] and any footnote markers
        cleaned_population = ''.join(ch for ch in population_text if ch.isdigit() or ch.isspace())
        cleaned_population = ' '.join(cleaned_population.split())

        print(f"Population of France (as shown on Wikipedia): {cleaned_population}")

        await browser.close()

asyncio.run(main())