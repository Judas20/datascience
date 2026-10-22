# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

School data science project: scrape the **Fiction** and **Nonfiction** categories from https://books.toscrape.com (title, description, cover image), then build classifiers that predict Fiction vs Nonfiction from text and image features, and compare them. Price, rating, stock and UPC are deliberately not scraped. The deliverable is a 4–6 page report with at most 2 images.

`PLAN.md` is the step-by-step roadmap (scraping → cleaning/EDA → features → models → evaluation → report). Read it before starting a new phase.

`DOCUMENTATION.md` is the running log the user will write the report from. Keep it up to date as part of the work, without being asked: whenever a step is finished, a decision is made or changed, or a result comes in, add it to the matching section. Record what was done, the decision and the reason for it, the actual numbers and results (check them against the data, never estimate), and a "For the report" note on what is worth writing up. If an earlier entry stops being true, correct it rather than adding a contradicting one. Mark each section's status and date.

The user is learning both data science and Claude Code. Explain the reasoning behind changes so they can understand and defend the work.

## Environment

Windows, PowerShell. Python virtualenv in `.venv/`:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/scraper.py   # scrape once (run from the project root)
python src/clean.py     # clean: data/raw/books.csv -> data/processed/books_clean.csv
jupyter lab
```

- `requirements.txt` is a full `pip freeze`, saved as UTF-8. When regenerating it, use `pip freeze | Out-File -Encoding utf8 requirements.txt`; PowerShell's plain `>` redirect would save it as UTF-16, which grep/diff tools can't read.
- pandas, Pillow and matplotlib are installed. scikit-learn is not installed yet; add it to the venv and to requirements.txt when the modelling work starts.
- There are no tests, linter or build step.

## Structure and conventions

- Scraping lives in `src/scraper.py`, which writes `data/raw/books.csv` (columns: title, category, description, image_url, image_path) and `data/raw/images/` (covers named by the book's URL slug; `image_path` is relative to `data/raw/`). Run code goes under `if __name__ == "__main__":` so functions can be imported into notebooks for testing.
- Cleaning lives in `src/clean.py`, which reads `data/raw/books.csv`, overwrites `description` with the cleaned text (the raw text stays in `data/raw/books.csv`) and writes `data/processed/books_clean.csv`. It has no built-in checks (the user removed them for simplicity). `image_path` in that file is still relative to `data/raw/`. The teaser-removal constants (`MATCH_LENGTH = 20`, cut only at position 350–400) were tested against the data. If they change or the data is re-scraped, re-verify the output: no `...more`, no empty descriptions, no `\xa0`/`\xad`/double spaces, same result when cleaned twice, and only *Crazy Rich Asians* still repeating its opening.
- Pattern for every step: work it out in a notebook, then move the final code into a script in `src/`. Notebooks keep the investigation and import functions from `src/` (`sys.path.append("../src")`) instead of copying them.
- Analysis happens in notebooks under `notebooks/`: `02_cleaning_eda` (cleaning investigation, plus exploration reading `data/processed/`) and `03_features_models` (reads `data/processed/`). `01_scrapeTest.ipynb` is a scratchpad for trying out selectors, and `demo.ipynb` holds BeautifulSoup practice.
- Scrape once. Notebooks load the CSV and never call the scraper or re-hit the site. When scraping, add a `time.sleep` between requests, check status codes, and skip images that already exist.
- Never overwrite `data/raw/` from the notebooks or `clean.py`. Cleaned output goes to `data/processed/`.

## Modelling constraints

- The dataset is small and imbalanced (~65 Fiction / ~110 Nonfiction). The majority-class baseline is ~63% accuracy.
- Keep models simple and explainable: Naive Bayes, Logistic Regression, Random Forest. No deep learning.
- Wrap TF-IDF and scalers in a scikit-learn `Pipeline` so they are fitted only on training folds, which avoids leakage.
- Evaluate with stratified 5-fold CV. Report macro precision/recall/F1 and a confusion matrix, not just accuracy.
