from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch a headless Chromium browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to the France Wikipedia page
        page.goto("https://en.wikipedia.org/wiki/France")

        # Locate the first population value in the infobox
        population_text = (
            page.locator('//th[contains(text(),"Population")]/following-sibling::td//span')
            .first.inner_text()
        )

        print(f"Population of France: {population_text}")

        browser.close()

if __name__ == "__main__":
    main()