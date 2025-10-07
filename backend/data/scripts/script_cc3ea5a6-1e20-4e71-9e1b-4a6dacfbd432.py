# Install Playwright once:   pip install playwright && playwright install

from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        # Launch a headless browser (default is headless=True)
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

        # Locate the table row that contains the label 'Population'
        population_text = None

        # Use XPath to find a <th> element containing the word 'Population'
        th_locator = page.locator("//table[contains(@class,'infobox')]/tr/th[normalize-space() and contains(., 'Population')]")
        if th_locator.count():
            # Get the corresponding <td> sibling
            td_locator = th_locator.first.sibling("td")
            if td_locator:
                population_text = td_locator.inner_text().strip()

        # If not found, try a more generic search for any cell containing 'Population'
        if not population_text:
            td_generic = page.locator("//table[contains(@class,'infobox')]//td[normalize-space() and contains(., 'Population')]")
            if td_generic.count():
                population_text = td_generic.first.inner_text().strip()

        # Output the result
        print(f"Population of France (as shown on Wikipedia): {population_text}")

        # Clean up
        browser.close()


if __name__ == "__main__":
    main()