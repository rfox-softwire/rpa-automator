# pip install playwright
# playwright install

from playwright.sync_api import sync_playwright

def get_france_population():
    with sync_playwright() as p:
        # launch a headless browser (change to True if you want to see the UI)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1️⃣ Open Wikipedia main page
        page.goto("https://www.wikipedia.org/")

        # 2️⃣ Search for “France”
        # The search input has id "searchInput"
        page.fill("#searchInput", "France")
        page.press("#searchInput", "Enter")

        # 3️⃣ Wait until the France article loads
        page.wait_for_selector("h1#firstHeading")  # title of the article

        # 4️⃣ Find the infobox that contains population data
        # Wikipedia uses a table with class "infobox" inside it
        infobox = page.query_selector(".infobox")

        if not infobox:
            raise RuntimeError("Could not find the infobox on the France page.")

        # 5️⃣ Look for the row where the first cell contains "Population"
        rows = infobox.query_selector_all("tr")
        population_text = None
        for row in rows:
            header_cell = row.query_selector("th")
            if header_cell and "Population" in header_cell.inner_text():
                data_cell = row.query_selector("td")
                if data_cell:
                    population_text = data_cell.inner_text().strip()
                    break

        browser.close()

        if not population_text:
            raise RuntimeError("Could not locate the population value in the infobox.")

        # Clean up the text (remove references like [1], [2], etc.)
        import re
        cleaned_population = re.sub(r"\[.*?\]", "", population_text).strip()
        return cleaned_population

if __name__ == "__main__":
    pop = get_france_population()
    print(f"Population of France (as reported by Wikipedia): {pop}")