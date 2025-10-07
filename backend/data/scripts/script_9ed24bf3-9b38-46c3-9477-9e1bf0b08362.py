# Install Playwright once:
#   pip install playwright
#   playwright install

from playwright.sync_api import sync_playwright

def get_france_population():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Open Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # 2. Search for "France"
        search_input = page.locator('input[name="search"]')
        search_input.fill("France")
        search_button = page.locator('button[type="submit"]')
        search_button.click()

        # 3. Wait until the France article loads
        page.wait_for_selector('#firstHeading')

        # 4. Locate the population value in the infobox
        #    The population is usually inside a table with class "infobox" and a row containing "Population"
        population_text = None
        for row in page.locator('table.infobox tr').all():
            header = row.locator('th')
            if header.inner_text().strip() == 'Population':
                # The value is often in the following <td>
                cell = row.locator('td')
                population_text = cell.inner_text().split('\n')[0].strip()
                break

        browser.close()

        return population_text


if __name__ == "__main__":
    pop = get_france_population()
    print(f"Population of France (as shown on Wikipedia): {pop}")