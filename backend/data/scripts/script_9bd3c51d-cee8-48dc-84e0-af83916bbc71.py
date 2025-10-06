# playwright_population_france.py
import asyncio
from playwright.async_api import async_playwright

async def main():
    # Launch browser and create a new page
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1. Go to Wikipedia homepage
        await page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search box and submit
        await page.fill("input#searchInput", "France")
        await page.press("input#searchInput", "Enter")

        # 3. Wait for the France article to load
        await page.wait_for_selector("h1")  # ensures the heading is loaded

        # 4. Locate the infobox table and find the population row
        # The infobox has class "infobox geography vcard"
        infobox = await page.query_selector(".infobox.geography.vcard")
        if not infobox:
            print("Infobox not found.")
            await browser.close()
            return

        # Search for a cell that contains the word "Population" (case-insensitive)
        rows = await infobox.query_selector_all("tr")
        population_value = None
        for row in rows:
            header = await row.query_selector("th")
            if header:
                text = (await header.inner_text()).strip().lower()
                if "population" in text and not ("estimate" in text or "resident" in text):
                    # Found the correct row; get the corresponding data cell
                    cell = await row.query_selector("td")
                    if cell:
                        population_value = await cell.inner_text()
                        break

        if population_value:
            print(f"Population of France: {population_value}")
        else:
            print("Could not find population information.")

        # Close browser
        await browser.close()

# Run the script
if __name__ == "__main__":
    asyncio.run(main())