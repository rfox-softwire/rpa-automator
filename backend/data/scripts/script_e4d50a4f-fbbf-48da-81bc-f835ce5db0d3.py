from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1️⃣ Go to Wikipedia home page
        page.goto("https://www.wikipedia.org/")

        # 2️⃣ Click the English language link
        page.click("#js-link-box-en")

        # 3️⃣ Search for "France"
        page.fill("#searchInput", "France")
        page.press("#searchInput", "Enter")

        # 4️⃣ Wait for the article to load
        page.wait_for_selector("h1#firstHeading")

        # 5️⃣ Extract the population value from the infobox
        #    The population row typically contains the text "Population" in a <td>
        population_element = page.query_selector(
            'table.infobox tr:has(td:has-text("Population")) td:nth-child(2)'
        )
        if population_element:
            population_text = population_element.inner_text().strip()
            print(f"The population of France is: {population_text}")
        else:
            print("Could not find the population information.")

        browser.close()

if __name__ == "__main__":
    main()