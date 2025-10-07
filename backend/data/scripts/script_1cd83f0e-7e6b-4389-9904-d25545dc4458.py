# pip install playwright==1.48.0  # if not already installed
# playwright install

from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # Type "France" in the search box and submit
        page.fill("input[name='search']", "France")
        page.press("input[name='search']", "Enter")

        # Wait for the article page to load and locate the population field
        page.wait_for_selector("#mw-content-text .infobox tr:has(td:has-text('Population')) td", timeout=10000)

        # Extract the population value (first number in the cell)
        population_cell = page.query_selector("#mw-content-text .infobox tr:has(td:has-text('Population')) td")
        population_text = population_cell.inner_text().strip()

        print(f"France population: {population_text}")

        browser.close()

if __name__ == "__main__":
    main()