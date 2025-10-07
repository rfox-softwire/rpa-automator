# rpa_wikipedia_population.py
#
# This script uses Playwright (sync API) to open Wikipedia,
# search for "France", navigate to the French article and extract
# the population figure from the infobox.
#
# Requirements:
#   pip install playwright
#   playwright install

from playwright.sync_api import sync_playwright
import re

def main():
    with sync_playwright() as p:
        # Launch a headless browser (set headless=False to see it)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. Go to Wikipedia homepage
            page.goto("https://www.wikipedia.org/", timeout=60000)

            # 2. Search for "France"
            search_input_selector = "#searchInput"          # input box id
            page.fill(search_input_selector, "France")
            page.press(search_input_selector, "Enter")

            # 3. Wait until the article page loads (check title contains "France - Wikipedia")
            page.wait_for_load_state("networkidle")
            if not page.title().startswith("France"):
                raise RuntimeError("Did not navigate to France article.")

            # 4. Locate the population value in the infobox
            #    The infobox is a table with class 'infobox'
            infobox_selector = "table.infobox"
            page.wait_for_selector(infobox_selector, timeout=10000)

            # Find the row that contains the word "Population" (case-insensitive)
            rows = page.query_selector_all(f"{infobox_selector} tr")
            population_value = None
            for row in rows:
                header = row.query_selector("th")
                if not header:
                    continue
                text = header.inner_text().strip()
                if re.search(r'population', text, re.I):
                    # The value is usually in the next <td> element
                    data_cell = row.query_selector("td")
                    if data_cell:
                        population_value = data_cell.inner_text().strip()
                        break

            if population_value:
                print(f"Population of France (as shown on Wikipedia): {population_value}")
            else:
                print("Could not find the population value in the infobox.")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()