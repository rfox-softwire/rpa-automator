from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Go to the France Wikipedia page
        page.goto("https://en.wikipedia.org/wiki/France")

        # Wait for the infobox to load
        page.wait_for_selector("table.infobox")

        # Extract the population value from the infobox
        # The row that contains "Population" has the value in its last <td>
        population_text = page.locator(
            "//table[contains(@class,'infobox')]//tr[td[contains(text(),'Population')]]/td[last()]"
        ).inner_text()

        print(f"Population of France: {population_text.strip()}")

        browser.close()

if __name__ == "__main__":
    main()