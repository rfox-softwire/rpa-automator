# pip install playwright
# playwright install

from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch browser (headless=True by default)
        browser = p.chromium.launch()
        page = browser.new_page()

        # 1. Go to Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search box and submit
        page.fill('input#searchInput', 'France')
        page.press('input#searchInput', 'Enter')

        # 3. Wait for the France article to load
        page.wait_for_selector('#firstHeading')

        # 4. Locate the population value in the infobox
        #    The population field is usually inside a table with class "infobox"
        #    and contains a <span> or <div> with itemprop="populationTotal".
        try:
            pop_element = page.query_selector(
                'table.infobox tr:has(td:contains("Population")) td'
            )
            if not pop_element:
                # fallback for different layout
                pop_element = page.query_selector(
                    'span[itemprop="populationTotal"]'
                )

            population_text = pop_element.inner_text().strip() if pop_element else "N/A"
        except Exception as e:
            population_text = f"Error: {e}"

        print(f"Population of France (as displayed on Wikipedia): {population_text}")

        browser.close()

if __name__ == "__main__":
    main()