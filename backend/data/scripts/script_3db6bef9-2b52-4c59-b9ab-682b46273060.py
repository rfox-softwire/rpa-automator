# Requires: pip install playwright
# To run this script:
#   1. Install Playwright browsers (once):
#        playwright install
#   2. Run the script:
#        python wikipedia_population.py

from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch a headless browser (change to True if you want to see it)
        browser = p.chromium.launch(headless=True)

        # Open a new page
        context = browser.new_context()
        page = context.new_page()

        # 1. Go to Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search box and press Enter
        #    The search input has id 'searchInput'
        page.fill("#searchInput", "France")
        page.press("#searchInput", "Enter")

        # 3. Wait for the France article to load
        page.wait_for_selector("h1#firstHeading")  # Title of the article

        # 4. Locate the infobox (table with class 'infobox')
        #    The population is usually inside a span with class 'bdi' or directly in a td
        #    We'll look for the row that contains "Population" text.
        population = None
        rows = page.query_selector_all("table.infobox tr")
        for row in rows:
            header = row.query_selector("th")
            if not header:
                continue
            if "Population" in header.inner_text():
                # The value is usually in the next td element
                value_td = row.query_selector("td")
                if value_td:
                    population = value_td.inner_text().strip()
                    break

        # 5. Print the result (cleaning up newlines and extra spaces)
        if population:
            print(f"Population of France (as per Wikipedia): {population}")
        else:
            print("Could not find population data.")

        # Clean up
        context.close()
        browser.close()

if __name__ == "__main__":
    main()