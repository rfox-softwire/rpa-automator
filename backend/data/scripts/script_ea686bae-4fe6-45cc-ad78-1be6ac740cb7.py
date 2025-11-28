from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Open the Wikipedia page for France
        page.goto("https://en.wikipedia.org/wiki/France")

        # Locate the population value in the infobox
        population_locator = page.locator(
            "//table[contains(@class,'infobox')]"
            "//tr[td[contains(text(),'Population')]]/td[2]"
        )
        population_text = population_locator.inner_text()

        print(f"Population of France: {population_text}")

        browser.close()

if __name__ == "__main__":
    main()