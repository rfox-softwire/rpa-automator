# playwright_population_france.py
#
# This script uses Playwright (sync API) to navigate Wikipedia,
# search for France and scrape the population figure from the
# infobox on the French page.

from playwright.sync_api import sync_playwright

def get_france_population():
    with sync_playwright() as p:
        # Launch a headless browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Go to Wikipedia main page
        page.goto("https://www.wikipedia.org/")

        # 2. Enter "France" in the search box and submit
        page.fill("#searchInput", "France")
        page.press("#searchInput", "Enter")

        # 3. Wait for navigation to the France article
        page.wait_for_load_state("domcontentloaded")

        # 4. In case we landed on a disambiguation or list page,
        #    click the first link that contains "France" in its text.
        if "France – Wikipedia" not in page.title():
            links = page.query_selector_all("a")
            for link in links:
                href = link.get_attribute("href") or ""
                if "/wiki/France" in href and "disambiguation" not in href:
                    link.click()
                    page.wait_for_load_state("domcontentloaded")
                    break

        # 5. Locate the population value in the infobox.
        #    Wikipedia uses a table with class "infobox".
        #    The population is usually inside a row whose first cell contains
        #    the text "Population" (or a variant like "Population (2022)").
        population = None
        rows = page.query_selector_all("table.infobox tr")
        for row in rows:
            header_cell = row.query_selector("th")
            data_cell = row.query_selector("td")
            if not header_cell or not data_cell:
                continue

            header_text = header_cell.inner_text().strip()
            # Look for common patterns that indicate the population figure
            if "Population" in header_text and ("2022" in header_text or "2019" in header_text):
                population = data_cell.inner_text().split("\n")[0].strip()
                break

        browser.close()

        return population


if __name__ == "__main__":
    pop = get_france_population()
    if pop:
        print(f"The population of France (as reported on Wikipedia) is: {pop}")
    else:
        print("Could not find the population figure.")