import playwright
from playwright.synctime import sync_timeout
import requests

def get_france_population():
    """
    Fetches the population of France from the official French government website.

    Returns:
        float: The population of France as a float, or None if an error occurs.
    """
    url = "https://www.insotat.fr/en/population"  # Official site for French population data
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return float(response.text)  # Convert to float
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        return None

if __name__ == "__main__":
    population = get_france_population()
    if population is not None:
        print(f"The population of France is: {population}")
    else:
        print("Could not retrieve the population data.")
