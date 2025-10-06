# playwright_population_france.py
#
# This script uses Playwright (Python) to open Wikipedia,
# search for “France”, and scrape the country’s population from the
# infobox on the France article page.
#
# Requirements:
#   pip install playwright
#   playwright install  # installs browsers

import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def extract_population(page):
    """
    Locate the population value in the French Wikipedia article.
    The infobox contains a row with header 'Population' (or 'Populatie', etc.).
    We search for table cells that contain a number and return it.
    """
    # Find the first table with class "infobox" (standard Wikipedia infobox)
    try:
        infobox = page.query_selector("table.infobox")
    except PlaywrightTimeoutError:
        raise RuntimeError("Infobox not found on the France page.")

    if not infobox:
        raise RuntimeError("Could not locate the infobox element.")

    # Search for rows that contain a header with text 'Population' (case-insensitive)
    rows = infobox.query_selector_all("tr")
    for row in rows:
        header = row.query_selector("th")
        if header and re.search(r"population", header.inner_text(), re.I):
            # The population value is usually in the adjacent <td>
            data_cell = row.query_selector("td")
            if data_cell:
                text = data_cell.inner_text()
                # Extract numeric part (e.g., "67,391,000")
                match = re.search(r"[\d{1,3}(?:,\d{3})+|\d+]", text.replace("\n", " "))
                if match:
                    return match.group(0).replace(",", "")
    raise RuntimeError("Population value not found in the infobox.")


def main():
    with sync_playwright() as p:
        # Launch a headless Chromium browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. Open Wikipedia home page
            page.goto("https://www.wikipedia.org/", timeout=30000)

            # 2. Type "France" into the search box and submit
            page.fill("[name='search']", "France")
            page.press("[name='search']", "Enter")

            # 3. Wait for navigation to the France article
            page.wait_for_load_state("domcontentloaded", timeout=30000)

            # 4. Extract population from the infobox
            population = extract_population(page)
            print(f"Population of France (as scraped): {population}")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()