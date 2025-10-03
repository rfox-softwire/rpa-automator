
import playwright
from playwright.sync_api import sync_playwright

def get_uk_population():
    """
    Fetches the population data for the UK from a specified URL.

    Returns:
        str: The population data as a string, or None if an error occurs.
    """
    try:
        client = playwright.Browser(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36") #Adapt user agent as needed
        url = "https://www.ons.gov.uk/population" # Replace with the actual URL if it changes

        page = client.new_page()
        page.goto(url)

        # Wait for the page to load completely (important!)
        page.wait_for_load_state("domcontentloaded")  # Adjust timeout as needed

        # Extract the population data. This part is highly dependent on the website's HTML structure!
        try:
            population_data = page.locator("#population-data").text
            return population_data
        except Exception as e:
            print(f"Error extracting data: {e}")  # Log for debugging
            return None

    except Exception as e:
        print(f"An error occurred: {e}") #Log for debugging.
        return None


if __name__ == "__main__":
    uk_population = get_uk_population()
    if uk_population:
        print("The population of the UK is:")
        print(uk_population)
    else:
        print("Could not retrieve population data.")
