# install dependencies first:
# pip install playwright
# playwright install

from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        # Launch browser (headless by default)
        browser = p.chromium.launch(headless=True)

        # Create a new page
        context = browser.new_context()
        page = context.new_page()

        # 1. Go to Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # 2. Type "France" into the search box and press Enter
        page.fill("input#searchInput", "France")
        page.press("input#searchInput", "Enter")

        # 3. Wait for the article page to load
        page.wait_for_selector('h1', timeout=10000)

        # 4. Find the population value in the infobox
        #    Wikipedia uses a table with class "infobox" and rows like:
        #    <th scope="row">Population</th> ... <td>~66,991,000 (2023)</td>
        population = None
        rows = page.query_selector_all("table.infobox tr")
        for row in rows:
            header = row.query_selector("th")
            if header and "Population" in header.inner_text():
                cell = row.query_selector("td")
                if cell:
                    # Grab the first number found (may include commas)
                    text = cell.inner_text()
                    population = text.split("(")[0].strip()  # e.g., "66,991,000"
                    break

        if population:
            print(f"Population of France: {population}")
        else:
            print("Could not find the population on the page.")

        # Clean up
        browser.close()


if __name__ == "__main__":
    main()