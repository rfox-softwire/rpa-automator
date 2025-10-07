# Install Playwright first (if not already installed):
#   pip install playwright
#   playwright install

from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch a headless browser (set headless=False to see the browser)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 1️⃣ Open Wikipedia
        page.goto("https://www.wikipedia.org/")

        # 2️⃣ Search for "France"
        search_input = page.locator("input[name='search']")
        search_input.fill("France")
        page.keyboard.press("Enter")

        # Wait until the page loads and the infobox is visible
        page.wait_for_selector("table.infobox.geography.vcard", timeout=10000)

        # 3️⃣ Extract the population from the infobox
        # The population usually appears in a row that contains the text "Population"
        # We'll look for a <span> with class "bday" which holds the numeric value.
        try:
            pop_span = page.locator("table.infobox.geography.vcard td:has-text('Population') + td span.bday")
            population_text = pop_span.inner_text()
            print(f"Population of France (according to Wikipedia): {population_text}")
        except Exception as e:
            print("Could not find the population value:", e)

        # Clean up
        context.close()
        browser.close()

if __name__ == "__main__":
    main()