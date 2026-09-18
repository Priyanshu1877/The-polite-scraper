# The Polite Scraper — Stage 0: Check Before You Collect

## Overview
This repository contains a polite web scraper built for the FlyRank Internship Backend AI Engineering Week 5 Assignment A9.

## Target Classification

- **Target Site**: Books to Scrape (`https://books.toscrape.com/`)
- **Why this target is appropriate**: `https://toscrape.com/` explicitly hosts Books to Scrape as an open sandbox/practice site specifically intended for developers to practice web scraping without causing disruption, violating copyright, or overloading live production systems.
- **Scope**: First 3 catalogue pages only (`page-1.html`, `page-2.html`, `page-3.html`).
- **What data will be collected**: Book metadata from catalogue cards across the first 3 pages, including:
  - Title
  - Price (GBP)
  - Availability status (In stock / Out of stock)
  - Star rating
  - Detail page URL
- **Why this is appropriate for this assignment**: Restricting the crawl scope to 3 pages demonstrates responsible, rate-limited ingestion while validating HTML parsing and schema enforcement on a standard practice target.
- **robots.txt Result**:
  - Request URL: `https://books.toscrape.com/robots.txt`
  - HTTP Status: `404 Not Found` — no robots file found.
  - Interpretation: A missing `robots.txt` file is simply a missing file and does not by itself grant permission to scrape. This target is appropriate because Books to Scrape (`https://toscrape.com/`) is explicitly provided as a public sandbox intended for scraping practice.

## Responsible Scraping Commitment
I will not reuse this code on another site without checking its rules and terms first.

## Stage 1: Polite Fetch & Cache

- **Target Page**: `https://books.toscrape.com/catalogue/page-1.html`
- **Identifying User-Agent**: `FlyRankInternship-A9/1.0 (+https://github.com/Priyanshu1877/WEEK4EmptybutLive)`
- **Request Timeout**: 10.0 seconds to prevent hanging requests.
- **HTTP 200 Requirement**: Only HTTP status code 200 is accepted as a successful response before proceeding to save or parse.
- **Cache Location**: `scraper/cache/catalogue-page-1.html`
- **Cache Behavior**:
  - **First Run (Cache Miss)**: Issues an HTTP GET request, prints `FETCH ...`, verifies HTTP 200, and writes the response HTML to disk.
  - **Subsequent Runs (Cache Hit)**: Detects existing cache file, bypasses network requests completely, prints `CACHE HIT ...`, and loads HTML from disk.
- **Why Caching Matters**: Local caching prevents unnecessary network traffic and avoids placing repetitive load on target servers during development, debugging, and testing iterations.

## Stage 2: Catalogue Link Discovery

- **Catalogue Discovery**: Discovers all book detail page URLs across exactly the first 3 catalogue pages starting from `https://books.toscrape.com/catalogue/page-1.html`.
- **Following Next Link**: Navigates dynamically from page to page by parsing the HTML with Beautiful Soup and following the site's own `<li class="next"><a href="...">` pagination element rather than constructing or hardcoding page URLs.
- **Relative to Absolute URL Conversion**: Converts relative product URLs (`a-light-in-the-attic_1000/index.html`) into absolute HTTPS URLs using `urllib.parse.urljoin` without manual string concatenation.
- **Duplicate Removal**: Cleans and deduplicates discovered book URLs using order-preserving dictionary lookup (`dict.fromkeys()`).
- **Catalogue-Page Caching**: Caches each catalogue page locally (`catalogue-page-1.html`, `catalogue-page-2.html`, `catalogue-page-3.html`). On subsequent runs, network requests are completely bypassed by reading from disk.
- **Rate Limiting**: Enforces a minimum 500 ms delay (`time.sleep(0.5)`) between consecutive real network requests, maintaining identifying `User-Agent` headers and a 10.0-second timeout.

## Stage 3: Raw Detail Extraction

- **Detail-Page Discovery Source**: Processes all 60 unique book detail page URLs discovered directly from the 3 catalogue pages in Stage 2. No book URLs are hardcoded.
- **Eight Raw Fields**: Extracts exactly eight raw fields for each book detail page:
  1. `title`: Clean book title string from `.product_main h1`.
  2. `product_url`: Absolute HTTPS URL discovered in Stage 2.
  3. `price_text`: Preserved original displayed price text (e.g., `£51.77`). Remains unparsed raw text; price normalization belongs strictly to Stage 4.
  4. `availability_text`: Preserved original raw availability string (e.g., `In stock (22 available)`).
  5. `rating_text`: Preserved original rating class representation (e.g., `Three`).
  6. `description`: Extracted text from `#product_description + p`. Returns `null` if a book has no description (never invents or substitutes text).
  7. `source_page`: Exact catalogue page URL from which the book was discovered, providing full data provenance.
  8. `fetched_at`: ISO 8601 timestamp recording when the detail page HTML was fetched/loaded.
- **Selector Rules**: Targeted specifically at the `.product_main` product container and explicit element IDs rather than generic page-wide text matching.
- **Detail-Page Caching**: Caches each fetched detail page locally under `cache/books/<safe-book-cache-name>.html`. Subsequent runs read directly from cache without hitting the live site.
- **Polite Fetching Rules**: Enforces identifying `User-Agent`, 10.0 s timeout, HTTP 200 validation, and minimum 500 ms delay between real network requests.

