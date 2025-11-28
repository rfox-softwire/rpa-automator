from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch a headless browser
        browser = p.chromium.launch()
        page = browser.new_page()

        # Go to the French Wikipedia article
        page.goto("https://en.wikipedia.org/wiki/France")

        # Locate the population value in the infobox
        # The population is usually inside a table row that contains the text "Population"
        # We extract the text from the following sibling <td> element.
        population_locator = page.locator(
            "//th[contains(text(), 'Population')]/following-sibling::td[1]"
        )
        population_text = population_locator.inner_text().strip()

        print(f"Population of France: {population_text}")

        # Close browser
        browser.close()

if __name__ == "__main__":
    main()