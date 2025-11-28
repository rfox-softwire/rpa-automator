from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        # Launch a headless Chromium browser
        browser = p.chromium.launch()
        page = browser.new_page()

        # 1️⃣ Open Wikipedia and navigate to the France article
        page.goto("https://en.wikipedia.org/wiki/France")

        # 2️⃣ Locate the table row that contains "Population" in its header
        population_cell = page.locator(
            'xpath=//th[contains(text(),"Population")]/following-sibling::td'
        )

        # 3️⃣ Retrieve the text content of that cell
        population_text = population_cell.text_content()

        # 4️⃣ Clean up and print the result
        if population_text:
            # Wikipedia often shows a number with commas and sometimes footnote markers.
            # Strip any bracketed references (e.g., [1]) and whitespace.
            cleaned = ''.join(ch for ch in population_text if ch.isdigit() or ch == ',').strip()
            print(f"Population of France: {cleaned}")
        else:
            print("Could not find the population information.")

        # Close browser
        browser.close()

if __name__ == "__main__":
    main()