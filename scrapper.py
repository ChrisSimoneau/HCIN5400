import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd
import requests

# Base configuration
BASE_URL = "https://www.planespotters.net"
COUNTRIES_URL = f"{BASE_URL}/airlines/country"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

## Fetch
def get_soup(url):
    """Helper function to fetch a URL and return a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def scrape_planespotters():
    print(f"Fetching country list from {COUNTRIES_URL}...")
    main_soup = get_soup(COUNTRIES_URL)

    if not main_soup:
        print("Failed to load the main page. Exiting.")
        return

    country_links = {}

    # Extract all the countries
    for link in main_soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("/airlines/") and href not in [
            "/airlines",
            "/airlines/country",
        ]:
            parts = href.strip("/").split("/")
            if len(parts) == 2:
                country_name = link.get_text(strip=True)
                full_url = urljoin(BASE_URL, href)
                if (
                    country_name
                    and full_url not in country_links.values()
                    and country_name.lower() != "country"
                ):
                    country_links[country_name] = full_url

    print(
        f"Found {len(country_links)} countries. :)"
    )

    country_data = []
    seen_combinations = set()

    # Iterate through all countries
    for country, url in country_links.items():
        print(f"Scraping: {country}...")
        country_soup = get_soup(url)

        if country_soup:
            # get each airliner in each country
            airline_links = country_soup.find_all("a", href=True)

            for a in airline_links:
                href = a["href"]
                if "/airline/" in href:
                    airline_name = a.get_text(strip=True)

                    # Filter out navigation elements/empty names...
                    if (
                        airline_name
                        and len(airline_name) > 1
                        and country.lower() not in airline_name.lower()
                    ):
                        identifier = (country, airline_name)
                        if identifier not in seen_combinations:
                            seen_combinations.add(identifier)
                            country_data.append(
                                {
                                    "Country": country,
                                    "Airline": airline_name,
                                    "Airline_URL": urljoin(BASE_URL, href),
                                    "Source_URL": url,
                                }
                            )

        # We are being nice to not DOS the website here just in case :)
        time.sleep(1)

    # Save data...idk if R likes Csv or josn better or if it even matters but I can get both and then see later
    if country_data:
        df = pd.DataFrame(country_data)
        df.to_csv("airlines_by_country.csv", index=False)
        df.to_json(
            "airlines_by_country.json", orient="records", indent=4
        )
        print(
            f"\nSuccess! {len(df)}"
        )
        print("Saved JSON AND CSV.")
    else:
        print(
            "I dont want to see this message"
        )


if __name__ == "__main__":
    scrape_planespotters()