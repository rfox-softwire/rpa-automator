# Install Playwright before running:
#   pip install playwright
#   playwright install

from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch a headless browser (use 'headless=False' to see the UI)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Go to Wikipedia
        page.goto("https://www.wikipedia.org/")

        # 2. Search for "France"
        # The search input has id 'searchInput'
        page.fill("#searchInput", "France")
        page.press("#searchInput", "Enter")

        # 3. Wait until the France article loads
        page.wait_for_selector("h1#firstHeading")  # Article title

        # 4. Find the population value in the infobox
        # The infobox is a table with class 'infobox'
        # The population field usually has a span with class 'bdi' or directly text
        # We'll search for rows that contain the word "Population" (case-insensitive)
        population = None
        rows = page.query_selector_all("table.infobox tr")
        for row in rows:
            header = row.query_selector("th")
            if header and "population" in header.inner_text().lower():
                # Get the first cell after the header
                data_cell = row.query_selector("td")
                if data_cell:
                    population = data_cell.inner_text()
                    break

        if population:
            print(f"Population of France (according to Wikipedia): {population}")
        else:
            print("Could not find the population value in the infobox.")

        # Clean up
        context.close()
        browser.close()

if __name__ == "__main__":
    main()