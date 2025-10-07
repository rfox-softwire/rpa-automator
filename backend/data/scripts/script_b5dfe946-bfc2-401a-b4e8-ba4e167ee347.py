# Requires Playwright 1.30+ and Python 3.8+
# Install: pip install playwright
# Run the script: python wikipedia_population.py

from playwright.sync_api import sync_playwright
import re

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # 1. Open Wikipedia homepage
        page.goto("https://www.wikipedia.org/")

        # 2. Search for "France"
        search_input = page.locator('input[name="search"]')
        search_input.fill("France")
        page.keyboard.press("Enter")

        # 3. Wait until the article loads and get the first paragraph
        page.wait_for_selector('#mw-content-text .mw-parser-output > p')

        first_para = page.locator('#mw-content-text .mw-parser-output > p').inner_text()

        # 4. Extract population from the paragraph (look for pattern "population of ...")
        match = re.search(r'population\s+of\s+France\s*is\s*([\d,\.]+)', first_para, re.I)
        if not match:
            # Try another common phrase
            match = re.search(r'France\s+has\s+a\s+population\s+of\s*([\d,\.]+)', first_para, re.I)

        population = match.group(1) if match else "Not found"

        print(f"Population of France (from Wikipedia): {population}")

        browser.close()

if __name__ == "__main__":
    main()