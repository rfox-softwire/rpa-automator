# Requires Playwright:
#   pip install playwright
#   playwright install

from playwright.sync_api import sync_playwright
import re

def get_france_population():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Open the France Wikipedia page
        page.goto("https://en.wikipedia.org/wiki/France")

        # Wait for the infobox to load
        page.wait_for_selector(".infobox.vcard")

        # Find the row that starts with "Population" in the infobox
        rows = page.locator(".infobox.vcard tr")
        population_value = None

        for i in range(rows.count()):
            header = rows.nth(i).locator("th").inner_text()
            if header.strip().lower() == "population":
                # The corresponding data cell is the next <td>
                data_cell = rows.nth(i).locator("td")
                text = data_cell.inner_text()
                # Extract the first number (may include commas)
                match = re.search(r"[\d,]+", text.replace("\n", " "))
                if match:
                    population_value = match.group(0).replace(",", "")
                break

        browser.close()

        return int(population_value) if population_value else None


if __name__ == "__main__":
    pop = get_france_population()
    if pop:
        print(f"Population of France (as per Wikipedia infobox): {pop:,}")
    else:
        print("Could not find the population value.")