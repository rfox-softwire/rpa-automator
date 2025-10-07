# install dependencies first:
# pip install playwright
# playwright install

from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # launch a headless browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Open Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # 2. Search for "France"
        page.fill("input[name='search']", "France")
        page.press("input[name='search']", "Enter")

        # 3. Click the first search result (should be France)
        page.click("a[title='France']")

        # 4. Wait until the infobox is visible
        page.wait_for_selector(".infobox.vcard")

        # 5. Extract population value from the infobox
        # The population row usually has a span with class "population" or text containing "Population"
        # We'll look for a row that contains the word "Population" and then get its value.
        rows = page.query_selector_all(".infobox.vcard tr")
        population_text = None
        for row in rows:
            header = row.query_selector("th")
            if header and "Population" in header.inner_text():
                data_cell = row.query_selector("td")
                if data_cell:
                    population_text = data_cell.inner_text()
                    break

        # 6. Print the result
        print(f"France population: {population_text}")

        browser.close()

if __name__ == "__main__":
    main()