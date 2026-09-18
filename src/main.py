"""
The Polite Scraper — Stage 4: Data Normalization & Schema Validation
FlyRank Internship Backend AI Engineering Week 5 Assignment A9
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError, field_validator
import requests

# Configuration
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = (
    "FlyRankInternship-A9/1.0 (+https://github.com/Priyanshu1877/WEEK4EmptybutLive)"
)
REQUEST_TIMEOUT = 10.0  # seconds
MIN_REQUEST_DELAY = 0.5  # seconds between real network requests
MAX_PAGES = 3

# Resolve paths relative to scraper directory
SCRAPER_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = SCRAPER_DIR / "cache"
OUTPUT_DIR = SCRAPER_DIR / "output"


class BookRecord(BaseModel):
    """Pydantic schema for a normalized and validated book record."""

    title: str
    product_url: str
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: str
    description: str | None = None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        """Validates that URLs are absolute HTTPS URLs."""
        if not v.startswith("https://"):
            raise ValueError(f"URL must be an absolute HTTPS URL, got: {v}")
        return v


def normalize_price(price_text: str) -> float:
    """Extracts numeric price float from raw price_text (e.g. '£51.77' -> 51.77)."""
    match = re.search(r"(\d+\.\d+|\d+)", price_text)
    if match:
        return float(match.group(1))
    raise ValueError(f"Unable to parse numeric price from price_text: {price_text!r}")


def get_catalogue_cache_path(url: str) -> Path:
    """Derives the cache file path for a catalogue URL."""
    filename = Path(urlparse(url).path).name
    return CACHE_DIR / f"catalogue-{filename}"


def get_book_cache_path(url: str) -> Path:
    """Derives a safe cache file path for a book detail page URL."""
    parts = Path(urlparse(url).path).parts
    if len(parts) >= 2:
        slug = parts[-2]
        if slug and slug != "catalogue":
            return CACHE_DIR / "books" / f"{slug}.html"
    safe_name = urlparse(url).path.strip("/").replace("/", "_").replace(".html", "")
    return CACHE_DIR / "books" / f"{safe_name}.html"


def fetch_or_load_catalogue_page(
    url: str,
    last_fetch_time: list[float],
    user_agent: str = USER_AGENT,
    timeout: float = REQUEST_TIMEOUT,
) -> str:
    """Fetches a catalogue page or returns cached HTML."""
    cache_path = get_catalogue_cache_path(url)

    if cache_path.exists() and cache_path.stat().st_size > 0:
        html_content = cache_path.read_text(encoding="utf-8")
        rel_cache_path = cache_path.relative_to(SCRAPER_DIR)
        print(
            f"CACHE HIT: Loaded {url} from {rel_cache_path} ({len(html_content.encode('utf-8'))} bytes)"
        )
        return html_content

    if last_fetch_time[0] > 0:
        elapsed = time.time() - last_fetch_time[0]
        if elapsed < MIN_REQUEST_DELAY:
            time.sleep(MIN_REQUEST_DELAY - elapsed)

    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers, timeout=timeout)
    last_fetch_time[0] = time.time()

    if response.status_code != 200:
        print(
            f"ERROR: Expected HTTP 200, got status code {response.status_code} for URL: {url}",
            file=sys.stderr,
        )
        sys.exit(1)

    html_content = response.text
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html_content, encoding="utf-8")

    rel_cache_path = cache_path.relative_to(SCRAPER_DIR)
    content_bytes = len(html_content.encode("utf-8"))
    print(
        f"FETCH: Requested {url} [HTTP {response.status_code}] -> Saved to {rel_cache_path} ({content_bytes} bytes)"
    )

    return html_content


def extract_next_page_url(html_content: str, base_url: str) -> str | None:
    """Extracts the 'next' navigation link from a catalogue page HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    next_tag = soup.select_one("li.next a")
    if next_tag and next_tag.get("href"):
        return urljoin(base_url, next_tag["href"])
    return None


def discover_catalogue_book_items() -> list[dict[str, str]]:
    """Discovers unique book items from MAX_PAGES catalogue pages with source_page provenance."""
    current_url = START_URL
    discovered_items: list[dict[str, str]] = []
    pages_processed = 0
    last_fetch_time = [0.0]

    while current_url and pages_processed < MAX_PAGES:
        html_content = fetch_or_load_catalogue_page(current_url, last_fetch_time)
        pages_processed += 1

        soup = BeautifulSoup(html_content, "html.parser")
        for article in soup.select("article.product_pod"):
            a_tag = article.select_one("h3 a")
            if a_tag and a_tag.get("href"):
                abs_url = urljoin(current_url, a_tag["href"])
                discovered_items.append(
                    {"product_url": abs_url, "source_page": current_url}
                )

        if pages_processed < MAX_PAGES:
            current_url = extract_next_page_url(html_content, current_url)
        else:
            break

    # Deduplicate by product_url while preserving order and provenance
    seen_urls = set()
    unique_items = []
    for item in discovered_items:
        if item["product_url"] not in seen_urls:
            seen_urls.add(item["product_url"])
            unique_items.append(item)

    return unique_items


