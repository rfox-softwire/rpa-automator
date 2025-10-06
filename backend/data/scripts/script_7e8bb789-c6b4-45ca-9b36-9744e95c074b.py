# filename: wikipedia_population.py
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch a headless browser (use `headless=False` if you want to see the UI)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1️⃣ Open Wikipedia's homepage
        page.goto("https://www.wikipedia.org/")

        # 2️⃣ Find the search box, type "France" and press Enter
        page.fill("input#searchInput", "France")
        page.press("input#searchInput", "Enter")

        # 3️⃣ Wait for the France article to load (the first heading should be h1 with text "France")
        page.wait_for_selector("h1 span.mw-title-first", timeout=10000)

        # 4️⃣ Locate the infobox table that contains population data
        #    The population is usually in a <span> with class "bdi" inside a row where the first cell contains "Population"
        #    We'll search for a row that starts with "Population" and grab the second cell's text.
        try:
            pop_row = page.locator(
                "//table[contains(@class, 'infobox')]/tbody/tr[th[contains(., 'Population')]]"
            )
            population_text = pop_row.locator("td").inner_text()
            print(f"The population of France (as listed on Wikipedia) is: {population_text}")
        except Exception as e:
            print("Could not find the population data:", e)

        # Close browser
        browser.close()

if __name__ == "__main__":
    main()