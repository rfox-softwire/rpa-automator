#!/usr/bin/env python3
"""
Playwright script to fetch the population of France from Wikipedia.

Requirements:
    pip install playwright
    playwright install

Run:
    python3 get_france_population.py
"""

import asyncio
from traceback import format_exc
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


async def main() -> None:
    """Main entry point."""
    try:
        # ---- Launch browser -------------------------------------------------
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            # ---- 1️⃣ Go to Wikipedia -----------------------------------------
            await page.goto("https://www.wikipedia.org/", timeout=60000)

            # ---- 2️⃣ Search for "France" ------------------------------------
            await page.fill("#searchInput", "France")
            await page.press("#searchInput", "Enter")

            # Wait until the article title is visible
            await page.wait_for_selector("h1#firstHeading", state="visible", timeout=60000)

            # ---- 3️⃣ Locate the population in the infobox -------------------
            # Wikipedia tables can be a bit nested; we look for any <th>
            # that contains the word “Population” and grab its adjacent <td>.
            rows = await page.query_selector_all("table.infobox tr")
            population_value: str | None = None

            for row in rows:
                header = await row.query_selector("th")
                if not header:
                    continue

                header_text = (await header.inner_text()).strip()
                # Some rows contain “Population” followed by a year or notes
                if "Population" in header_text:
                    data_cell = await row.query_selector("td")
                    if data_cell:
                        population_value = (await data_cell.inner_text()).strip()
                        break

            # ---- 4️⃣ Output ----------------------------------------------------
            if population_value:
                print(f"Population of France: {population_value}")
            else:
                print("Could not find the population value.")

            # ---- Clean up -----------------------------------------------------
            await context.close()
            await browser.close()

    except PlaywrightTimeout as exc:
        print(f"[ERROR] Timeout while waiting for a selector: {exc}")
    except Exception:
        # Print full traceback – useful when debugging why the script failed
        print("[ERROR] Unexpected exception occurred:")
        print(format_exc())


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())