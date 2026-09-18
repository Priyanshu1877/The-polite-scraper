"""
The Polite Scraper — Stage 2: Catalogue Link Discovery
FlyRank Internship Backend AI Engineering Week 5 Assignment A9
"""

from pathlib import Path
import sys
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
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


def get_cache_path(url: str) -> Path:
    """Derives the cache file path for a given catalogue URL."""
    filename = Path(urlparse(url).path).name
    return CACHE_DIR / f"catalogue-{filename}"


def fetch_or_load_cached_page(
    url: str,
    last_fetch_time: list[float],
    user_agent: str = USER_AGENT,
    timeout: float = REQUEST_TIMEOUT,
) -> str:
    """
    Fetches the HTML page from the given URL or returns the cached HTML if present.

    - Uses cache if present and non-empty.
    - Enforces minimum 500ms delay before real network requests.
    - Only HTTP 200 is accepted on network fetch.
    - Uses an honest, identifying User-Agent.
    - Applies a request timeout to prevent hanging.
    """
    cache_path = get_cache_path(url)

    # Check if cache exists and is non-empty
    if cache_path.exists() and cache_path.stat().st_size > 0:
        html_content = cache_path.read_text(encoding="utf-8")
        rel_cache_path = cache_path.relative_to(SCRAPER_DIR)
        print(
            f"CACHE HIT: Loaded {url} from {rel_cache_path} ({len(html_content.encode('utf-8'))} bytes)"
        )
        return html_content

    # Enforce minimum request delay between real network requests
    if last_fetch_time[0] > 0:
        elapsed = time.time() - last_fetch_time[0]
        if elapsed < MIN_REQUEST_DELAY:
            time.sleep(MIN_REQUEST_DELAY - elapsed)

    # Cache miss: Perform HTTP request
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers, timeout=timeout)
    last_fetch_time[0] = time.time()

    # Enforce HTTP 200 requirement
    if response.status_code != 200:
        print(
            f"ERROR: Expected HTTP 200, got status code {response.status_code} for URL: {url}",
            file=sys.stderr,
        )
        sys.exit(1)

    html_content = response.text

    # Save to cache
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html_content, encoding="utf-8")

    rel_cache_path = cache_path.relative_to(SCRAPER_DIR)
    content_bytes = len(html_content.encode("utf-8"))
    print(
        f"FETCH: Requested {url} [HTTP {response.status_code}] -> Saved to {rel_cache_path} ({content_bytes} bytes)"
    )

    return html_content


def extract_book_urls(html_content: str, base_url: str) -> list[str]:
    """
    Extracts all book detail page URLs from a catalogue page HTML and converts
    them to absolute URLs using urllib.parse.urljoin.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    urls = []
    for article in soup.select("article.product_pod"):
        a_tag = article.select_one("h3 a")
        if a_tag and a_tag.get("href"):
            abs_url = urljoin(base_url, a_tag["href"])
            urls.append(abs_url)
    return urls


def extract_next_page_url(html_content: str, base_url: str) -> str | None:
    """
    Extracts the 'next' navigation link from a catalogue page HTML and converts
    it to an absolute URL using urllib.parse.urljoin.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    next_tag = soup.select_one("li.next a")
    if next_tag and next_tag.get("href"):
        return urljoin(base_url, next_tag["href"])
    return None


def run_stage2_discovery() -> tuple[int, int, int]:
    """
    Discovers all book URLs across MAX_PAGES catalogue pages starting from START_URL.
    Follows the site's own 'next' navigation links for pagination.
    """
    current_url = START_URL
    all_discovered_urls: list[str] = []
    pages_processed = 0
    last_fetch_time = [0.0]

    while current_url and pages_processed < MAX_PAGES:
        html_content = fetch_or_load_cached_page(current_url, last_fetch_time)
        pages_processed += 1

        book_urls = extract_book_urls(html_content, current_url)
        all_discovered_urls.extend(book_urls)

        if pages_processed < MAX_PAGES:
            current_url = extract_next_page_url(html_content, current_url)
        else:
            break

    # Deduplicate while maintaining order
    unique_urls = list(dict.fromkeys(all_discovered_urls))

    catalogue_pages = pages_processed
    discovered = len(all_discovered_urls)
    unique_urls_count = len(unique_urls)

    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={discovered}")
    print(f"unique_urls={unique_urls_count}")

    return catalogue_pages, discovered, unique_urls_count


def main() -> None:
    run_stage2_discovery()


if __name__ == "__main__":
    main()
