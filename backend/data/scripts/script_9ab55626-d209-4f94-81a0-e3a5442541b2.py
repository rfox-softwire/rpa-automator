from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1️⃣ Open Wikipedia
        page.goto("https://www.wikipedia.org/")

        # 2️⃣ Search for "France"
        page.fill("input#searchInput", "France")
        page.click("button[type='submit']")

        # 3️⃣ Wait for the article to load
        page.wait_for_selector("#firstHeading")

        # 4️⃣ Extract the population from the infobox
        # The value is in a <td> that follows a <th> containing the text "Population"
        population_text = page.eval_on_selector(
            "//th[normalize-space()='Population']/following-sibling::td[1]",
            "el => el.textContent.trim()",
        )

        print(f"Population of France: {population_text}")

        browser.close()

if __name__ == "__main__":
    main()