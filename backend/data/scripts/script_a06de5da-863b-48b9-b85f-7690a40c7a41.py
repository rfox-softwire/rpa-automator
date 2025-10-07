# Install Playwright first (if not already installed):
#   pip install playwright
#   playwright install

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def main() -> None:
    """Open Wikipedia, search for France, and print its population."""
    with sync_playwright() as p:
        # Launch a headless browser (set headless=False to see the UI)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1️⃣ Open Wikipedia
        page.goto("https://www.wikipedia.org/")

        # 2️⃣ Search for "France"
        search_input = page.locator("input[name='search']")
        search_input.fill("France")
        page.keyboard.press("Enter")

        # Wait until navigation is complete before looking for the infobox.
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            print("Navigation took too long – proceeding anyway.")

        # 3️⃣ Wait for the infobox to appear
        try:
            page.wait_for_selector("table.infobox.geography.vcard", state="visible", timeout=20000)
        except PlaywrightTimeoutError:
            print("Could not find the infobox – exiting.")
            context.close()
            browser.close()
            return

        # 4️⃣ Extract the population from the infobox
        # The population row may contain a <span class="bday"> element.
        # If that fails, try a more general selector that looks for the word “Population”
        population_text = None
        try:
            pop_span = page.locator(
                "table.infobox.geography.vcard td:has-text('Population') + td span.bday"
            )
            population_text = pop_span.inner_text()
        except Exception:
            # Fallback: find the cell that contains the word “Population” and get its value
            try:
                row = page.locator(
                    "table.infobox.geography.vcard tr:has(td:has-text('Population'))"
                )
                population_text = row.locator("td:nth-child(2)").inner_text()
            except Exception as e:
                print(f"Could not locate the population value: {e}")

        if population_text:
            print(f"Population of France (according to Wikipedia): {population_text}")
        else:
            print("Population data was not found.")

        # Clean up
        context.close()
        browser.close()


if __name__ == "__main__":
    main()