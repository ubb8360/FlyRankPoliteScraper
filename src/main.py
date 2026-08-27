from pathlib import Path
from time import sleep
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


START_URL = "https://books.toscrape.com/catalogue/page-1.html"

USER_AGENT = (
    "FlyRankInternship-A9/1.0 "
    "(+https://github.com/ubb8360/FlyRankPoliteScraper)"
)

TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 0.5

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"


def cache_path_for_url(url):
    parsed_url = urlparse(url)

    filename = Path(parsed_url.path).name

    return CACHE_DIR / filename


def get_page(url):
    cache_path = cache_path_for_url(url)

    if cache_path.exists():
        content = cache_path.read_bytes()

        print(f"CACHE HIT: {url}")
        print(f"response_size={len(content)} bytes")

        return content

    print(f"FETCH: {url}")

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed with HTTP status {response.status_code}: {url}"
        )

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(response.content)

    print(f"status={response.status_code}")
    print(f"response_size={len(response.content)} bytes")

    # Only delay after a real request.
    sleep(REQUEST_DELAY_SECONDS)

    return response.content


def discover_books():
    current_url = START_URL

    catalogue_pages = 0
    discovered_urls = []

    while current_url and catalogue_pages < 3:
        html = get_page(current_url)
        soup = BeautifulSoup(html, "html.parser")

        catalogue_pages += 1

        # Each book inside an article with class "product_pod".
        books = soup.select("article.product_pod h3 a")

        for book in books:
            href = book.get("href")

            if href:
                product_url = urljoin(current_url, href)
                discovered_urls.append(product_url)

        # Follow the catalogue's own Next link.
        next_link = soup.select_one("li.next a")

        if next_link and catalogue_pages < 3:
            current_url = urljoin(current_url, next_link.get("href"))
        else:
            current_url = None

    unique_urls = list(dict.fromkeys(discovered_urls))

    print()
    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={len(discovered_urls)}")
    print(f"unique_urls={len(unique_urls)}")

    return unique_urls


if __name__ == "__main__":
    discover_books()