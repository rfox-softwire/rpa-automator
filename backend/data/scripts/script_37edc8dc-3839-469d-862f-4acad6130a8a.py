import asyncio
from playwright.async_api import async_playwright

async def fetch_france_population():
    # Navigate to the France Wikipedia page
    url = "https://en.wikipedia.org/wiki/France"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        # Locate the population value in the infobox
        # The first 'Population' row typically contains the most recent figure
        population_locator = page.locator(
            '//table[contains(@class,"infobox")]/tbody/tr[th[contains(text(),"Population")]]/td'
        )
        population_text = await population_locator.text_content()

        print(f"France population: {population_text.strip()}")
        await browser.close()

asyncio.run(fetch_france_population())