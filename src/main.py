from datetime import datetime, timezone
import json
from pathlib import Path
from time import sleep
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, field_validator


START_URL = "https://books.toscrape.com/catalogue/page-1.html"

USER_AGENT = (
    "FlyRankInternship-A9/1.0 "
    "(+https://github.com/ubb8360/FlyRankPoliteScraper)"
)

TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 0.5

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_ROOT / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"

BOOKS_PATH = OUTPUT_DIR / "books.json"
ERRORS_PATH = OUTPUT_DIR / "errors.json"


class BookRecord(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: Optional[str]
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def require_https(cls, value):
        if not value.startswith("https://"):
            raise ValueError("URL must start with https://")

        return value


def cache_path_for_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path.strip("/")

    if path.startswith("catalogue/page-") and path.endswith(".html"):
        filename = Path(path).name
    else:
        # Unique filename for each cache
        filename = path.replace("/", "__")

    return CACHE_DIR / filename


def timestamp_for_cache(cache_path):
    modified_time = cache_path.stat().st_mtime

    return (
        datetime.fromtimestamp(modified_time, timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def get_page(url):
    cache_path = cache_path_for_url(url)

    if cache_path.exists():
        content = cache_path.read_bytes()
        fetched_at = timestamp_for_cache(cache_path)

        print(f"CACHE HIT: {url}")

        return content, fetched_at

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

    fetched_at = (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )

    cache_path.write_bytes(response.content)

    print(f"status={response.status_code}")
    print(f"response_size={len(response.content)} bytes")

    # Delay only after a real network request.
    sleep(REQUEST_DELAY_SECONDS)

    return response.content, fetched_at


def discover_books():
    current_url = START_URL

    catalogue_pages = 0
    discovered_count = 0

    # product_url -> source catalogue page
    discovered_books = {}

    while current_url and catalogue_pages < 3:
        html, _ = get_page(current_url)
        soup = BeautifulSoup(html, "html.parser")

        catalogue_pages += 1

        books = soup.select("article.product_pod h3 a")

        for book in books:
            href = book.get("href")

            if href:
                product_url = urljoin(current_url, href)

                discovered_count += 1

                # Keep only the first occurrence of a URL.
                discovered_books.setdefault(product_url, current_url)

        next_link = soup.select_one("li.next a")

        if next_link and catalogue_pages < 3:
            current_url = urljoin(
                current_url,
                next_link.get("href"),
            )
        else:
            current_url = None

    print()
    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={discovered_count}")
    print(f"unique_urls={len(discovered_books)}")
    print()

    return discovered_books


def extract_book(product_url, source_page):
    html, fetched_at = get_page(product_url)
    soup = BeautifulSoup(html, "html.parser")

    product_main = soup.select_one("div.product_main")

    title = product_main.select_one("h1").get_text(strip=True)

    price_text = (
        product_main
        .select_one("p.price_color")
        .get_text(strip=True)
    )

    availability_text = (
        product_main
        .select_one("p.instock.availability")
        .get_text(" ", strip=True)
    )

    rating_tag = product_main.select_one("p.star-rating")
    rating_classes = rating_tag.get("class", [])

    rating_text = next(
        (
            class_name
            for class_name in rating_classes
            if class_name != "star-rating"
        ),
        None,
    )

    description_tag = soup.select_one(
        "#product_description + p"
    )

    description = (
        description_tag.get_text(" ", strip=True)
        if description_tag
        else None
    )

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


def extract_all_books(discovered_books):
    raw_records = []

    for product_url, source_page in discovered_books.items():
        record = extract_book(
            product_url,
            source_page,
        )

        raw_records.append(record)

    return raw_records


def normalize_price(price_text):
    cleaned_price = (
        price_text
        .replace("£", "")
        .replace(",", "")
        .strip()
    )

    return float(cleaned_price)


def validate_records(raw_records):
    valid_records = {}
    errors = []

    for raw_record in raw_records:
        try:
            normalized_record = {
                **raw_record,
                "price_gbp": normalize_price(
                    raw_record["price_text"]
                ),
            }

            validated = BookRecord.model_validate(
                normalized_record
            )

            record = validated.model_dump()

           # Keep only first occurance
            valid_records[record["product_url"]] = record

        except (ValidationError, ValueError) as exc:
            errors.append(
                {
                    "record": raw_record,
                    "reason": str(exc),
                }
            )

    return list(valid_records.values()), errors


def write_output(valid_records, errors):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    BOOKS_PATH.write_text(
        json.dumps(
            valid_records,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    ERRORS_PATH.write_text(
        json.dumps(
            errors,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main():
    discovered_books = discover_books()

    raw_records = extract_all_books(
        discovered_books
    )

    valid_records, errors = validate_records(
        raw_records
    )

    write_output(
        valid_records,
        errors,
    )

    print()
    print(f"valid_records={len(valid_records)}")
    print(f"invalid_records={len(errors)}")
    print(f"books_file={BOOKS_PATH}")
    print(f"errors_file={ERRORS_PATH}")


if __name__ == "__main__":
    main()