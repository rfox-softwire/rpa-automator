from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch Chromium in head‑less mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1️⃣ Open Wikipedia's homepage
        page.goto("https://www.wikipedia.org/")

        # 2️⃣ Search for "France"
        page.fill("input#searchInput", "France")
        page.click("button[type='submit']")

        # 3️⃣ Wait for the article to load completely
        page.wait_for_selector("#firstHeading")

        # 4️⃣ Wait until the population cell is present in the infobox
        population_cell_selector = "//th[normalize-space()='Population']/following-sibling::td[1]"
        page.wait_for_selector(population_cell_selector)

        # 5️⃣ Extract and clean the population text
        population_text = page.eval_on_selector(
            population_cell_selector,
            "el => el.textContent.trim()"
        )

        print(f"Population of France: {population_text}")

        browser.close()

if __name__ == "__main__":
    main()