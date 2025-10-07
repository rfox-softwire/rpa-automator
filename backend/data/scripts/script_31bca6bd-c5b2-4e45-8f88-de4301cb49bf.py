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

        # Wait for the article page to load
        await page.wait_for_selector("span#mw-hidden-xs")

        # Extract the population value from the infobox
        population_text = await page.inner_text(
            'table.infobox.vcard tr:has(td:has-text("Population")) td:last-child'
        )

        await browser.close()
        return population_text.strip()


async def main():
    population = await get_france_population()
    print(f"France population (from Wikipedia): {population}")


if __name__ == "__main__":
    asyncio.run(main())