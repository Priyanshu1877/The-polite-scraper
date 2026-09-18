"""
The Polite Scraper - Stage 1: Polite Fetch & Cache
FlyRank Internship Backend AI Engineering Week 5 Assignment A9
"""

from pathlib import Path
import sys
import requests

# Stage 1 Configuration
TARGET_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/Priyanshu1877/WEEK4EmptybutLive)"
REQUEST_TIMEOUT = 10.0  # seconds

# Resolve paths relative to scraper directory
SCRAPER_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = SCRAPER_DIR / "cache"
CACHE_FILE = CACHE_DIR / "catalogue-page-1.html"


def fetch_or_load_cached_page(
    url: str = TARGET_URL,
    cache_path: Path = CACHE_FILE,
    user_agent: str = USER_AGENT,
    timeout: float = REQUEST_TIMEOUT,
) -> str:
    """
    Fetches the HTML page from the given URL or returns the cached HTML if present.

    - Only HTTP 200 is accepted on network fetch.
    - Uses an honest, identifying User-Agent.
    - Applies a request timeout to prevent hanging.
    - Caches the response to disk to avoid repeated network requests.
    """
    # Check if cache exists and is non-empty
    if cache_path.exists() and cache_path.stat().st_size > 0:
        html_content = cache_path.read_text(encoding="utf-8")
        rel_cache_path = cache_path.relative_to(SCRAPER_DIR)
        print(
            f"CACHE HIT: Loaded {url} from {rel_cache_path} ({len(html_content.encode('utf-8'))} bytes)"
        )
        return html_content

    # Cache miss: Perform HTTP request
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers, timeout=timeout)

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


def main() -> None:
    fetch_or_load_cached_page()


if __name__ == "__main__":
    main()
