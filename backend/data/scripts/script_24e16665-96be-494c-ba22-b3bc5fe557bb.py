import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Launch a headless browser (use 'chromium', 'firefox' or 'webkit')
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 1️⃣ Go to Wikipedia's homepage
        await page.goto("https://www.wikipedia.org/")

        # 2️⃣ Search for "France"
        # Locate the search input, type the query and press Enter
        await page.fill('input#searchInput', 'France')
        await page.press('input#searchInput', 'Enter')

        # 3️⃣ Wait until the article page loads (check for heading)
        await page.wait_for_selector('#firstHeading >> text=France')

        # 4️⃣ Locate the population field in the infobox
        # The population is usually inside a table with class "infobox"
        # We'll look for a row that contains the word "Population" and then grab its value.
        try:
            # Find the infobox first
            infobox = await page.query_selector('.infobox')
            if not infobox:
                raise Exception("Infobox not found on the France article.")

            # Search for rows that contain "Population"
            rows = await infobox.query_selector_all('tr')
            population_value = None
            for row in rows:
                header = await row.query_selector('th')
                data_cell = await row.query_selector('td')
                if header and data_cell:
                    header_text = (await header.inner_text()).strip().lower()
                    if 'population' in header_text:
                        # Clean up the population text
                        raw_value = (await data_cell.inner_text()).strip()
                        # Remove references [1], [2] etc.
                        cleaned = ''.join(ch for ch in raw_value if not ch.isdigit() and ch != ',' and ch != '.' and ch != ' ')
                        population_value = raw_value.split('[')[0].strip()
                        break

            if population_value:
                print(f"Population of France (as per Wikipedia infobox): {population_value}")
            else:
                print("Could not find the population value in the infobox.")
        except Exception as e:
            print(f"Error while extracting population: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())