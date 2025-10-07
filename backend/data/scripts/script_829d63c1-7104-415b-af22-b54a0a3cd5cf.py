# pip install playwright
# python -m playwright install

from playwright.sync_api import sync_playwright

def get_france_population():
    with sync_playwright() as p:
        # Launch a headless browser (change headless=False to see the UI)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Open Wikipedia
        page.goto("https://www.wikipedia.org/")

        # 2. Search for "France"
        search_input_selector = "#searchInput"
        page.fill(search_input_selector, "France")
        page.press(search_input_selector, "Enter")

        # 3. Wait until the article loads and get the population value
        #    The population is usually inside the infobox with a span that has class "value"
        #    We locate the row where the header contains "Population" (or "População")
        page.wait_for_selector("table.infobox")

        # Find the table rows in the infobox
        rows = page.query_selector_all("table.infobox tr")
        population_text = None

        for row in rows:
            header = row.query_selector("th")
            if header and "Population" in header.inner_text():
                # The value is typically inside a <td> after the header
                value_cell = row.query_selector("td")
                if value_cell:
                    population_text = value_cell.inner_text().strip()
                    break

        browser.close()

        return population_text


if __name__ == "__main__":
    pop = get_france_population()
    print(f"Population of France (as shown on Wikipedia): {pop}")