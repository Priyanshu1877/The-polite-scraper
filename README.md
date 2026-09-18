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


