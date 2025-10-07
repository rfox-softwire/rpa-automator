# Install Playwright once:   pip install playwright && playwright install

from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch a headless browser
        browser = p.chromium.launch()
        context = browser.new_context()

        # Open Wikipedia's homepage
        page = context.new_page()
        page.goto("https://www.wikipedia.org/")

        # Find the search input, type "France" and press Enter
        page.fill("input[name='search']", "France")
        page.press("input[name='search']", "Enter")

        # Wait for navigation to the France article
        page.wait_for_selector("#firstHeading")

        # The population is usually in the infobox under a row with span having class "infobox-data"
        # Locate the table row that contains the label 'Population'
        rows = page.query_selector_all("table.infobox.vcard tr")
        population_text = None
        for row in rows:
            header = row.query_selector("th")
            if header and "Population" in header.inner_text():
                data_cell = row.query_selector("td")
                if data_cell:
                    population_text = data_cell.inner_text().strip()
                    break

        # If the first match didn't work, try a more generic search for "Population"
        if not population_text:
            # Search for any element containing the word 'Population' in the infobox
            span = page.query_selector("table.infobox.vcard td:has-text('Population')")
            if span:
                population_text = span.inner_text().strip()

        print(f"Population of France (as shown on Wikipedia): {population_text}")

        # Clean up
        browser.close()

if __name__ == "__main__":
    main()