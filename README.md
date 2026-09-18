# The polite scraper

## Overview

**The polite scraper** is a production-grade, rate-limited web scraper built in Python for the FlyRank Internship Backend AI Engineering Week 5 Assignment A9.

The scraper follows a clean 6-stage architecture:
**fetch → extract → normalize → validate → store → report**

It targets [Books to Scrape](https://books.toscrape.com/) and processes **exactly the first three catalogue pages** to discover and collect data for **60 unique books**.

---

## Target Classification & Compliance

- **Target Site**: Books to Scrape (`https://books.toscrape.com/`)
- **Scope**: First 3 catalogue pages only (`page-1.html`, `page-2.html`, `page-3.html`).
- **Collected Fields**: Book title, product URL, raw price text, numeric price in GBP, availability, rating, product description, catalogue source URL, and fetch timestamp.
- **Appropriateness**: `https://toscrape.com/` explicitly hosts Books to Scrape as an open sandbox/practice target specifically intended for developers to practice web scraping without causing disruption or overloading production systems.
- **robots.txt Result**:
  - Request URL: `https://books.toscrape.com/robots.txt`
  - HTTP Status: `404 Not Found` — no robots file found.
  - Interpretation: A missing `robots.txt` file does not by itself grant permission to scrape. Books to Scrape is appropriate because it is publicly designated for web scraping practice.

> I will not reuse this code on another site without checking its rules and terms first.

---

## Tech Stack

- **Python**: 3.10+
- **HTTP Client**: `requests`
- **HTML Parser**: `beautifulsoup4`
- **Data Validation & Schemas**: `pydantic` (v2)

---

## Installation & Setup

Clone the repository and install dependencies in under 5 minutes:

```bash
# Navigate to the project directory
cd scraper

# Create a virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## Usage

### 1. Normal Scraping Run
To execute a standard scraping run:

```bash
python src/main.py
```

*Note: Ensure your working directory is the `scraper/` directory.*

Expected terminal output:
```text
CACHE HIT: Loaded https://books.toscrape.com/catalogue/page-1.html from cache\catalogue-page-1.html (50509 bytes)
...
valid_records=60
invalid_records=0
unique_records=60
failed_pages=0
```

### 2. Controlled Failure Test
To execute a local, controlled failure test (simulating a broken/404 detail page):

```bash
python src/main.py --test-failure
```

*This injects a single non-existent test URL to verify per-page failure isolation. It is an opt-in test mode and is never executed during normal scraping.*

Expected terminal output:
```text
HTTP 404 for https://books.toscrape.com/catalogue/nonexistent-broken-book_99999/index.html - skipping without retry.
PAGE FAILED: Could not fetch detail page for https://books.toscrape.com/catalogue/nonexistent-broken-book_99999/index.html [HTTP 404]
...
valid_records=60
invalid_records=0
unique_records=60
failed_pages=1
```

---

## Record Schema

Every collected book is validated against a Pydantic schema (`BookRecord`) containing nine fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `title` | `str` | Clean book title extracted from `.product_main h1`. |
| `product_url` | `str` | Absolute HTTPS URL of the book detail page. |
| `price_text` | `str` | Original raw price string (e.g. `"£51.77"`). |
| `price_gbp` | `float` | Numeric price value in GBP derived from `price_text` (e.g. `51.77`). |
| `availability_text` | `str` | Raw availability string (e.g. `"In stock (22 available)"`). |
| `rating_text` | `str` | Class-based rating string (e.g. `"Three"`). |
| `description` | `str \| None` | Product description text (`null` if missing). |
| `source_page` | `str` | Absolute HTTPS URL of the catalogue page where the book link was discovered. |
| `fetched_at` | `str` | ISO 8601 UTC timestamp recording when the page was fetched/loaded. |

---

## Politeness & Rate-Limiting Rules

- **Identifying User-Agent**: Every request includes an explicit header:  
  `User-Agent: FlyRankInternship-A9/1.0 (+https://github.com/Priyanshu1877/WEEK4EmptybutLive)`
- **Request Timeout**: All network requests enforce a 10.0-second timeout to prevent hanging.
- **Rate Limiting**: Enforces a minimum 500 ms delay (`time.sleep(0.5)`) between consecutive network requests.
- **Local Caching**: All fetched HTML pages are saved under `cache/`. Subsequent runs read from local disk to prevent unnecessary server load.
- **HTTP Status Validation**: Accepts HTTP 200 as successful responses.
- **Polite Retry Policy**:
  - **Timeout / HTTP 5xx Errors**: Retried exactly ONCE after a 1.0 s pause.
  - **HTTP 404 / 403 Errors**: Skipped immediately WITHOUT retry (404 indicates non-existent content; 403 indicates access refusal).

---

## Output Files

Output files are saved to `output/` (excluded from version control):

- **`output/books.json`**: JSON file containing the validated list of unique book records (exactly 60 on completion).
- **`output/errors.json`**: JSON file containing records that failed schema validation (empty `[]` on clean runs).
- **`output/run-report.json`**: Execution metrics and statistics for the run.

### Sample Run Report (`output/run-report.json`)
```json
{
  "started_at": "2026-09-18T19:05:18.520448+00:00",
  "duration_seconds": 0.45,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

---

## Project Structure

```text
scraper/
├── README.md
├── .gitignore
├── requirements.txt
├── sample/
│   └── books.sample.json
└── src/
    └── main.py
```

*Note: Local directories `cache/` and `output/` are excluded from Git via `.gitignore`.*

---

## Design Decisions & Notes

### Architectural Choice: Why No Headless Browser?
This assignment does not require browser automation (such as Playwright or Selenium) because Books to Scrape delivers all required book data directly within server-rendered HTML. Utilizing a headless browser would introduce unnecessary runtime overhead, heavy binary dependencies, and excess CPU/memory consumption without providing any functional benefit.

### Honest Limitation
This scraper is intentionally scoped to the first three catalogue pages of Books to Scrape and is not designed as a generic crawler for dynamic or login-protected websites.

### Web Scraping Ethics & Best Practices
- Always check for and utilize an official public API if available.
- Respect rate limits and maintain low request rates to protect server health.
- Never attempt to bypass authentication, paywalls, or anti-bot protections.
- Collect only the minimum necessary data required for your application.
