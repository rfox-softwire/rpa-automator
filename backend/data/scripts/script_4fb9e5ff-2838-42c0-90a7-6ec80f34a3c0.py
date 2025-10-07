# playwright_population.py
# Requires: pip install playwright
# Run once to install browsers:  playwright install

import re
from pathlib import Path

from playwright.sync_api import sync_playwright


def extract_population(text: str) -> str:
    """
    Extract the population figure from a Wikipedia infobox paragraph.
    The pattern usually looks like "Population (2023): 67,425,000".
    """
    # Find a line containing the word 'population' and a number
    match = re.search(r"Population(?:\s*\([^\)]+\))?:?\s*([\d,\.]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).replace(",", "")
    return "Not found"


def main():
    with sync_playwright() as p:
        # Launch a headless browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Go to Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search box and submit
        page.fill("input#searchInput", "France")
        page.click("button[type='submit']")

        # 3. Wait for navigation to France article
        page.wait_for_load_state("domcontentloaded")

        # 4. Grab the content of the infobox (class="infobox")
        infobox = page.query_selector(".infobox")
        if not infobox:
            print("Could not find the infobox.")
            return

        infobox_text = infobox.inner_text()

        # 5. Extract population
        population = extract_population(infobox_text)

        print(f"Population of France (latest available): {population}")

        # Close browser
        context.close()
        browser.close()


if __name__ == "__main__":
    main()