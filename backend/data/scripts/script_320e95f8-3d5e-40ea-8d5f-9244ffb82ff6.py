from playwright.sync_api import sync_playwright

def get_france_population():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1️⃣ Open Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # 2️⃣ Search for "France"
        page.fill('input#searchInput', 'France')
        page.press('input#searchInput', 'Enter')

        # 3️⃣ Wait until the article page loads
        page.wait_for_selector('#mw-content-text')

        # 4️⃣ Locate the infobox table that contains the population data
        #    The value is usually inside a <span class="noprint inline-iso"> or similar.
        #    We'll look for the first "Population" row in the infobox.
        population_element = page.locator(
            "//table[contains(@class, 'infobox')]//tr[td[contains(text(), 'Population')]]/td"
        )
        population_text = population_element.inner_text()

        # 5️⃣ Extract just the numeric part (remove commas, brackets, etc.)
        import re
        match = re.search(r'[\d,]+', population_text)
        population_number = match.group(0) if match else "Not found"

        print(f"Population of France: {population_number}")

        browser.close()

if __name__ == "__main__":
    get_france_population()