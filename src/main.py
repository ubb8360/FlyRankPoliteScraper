from pathlib import Path

import requests


PAGE_URL = "https://books.toscrape.com/catalogue/page-1.html"

USER_AGENT = (
    "FlyRankInternship-A9/1.0 "
    "(+https://github.com/ubb8360/FlyRankPoliteScraper)"
)

TIMEOUT_SECONDS = 10

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = PROJECT_ROOT / "cache" / "catalogue-page-1.html"


def get_catalogue_page():
    # Use the saved HTML if we already fetched this page.
    if CACHE_PATH.exists():
        content = CACHE_PATH.read_bytes()

        print(f"CACHE HIT: {PAGE_URL}")
        print(f"response_size={len(content)} bytes")

        return content

    print(f"FETCH: {PAGE_URL}")

    try:
        response = requests.get(
            PAGE_URL,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed with HTTP status {response.status_code}"
        )

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_bytes(response.content)

    print(f"status={response.status_code}")
    print(f"response_size={len(response.content)} bytes")

    return response.content


if __name__ == "__main__":
    get_catalogue_page()