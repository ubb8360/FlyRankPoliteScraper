# FlyRank Polite Scraper

A Python web scraping project for FlyRank's Backend Development Track.

## Target Classification

**Target:** Books to Scrape (`https://books.toscrape.com/`)

**Classification:** Books to Scrape is a public practice sandbox specifically designed for learning and testing web scraping.

**Scope:** This scraper will process only the first three catalogue pages, covering 60 books total.

**Data collected:** For each book, the scraper will collect its title, product URL, price, availability, rating, description, source catalogue page, and fetch timestamp. Later stages will normalize and validate this data before storing it.

**robots.txt result:** No robots file found. A request to `https://books.toscrape.com/robots.txt` returned HTTP `404 Not Found`.

A missing robots file is not treated as permission. This target is appropriate because Books to Scrape is intentionally provided as a practice sandbox for web scraping, and this project is limited to the first three catalogue pages.

The scraper will also use polite request behavior including an identifying user-agent, request timeouts, delays between real requests, and local caching.

I will not reuse this code on another site without checking its rules and terms first.