def fetch_or_load_book_page(
    url: str,
    last_fetch_time: list[float],
    user_agent: str = USER_AGENT,
    timeout: float = REQUEST_TIMEOUT,
) -> tuple[str, str]:
    """
    Fetches the HTML page for a book detail page or returns cached HTML.
    Returns (html_content, fetched_at_iso_string).
    """
    cache_path = get_book_cache_path(url)

    if cache_path.exists() and cache_path.stat().st_size > 0:
        html_content = cache_path.read_text(encoding="utf-8")
        mtime = cache_path.stat().st_mtime
        fetched_at = datetime.fromtimestamp(mtime, timezone.utc).isoformat()
        rel_cache_path = cache_path.relative_to(SCRAPER_DIR)
        print(
            f"CACHE HIT: Loaded detail page from {rel_cache_path} ({len(html_content.encode('utf-8'))} bytes)"
        )
        return html_content, fetched_at

    if last_fetch_time[0] > 0:
        elapsed = time.time() - last_fetch_time[0]
        if elapsed < MIN_REQUEST_DELAY:
            time.sleep(MIN_REQUEST_DELAY - elapsed)

    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers, timeout=timeout)
    last_fetch_time[0] = time.time()

    if response.status_code != 200:
        raise RuntimeError(
            f"Expected HTTP 200, got status code {response.status_code} for URL: {url}"
        )

    html_content = response.text
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html_content, encoding="utf-8")

    fetched_at = datetime.now(timezone.utc).isoformat()
    rel_cache_path = cache_path.relative_to(SCRAPER_DIR)
    content_bytes = len(html_content.encode("utf-8"))
    print(
        f"FETCH: Requested detail page {url} [HTTP {response.status_code}] -> Saved to {rel_cache_path} ({content_bytes} bytes)"
    )

    return html_content, fetched_at


def parse_book_detail_page(
    html_content: str, product_url: str, source_page: str, fetched_at: str
) -> dict:
    """Parses a book detail page HTML and extracts raw record fields."""
    soup = BeautifulSoup(html_content, "html.parser")

    title_elem = soup.select_one(".product_main h1")
    title = title_elem.text.strip() if title_elem else ""

    price_elem = soup.select_one(".product_main .price_color")
    price_text = price_elem.text.strip() if price_elem else ""

    avail_elem = soup.select_one(".product_main .availability")
    availability_text = " ".join(avail_elem.text.split()) if avail_elem else ""

    rating_elem = soup.select_one(".product_main .star-rating")
    rating_text = ""
    if rating_elem and rating_elem.get("class"):
        classes = [c for c in rating_elem["class"] if c != "star-rating"]
        if classes:
            rating_text = classes[0]

    desc_header = soup.select_one("#product_description")
    description = None
    if desc_header:
        desc_elem = desc_header.find_next_sibling("p")
        if desc_elem and desc_elem.text.strip():
            description = desc_elem.text.strip()

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


def process_and_validate_records() -> tuple[list[dict], list[dict]]:
    """Fetches, normalizes, and validates all book records."""
    book_items = discover_catalogue_book_items()
    valid_records: list[dict] = []
    invalid_records: list[dict] = []
    last_fetch_time = [0.0]

    for idx, item in enumerate(book_items, start=1):
        product_url = item["product_url"]
        source_page = item["source_page"]
        try:
            html_content, fetched_at = fetch_or_load_book_page(
                product_url, last_fetch_time
            )
            raw_record = parse_book_detail_page(
                html_content, product_url, source_page, fetched_at
            )

            # Stage 4: Normalize price_text -> price_gbp
            price_gbp = normalize_price(raw_record["price_text"])
            record_to_validate = {**raw_record, "price_gbp": price_gbp}

            # Stage 4: Validate against Pydantic schema
            validated_model = BookRecord(**record_to_validate)
            valid_records.append(validated_model.model_dump())

        except (ValidationError, Exception) as e:
            invalid_entry = {
                "product_url": product_url,
                "source_page": source_page,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            invalid_records.append(invalid_entry)

    # Deduplicate valid records by canonical product_url (idempotency)
    seen_urls = set()
    unique_valid_records = []
    for rec in valid_records:
        if rec["product_url"] not in seen_urls:
            seen_urls.add(rec["product_url"])
            unique_valid_records.append(rec)

    return unique_valid_records, invalid_records


def run_stage4_pipeline() -> None:
    """Executes Stage 4: extraction, normalization, validation, and output generation."""
    valid_records, invalid_records = process_and_validate_records()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write output/books.json
    books_file = OUTPUT_DIR / "books.json"
    books_file.write_text(
        json.dumps(valid_records, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Write output/errors.json
    errors_file = OUTPUT_DIR / "errors.json"
    errors_file.write_text(
        json.dumps(invalid_records, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    valid_count = len(valid_records)
    invalid_count = len(invalid_records)
    unique_count = len({r["product_url"] for r in valid_records})

    print(f"\nvalid_records={valid_count}")
    print(f"invalid_records={invalid_count}")
    print(f"unique_records={unique_count}")

    if valid_records:
        print("\nSample Validated Record (1 of 60):")
        print(json.dumps(valid_records[0], indent=2, ensure_ascii=False))


def main() -> None:
    run_stage4_pipeline()


if __name__ == "__main__":
    main()
