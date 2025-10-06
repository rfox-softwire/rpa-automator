# playwright_population_france.py
#
# This script uses Playwright (sync API) to navigate Wikipedia,
# search for the "France" page and extract its population from the
# infobox on the right side of the article.
#
# Install dependencies first:
#   pip install playwright
#   playwright install

from playwright.sync_api import sync_playwright
import re

def main():
    with sync_playwright() as p:
        # Launch a headless browser (change to False for debugging)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1️⃣ Open Wikipedia
            page.goto("https://www.wikipedia.org/")

            # 2️⃣ Type "France" in the search box and submit
            page.fill("input[name='search']", "France")
            page.press("input[name='search']", "Enter")

            # 3️⃣ Wait for the article to load
            page.wait_for_selector("#content", timeout=15000)

            # 4️⃣ Locate the population value in the infobox.
            #    Wikipedia uses a table with class 'infobox'.
            #    The population is usually inside a <tr> that contains
            #    a <th> or <td> with text "Population".
            #
            # We'll use XPath to find any cell containing the word "Population"
            # and then get the following sibling cell.
            population_xpath = (
                "//table[contains(@class, 'infobox')]//tr["
                "(contains(., 'Population') or contains(., 'População'))]"
            )
            row = page.query_selector(population_xpath)

            if not row:
                raise RuntimeError("Could not find the Population row in the infobox.")

            # The population number is usually in a <td> that follows the label
            pop_cell = row.locator("td").nth(1)  # second cell of the row
            raw_text = pop_cell.inner_text()

            # Clean up: keep only numbers and commas (e.g., "67,391,000")
            cleaned = re.sub(r"[^\d,]", "", raw_text)

            print(f"Population of France (as per Wikipedia infobox): {cleaned}")

        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()