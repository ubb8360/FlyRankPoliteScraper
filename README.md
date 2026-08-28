# FlyRank Polite Scraper

A polite web scraping pipeline built in Python for FlyRank's Backend Development Track.

This project processes the first three catalogue pages of Books to Scrape, discovers 60 books, extracts structured information from each book page, normalizes and validates the data, stores the results as JSON, handles individual page failures without crashing, and produces a report describing what happened during each run.

## Target Classification

**Target:** Books to Scrape (`https://books.toscrape.com/`)

**Classification:** Books to Scrape is a public practice sandbox specifically designed for learning and testing web scraping.

**Scope:** This scraper processes only the first three catalogue pages, covering 60 books total.

**Data collected:** For each book, the scraper collects its title, product URL, price, availability, rating, description, source catalogue page, and fetch timestamp.

**robots.txt result:** No robots file found. A request to `https://books.toscrape.com/robots.txt` returned HTTP `404 Not Found`.

A missing robots file is not treated as permission. This target is appropriate because Books to Scrape is intentionally provided as a practice sandbox for web scraping, and this project is limited to the first three catalogue pages.

I will not reuse this code on another site without checking its rules and terms first.

## Tech Stack

This project uses the Python lane for the assignment.

- Python 3
- Requests
- Beautiful Soup
- Pydantic
- Python's built-in JSON module
- Git and GitHub

## Project Structure

```text
FlyRankPoliteScraper/
├── src/
│   └── main.py
├── output/
│   ├── books.json
│   ├── errors.json
│   └── run-report.json
├── .gitignore
├── README.md
└── requirements.txt
```

The local `cache/` directory is excluded from Git because it contains downloaded HTML pages used during development.

## Installation

Clone the repository:

```bash
git clone https://github.com/ubb8360/FlyRankPoliteScraper.git
cd FlyRankPoliteScraper
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
python -m pip install -r requirements.txt
```

## Run

Run the complete scraping pipeline with:

```powershell
python src/main.py
```

A successful run creates or updates:

```text
output/
├── books.json
├── errors.json
└── run-report.json
```

## Pipeline

The scraper follows this pipeline:

```text
fetch -> extract -> normalize -> validate -> store -> report
```

The first three catalogue pages are used to discover 60 unique book URLs. Each book detail page is then processed individually.

## Record Schema

Each validated book record contains the following fields:

| Field | Type | Description |
|---|---|---|
| `title` | string | Title of the book |
| `product_url` | string | Absolute canonical URL for the book |
| `price_text` | string | Original scraped price, such as `£51.77` |
| `price_gbp` | float | Normalized numeric price, such as `51.77` |
| `availability_text` | string | Availability text from the product page |
| `rating_text` | string | Text representation of the star rating |
| `description` | string or null | Book description when available |
| `source_page` | string | Catalogue page where the book was discovered |
| `fetched_at` | string | UTC timestamp associated with the downloaded page |

Pydantic validates each normalized record before it is stored.

Records that pass validation are written to:

```text
output/books.json
```

Records that fail validation are written to:

```text
output/errors.json
```

along with the reason they failed.

## Normalization

Scraped values are not trusted automatically.

For example, the raw price:

```text
£51.77
```

is preserved as:

```json
"price_text": "£51.77"
```

and is also converted into a numeric value:

```json
"price_gbp": 51.77
```

This allows another program to sort, compare, or calculate using the price while still preserving the original scraped value.

## Canonical URLs and Duplicate Prevention

The absolute `product_url` is used as each book's canonical identity.

If the same book URL is discovered more than once, only one record is stored.

Running the scraper multiple times therefore does not continue adding duplicate books. A successful run still produces exactly 60 unique records.

## Politeness Rules

The scraper follows several rules to reduce unnecessary requests and behave respectfully toward the target site.

### Identifying User-Agent

Every real HTTP request sends an identifying user-agent containing a link to this repository.

```text
FlyRankInternship-A9/1.0 (+https://github.com/ubb8360/FlyRankPoliteScraper)
```

