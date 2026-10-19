"""Scrape the Fiction and Nonfiction categories from books.toscrape.com.

Run once from the project root:

    python src/scraper.py                 # full scrape (~175 books)
    python src/scraper.py --max-books 2   # quick test: 2 books per category

Writes data/raw/books.csv (title, category, description, image_url, image_path)
and the cover images to data/raw/images/.
"""

import argparse
import csv
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup as bs

BASE_URL = "https://books.toscrape.com/"
CATEGORIES = ["Fiction", "Nonfiction"]

# Paths are based on where this file lives (src/), not on the folder you run it from,
# so the data always ends up in <project root>/data/raw.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
IMAGE_DIR = RAW_DIR / "images"

# Seconds to wait between requests, so we don't hammer the server. This is a polite courtesy to the website owner and also helps avoid getting blocked. This is actually not needed for this site since it's a test site, but it's good practice for real-world scraping.   
DELAY = 0.5            


def get_soup(url):
    """Download a page and return it parsed. Returns None if the request fails."""
    time.sleep(DELAY)
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve {url} (status code {response.status_code})")
        return None
    return bs(response.content, "html.parser")


def download_image(image_url, filename):
    """Save a cover image to IMAGE_DIR. Skips it if the file already exists."""
    path = IMAGE_DIR / filename
    if path.exists():
        return path

    time.sleep(DELAY)
    response = requests.get(image_url)
    if response.status_code != 200:
        print(f"Failed to download image {image_url}")
        return None

    # Images are binary data, so write bytes ("wb"), not text
    with open(path, "wb") as f:
        f.write(response.content)
    return path


def scrape_book(book_url, category_name):
    """Scrape one book page and return its data as a dict (one CSV row)."""
    soup = get_soup(book_url)
    if soup is None:
        return None

    # Some books have no description, so store an empty string instead of crashing
    description_tag = soup.select_one("#product_description + p")
    description = description_tag.get_text(" ", strip=True) if description_tag else ""

    # Image src is relative ("../../media/..."), so urljoin makes it a full URL
    image_url = urljoin(book_url, soup.select_one(".item.active img")["src"])

    # Name the image after the book's URL slug, which is unique per book:
    # ".../catalogue/its-only-the-himalayas_981/index.html" -> "its-only-the-himalayas_981.jpg"
    slug = book_url.rstrip("/").split("/")[-2]
    image_path = download_image(image_url, f"{slug}.jpg")

    return {
        "title": soup.h1.get_text(strip=True),
        "category": category_name,
        "description": description,
        "image_url": image_url,
        # Path relative to data/raw, so each row knows which image file is its cover
        "image_path": image_path.relative_to(RAW_DIR).as_posix() if image_path else "",
    }


def scrape_category(category_name, max_books=None):
    """Scrape every book in a category and return a list of dicts.

    max_books: stop after this many books (handy for quick tests). None = all.
    """
    homepage = get_soup(BASE_URL)
    if homepage is None:
        return []

    # Find the category link in the sidebar by its name
    category_link = next(
        (
            link
            for link in homepage.select("ul.nav-list a")
            if link.get_text(strip=True).casefold() == category_name.casefold()
        ),
        None,
    )
    if category_link is None:
        print(f"Category not found: {category_name}")
        return []  # an empty list, so "+" still works when combining categories

    records = []
    page_url = urljoin(BASE_URL, category_link["href"])

    # Keep going until there is no "next" button
    while page_url:
        print(f"Scraping page: {page_url}")
        page = get_soup(page_url)
        if page is None:
            break

        for book in page.select("h3 a"):
            book_url = urljoin(page_url, book["href"])
            record = scrape_book(book_url, category_name)
            if record:
                records.append(record)
                print(f"  {len(records):>3}. {record['title']}")

            if max_books and len(records) >= max_books:
                return records

        next_link = page.select_one("li.next a")
        page_url = urljoin(page_url, next_link["href"]) if next_link else None

    return records


def save_csv(records, path):
    """Write a list of dicts to a CSV file, one row per dict."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()       # first line: column names
        writer.writerows(records)  # one line per dict


# This block only runs when the file is executed directly (python src/scraper.py),
# not when a notebook does "from scraper import scrape_book".
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape books.toscrape.com")
    parser.add_argument(
        "--max-books",
        type=int,
        default=None,
        help="stop after this many books per category (for quick tests)",
    )
    args = parser.parse_args()

    # Create the output folders if they don't exist yet
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    all_books = []
    for category in CATEGORIES:
        all_books += scrape_category(category, max_books=args.max_books)

    if not all_books:
        print("No books scraped, nothing saved.")
    else:
        csv_path = RAW_DIR / "books.csv"
        save_csv(all_books, csv_path)
        print(f"\nSaved {len(all_books)} books to {csv_path}")
