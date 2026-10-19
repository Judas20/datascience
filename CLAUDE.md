# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

School data science project: scrape the **Fiction** and **Nonfiction** categories from https://books.toscrape.com (title, description, cover image, price, rating, stock, UPC), then build classifiers that predict Fiction vs Nonfiction from text, image and metadata features, and compare them. The deliverable is a 4–6 page report with at most 2 images.

`PLAN.md` is the step-by-step roadmap (scraping → cleaning/EDA → features → models → evaluation → report). Read it before starting a new phase.

The user is learning both data science and Claude Code. Explain the reasoning behind changes so they can understand and defend the work.

## Environment

Windows, PowerShell. Python virtualenv in `.venv/`:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/scraper.py   # scrape once (run from the project root)
jupyter lab
```

- `requirements.txt` is a full `pip freeze` saved as **UTF-16 LE** (PowerShell's `>` redirect). Grep/diff tools may not read it as text. When regenerating it, use `pip freeze | Out-File -Encoding utf8 requirements.txt`.
- pandas, scikit-learn and Pillow are not installed yet. PLAN.md needs them for later phases, so add them to the venv and to requirements.txt when that work starts.
- There are no tests, linter or build step.

## Structure and conventions

- Scraping lives in `src/scraper.py`, which writes `data/raw/books.csv` and `data/raw/images/` (covers named by UPC or URL slug so each image stays paired with its row). Run code goes under `if __name__ == "__main__":` so functions can be imported into notebooks for testing.
- Analysis happens in notebooks under `notebooks/`: `02_cleaning_eda` (reads `data/raw/`, writes `data/processed/books_clean.csv`) and `03_features_models` (reads `data/processed/`). `scrapeTest.ipynb` is a scratchpad for trying out selectors, and `demo.ipynb` holds BeautifulSoup practice.
- Scrape once. Notebooks load the CSV and never call the scraper or re-hit the site. When scraping, add a `time.sleep` between requests, check status codes, and skip images that already exist.
- Never overwrite `data/raw/` from the notebooks. Cleaned output goes to `data/processed/`.

## Modelling constraints

- The dataset is small and imbalanced (~65 Fiction / ~110 Nonfiction). The majority-class baseline is ~63% accuracy.
- Keep models simple and explainable: Naive Bayes, Logistic Regression, Random Forest. No deep learning.
- Wrap TF-IDF and scalers in a scikit-learn `Pipeline` so they are fitted only on training folds, which avoids leakage.
- Evaluate with stratified 5-fold CV. Report macro precision/recall/F1 and a confusion matrix, not just accuracy.
