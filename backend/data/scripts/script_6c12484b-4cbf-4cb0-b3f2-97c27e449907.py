import asyncio
from playwright.async_api import async_playwright


async def get_france_population() -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Go to Wikipedia homepage
        await page.goto("https://www.wikipedia.org/")

        # Type "France" into the search box and submit
        await page.fill("input#searchInput", "France")
        await page.press("input#searchInput", "Enter")

        # Wait for the article page to load (first heading appears)
        await page.wait_for_selector("h1#firstHeading")

        # Extract the population value from the infobox
        population_locator = page.locator(
            'table.infobox.vcard tr:has(td:text("Population")) td:last-child'
        )
        population_text = await population_locator.text_content()

        await browser.close()
        return population_text.strip() if population_text else "N/A"


async def main():
    population = await get_france_population()
    print(f"France population (from Wikipedia): {population}")


if __name__ == "__main__":
    asyncio.run(main())