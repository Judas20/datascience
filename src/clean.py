"""Clean the scraped book data.

Run from the project root, after the scraper:

    python src/clean.py

Reads data/raw/books.csv, cleans the description column and writes the result to
data/processed/books_clean.csv. The raw text stays available in data/raw/books.csv.

How the cleaning was worked out is documented in notebooks/02_cleaning_eda.ipynb.
"""

from pathlib import Path

import pandas as pd

# Paths are based on where this file lives (src/), not on the folder you run it from
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = PROJECT_ROOT / "data" / "raw" / "books.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CLEAN_CSV = PROCESSED_DIR / "books_clean.csv"

# How many characters from the start to search for again to find the teaser.
# Tested in the notebook: 15-25 finds all 171 teasers, 40 misses 3, 10 gives a false match.
MATCH_LENGTH = 20

# Every real teaser ends at position 372-377. A repeat outside this range is real text.
TEASER_END_MIN = 350
TEASER_END_MAX = 400


def clean_description(description):
    """Remove the teaser, "...more" and special whitespace from one description."""
    description = description.removesuffix("...more")
    description = description.strip() # Remove leading and trailing whitespace

    # Find where the first characters appear again = where the teaser ends
    teaser_end = description.find(description[:MATCH_LENGTH], 1)
    # Only cut if the repeat is where a teaser ends.
    # A repeat anywhere else is real text, e.g. Crazy Rich Asians repeats its title later on.
    if TEASER_END_MIN <= teaser_end <= TEASER_END_MAX:
        description = description[teaser_end:]

    description = description.replace("\xad", "") # Remove soft hyphens (invisible characters inside words)
    description = " ".join(description.split())  # Turn non-breaking spaces and double spaces into one normal space

    return description


# This block only runs when the file is executed directly (python src/clean.py),
if __name__ == "__main__":
    df = pd.read_csv(RAW_CSV)
    print(f"Loaded {len(df)} books from {RAW_CSV}")

    # Overwrite the column
    df["description"] = df["description"].apply(clean_description)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_CSV, index=False)
    print(f"Saved {len(df)} books to {CLEAN_CSV}")
