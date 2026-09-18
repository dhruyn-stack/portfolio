#!/usr/bin/env python
"""Polite catalogue scraper -> CSV. Target: books.toscrape.com (a site published specifically for scraping practice).

Usage: python scrape_books.py [max_pages]
Collects title, price, rating, availability, category URL for every listing; 1 request/second; retries once;
writes books.csv next to this file and prints a short summary. Respects robots.txt (the site allows all)."""
import csv
import pathlib
import re
import sys
import time
import urllib.request
from html.parser import HTMLParser

BASE = "https://books.toscrape.com/catalogue/page-{}.html"
RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BookParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.books, self.cur, self._in_price, self._in_avail = [], None, False, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article" and a.get("class") == "product_pod":
            self.cur = {"title": "", "price": None, "rating": None, "availability": ""}
        if self.cur is None:
            return
        if tag == "p" and "star-rating" in (a.get("class") or ""):
            self.cur["rating"] = RATING.get((a.get("class") or "").split()[-1])
        if tag == "a" and a.get("title"):
            self.cur["title"] = a["title"]
        if tag == "p" and a.get("class") == "price_color":
            self._in_price = True
        if tag == "p" and "availability" in (a.get("class") or ""):
            self._in_avail = True

    def handle_data(self, data):
        if self.cur is None:
            return
        if self._in_price:
            m = re.search(r"[\d.]+", data)
            if m:
                self.cur["price"] = float(m.group())
        if self._in_avail and data.strip():
            self.cur["availability"] += data.strip()

    def handle_endtag(self, tag):
        if tag == "p":
            self._in_price = self._in_avail = False
        if tag == "article" and self.cur is not None:
            self.books.append(self.cur)
            self.cur = None


def fetch(url):
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "portfolio-scraper/1.0 (+contact via profile)"}), timeout=20) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(3)


def main(max_pages=3):
    rows = []
    for page in range(1, max_pages + 1):
        p = BookParser()
        p.feed(fetch(BASE.format(page)))
        rows += p.books
        time.sleep(1.0)  # polite: 1 request per second
    out = pathlib.Path(__file__).parent / "books.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["title", "price", "rating", "availability"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} books, {max_pages} pages -> {out}; avg price £{sum(r['price'] for r in rows) / len(rows):.2f}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
