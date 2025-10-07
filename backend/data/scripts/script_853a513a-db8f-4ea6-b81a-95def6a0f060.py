# rpa_script.py
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch a headless browser (Chrome/Chromium)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Open Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # 2. Type "France" in the search box and submit
        page.fill("input#searchInput", "France")
        page.press("input#searchInput", "Enter")

        # 3. Wait for the article page to load and locate the infobox population field
        #    The population is usually inside a table with class "infobox" in a row that contains
        #    the text "Population". We will use a robust selector.
        page.wait_for_selector("table.infobox")

        # 4. Extract the first occurrence of "Population" label and its corresponding value
        rows = page.query_selector_all("table.infobox tr")
        population_text = None

        for row in rows:
            header_cell = row.query_selector("th")
            if header_cell and "Population" in header_cell.inner_text():
                # The data cell is the next sibling <td>
                data_cell = row.query_selector("td")
                if data_cell:
                    population_text = data_cell.inner_text().strip()
                    break

        if population_text:
            print(f"The population of France (as shown on Wikipedia) is: {population_text}")
        else:
            print("Population information not found.")

        browser.close()

if __name__ == "__main__":
    main()