from playwright.sync_api import sync_playwright
                    import re

# --- Monitoring Code (Injected) ---
from playwright.sync_api import sync_playwright
from playwright_monitor import monitor_playwright


# --- Original Script ---
# playwright_population.py
#
# This script uses Playwright (sync API) to:
# 1. Open https://www.wikipedia.org/
# 2. Search for "France"
# 3. Navigate to the France article page
# 4. Extract the population figure from the infobox
# 5. Print the result



def main():
    with sync_playwright() as p:
        # Launch a headless browser (change headless=False if you want to see it)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Open Wikipedia
        page.goto("https://www.wikipedia.org/")

        # 2. Search for "France"
        # The search input has id 'searchInput'
        page.fill("#searchInput", "France")
        page.press("#searchInput", "Enter")

        # 3. Wait until the article page loads and the infobox is visible
        # Wikipedia uses a table with class 'infobox' for the data box
        page.wait_for_selector("table.infobox")

        # 4. Extract population from the infobox
        # The population row usually has a span with class "bday" or directly text like "Population"
        # We'll look for a row that contains the word "Population" and get the first number inside it.
        rows = page.query_selector_all("table.infobox tr")
        population_value = None

        for row in rows:
            header = row.query_selector("th")
            if header and "Population" in header.inner_text():
                # Find numeric value in this row
                data_cell = row.query_selector("td")
                if data_cell:
                    text = data_cell.inner_text()
                    # Extract the first number (may contain commas)

                    match = re.search(r"([\d,]+)", text.replace("\n", " "))
                    if match:
                        population_value = match.group(1).replace(",", "")
                        break

        if population_value:
            print(f"Population of France: {population_value}")
        else:
            print("Could not find the population value.")

        # Clean up
        context.close()
        browser.close()


if __name__ == "__main__":
    main()