### Request Timeout

Every network request has a timeout so the program does not wait forever for a response.

### Status Checking

A page is parsed only after checking its HTTP response status.

HTTP `200` is treated as a successful page response.

### Request Delay

The scraper waits at least 500 milliseconds between real network requests.

Cached pages do not require a delay because they are read directly from the local computer.

### Local Cache

Downloaded HTML is stored locally inside:

```text
cache/
```

During later development runs, the scraper reads the saved HTML instead of repeatedly requesting the same pages from the website.

The cache directory is excluded from Git.

### Retry Rules

If a request times out or receives a server-side `5xx` response, the scraper waits and tries one more time.

Responses such as `403` and `404` are not retried.

A `404` means the requested page does not exist, while a `403` means the server refused the request. Repeating those requests would not be useful or polite.

## Failure Handling

Each book detail page is processed separately.

If one page fails, that failure is recorded and the scraper continues processing the remaining pages instead of terminating the entire run.

For Stage 5, one deliberately fake book URL is added:

```text
https://books.toscrape.com/catalogue/this-book-does-not-exist-stage-5/index.html
```

The page returns HTTP `404`, so the scraper logs and skips it.

The failure does not remove or corrupt the successfully collected books.

The final result still contains:

```text
valid_records=60
invalid_records=0
failed_pages=1
```

## Run Report

Every execution writes a report to:

```text
output/run-report.json
```

The report includes:

- start time
- duration
- pages fetched from the network
- cache hits
- valid records
- invalid records
- failed pages
- details about individual failures

### Example From a Real Run

```json
{
  "start_time": "2026-08-28T12:15:13.303237Z",
  "duration_seconds": 5.904,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failures": [
    {
      "url": "https://books.toscrape.com/catalogue/this-book-does-not-exist-stage-5/index.html",
      "reason": "HTTP 404: https://books.toscrape.com/catalogue/this-book-does-not-exist-stage-5/index.html"
    }
  ]
}
```

## Output

### `books.json`

Contains the 60 validated and normalized book records.

### `errors.json`

Contains records that failed schema validation and the reason for each validation failure.

A normal successful run currently produces zero validation errors.

### `run-report.json`

Contains summary statistics and failure information for the most recent run.

## Why No Browser Is Needed

The core assignment does not require browser automation because the book data is already included in the HTML returned directly by the server.

A normal HTTP request can therefore retrieve the information needed by the scraper.

Using browser automation such as Playwright for this target would add unnecessary execution time, memory usage, and complexity without providing useful additional data.

## Limitations

This scraper is intentionally limited to the first three catalogue pages of Books to Scrape.

It is also designed around the current HTML structure of that practice site. If the site changes its HTML structure or CSS classes, some selectors may need to be updated.

The scraper is not intended to be reused on arbitrary websites without first reviewing the site's rules, terms, available APIs, and scraping policies.

## Ethics

When an official API exists, it should generally be preferred over scraping.

A scraper should not bypass logins, paywalls, authentication systems, access controls, or blocks.

Only the data necessary for the intended task should be collected.

Before using scraping code on another website, that site's rules and terms should be reviewed first.

## Assignment Checkpoint Results

The final scraper successfully demonstrates the required behaviors:

- Processes exactly the first 3 catalogue pages
- Discovers 60 book links
- Produces 60 unique product URLs
- Extracts all required raw fields
- Converts prices into numeric GBP values
- Preserves both raw and normalized price values
- Validates records with Pydantic before storage
- Produces exactly 60 validated records
- Produces the same 60 records after rerunning
- Uses an identifying user-agent
- Uses request timeouts
- Waits at least 500 milliseconds between real requests
- Uses local caching during development
- Does not retry `404` or `403` responses
- Retries a timeout or `5xx` response once
- Survives an intentionally broken book URL
- Reports the broken URL instead of crashing
- Writes `books.json`
- Writes `errors.json`
- Writes `run-report.json`

## Repository

GitHub:

```text
https://github.com/ubb8360/FlyRankPoliteScraper
```