# Project Plan: Fiction vs Nonfiction Classifier

| Day | Step |
|-----|------|
| 1 | [Finish the scraper](#step-1-finish-the-scraper-day-1) |
| 2 | [Clean and explore the data](#step-2-clean-and-explore-the-data-day-2) |
| 2–3 | [Feature engineering](#step-3-feature-engineering-days-23) |
| 3–4 | [Model training](#step-4-model-training-days-34) |
| 4 | [Evaluation](#step-5-evaluation-day-4) |
| 5–6 | [Write the report](#step-6-write-the-report-days-56) |
| 7 | [Buffer](#day-7-buffer) |

---

## Step 1: Finish the scraper (Day 1) ✅

Done: `src/scraper.py` scraped **65 Fiction + 110 Nonfiction = 175 books** with all cover images. Details and decisions are in [DOCUMENTATION.md](DOCUMENTATION.md#1-data-collection).

The prototype in `01_scrapeTest.ipynb` worked, but it printed everything instead of storing it. It was moved into `src/scraper.py`, and the notebook stays as a scratchpad for trying out selectors.

### Changes to make

- [x] **Save the data.** Build one record per book and write all of them to `data/raw/books.csv` at the end. Each record holds:
  - title
  - category label
  - description
  - image URL
  - local image path
- [x] **Download the images.** The brief asks you to scrape the image itself, not just its URL. Save each cover to `data/raw/images/` and name the file by the book's URL slug (e.g. `its-only-the-himalayas_981.jpg`), so it stays paired with its row. Skip any image that already exists, so re-running after a crash doesn't download everything again.
- [x] **Explain which fields you kept.** The product page also has UPC, price, stock, rating, product type, tax and number of reviews. You deliberately keep only the text and the image, because those are what describe the book's content. Product type, tax and review count are the same for every book anyway. Mention this choice in the report. That covers the brief's *"is anything unnecessary?"* question.
- [x] **Make the functions self-contained.** The notebook version relies on `homepage_soup` and `base_url` from an earlier cell. In the script, each function should get what it needs through its arguments, so the file runs from top to bottom on its own.
- [x] **Add an entry point.** Put the code that runs the scrape under `if __name__ == "__main__":`. Then you can import functions like `scrape_category` into a notebook to test them without starting a full scrape.
- [x] **Be polite to the server.** Add a short `time.sleep` between requests, and check the status codes of the book pages too.
- [x] **Scrape once, then work from the CSV.** Run the script once from the project root with `python src/scraper.py`. The analysis notebooks only read `data/raw/books.csv` and never call the scraper.

> **Result:** exactly **65 Fiction** and **110 Nonfiction** books, **175 in total**. That's a small, imbalanced dataset, and it shapes everything after this step. Put the exact counts in the introduction.
>
> `data/raw/` is in `.gitignore`, so the scraped data is not in the repo. Anyone who clones it recreates the data with `python src/scraper.py`.

---

## Step 2: Clean and explore the data (Day 2)

The cleaning was worked out in `02_cleaning_eda.ipynb` and then moved into the script `src/clean.py`, the same way as the scraper. Run it from the project root:

```powershell
python src/clean.py
```

It reads `data/raw/books.csv`, cleans the `description` column and saves `data/processed/books_clean.csv`. The raw scrape is never overwritten. The notebook keeps the investigation (how the problems were found and the tests behind each decision) and the exploration below, which reads `data/processed/books_clean.csv`.

### Cleaning

- [x] **Missing descriptions:** checked, every book has one. Nothing to drop. Mention this in the report.
- [x] **Clean the text** (`clean_description()` in `src/clean.py`):
  - Removes the `...more` at the end (171 of 175 descriptions).
  - Removes the repeated teaser at the start (171 of 175), by matching the first 20 characters and only cutting at position 350–400.
  - Replaces non-breaking spaces and double spaces with single spaces, and deletes soft hyphens.
- [ ] **Optional: verification cell in the notebook.** Load `data/processed/books_clean.csv` and print a few counts as visible proof that the cleaning worked: no `...more`, no empty descriptions, no `\xa0`/`\xad`/double spaces, and only *Crazy Rich Asians* still repeating its opening. The expected results are in DOCUMENTATION.md.
- [x] **Non-English books:** only *Soumission* (French) is not in English. Decision: keep it. See DOCUMENTATION.md for how this was checked and why.
- [x] **Check duplicates and image integrity:** no duplicate titles, every row has an `image_path` pointing to an existing file, and all 175 images open without errors (checked with Pillow's `img.load()`).

### Exploration

Explore each of these, then write up what you find:

- [ ] Class balance
- [ ] Description and title length per class
- [ ] Most frequent words per class
- [ ] Average cover colour and brightness per class

> **Question to answer:** which features actually differ between Fiction and Nonfiction?
> My guess is that the text matters a lot and the covers much less. Test it rather than assume it.

---

## Step 3: Feature engineering (Days 2–3)

Build a text and an image feature set so you can compare them. **That comparison is what the grade rewards.**

| Feature set | Ideas |
|-------------|-------|
| **Text** | Bag-of-words or TF-IDF on title + description. Try with and without stop-word removal. Optionally add simple length features (description and title length). |
| **Title features** | Found in the exploration: colon in the title (subtitle), series marker (`#` + digit), title word count. TF-IDF drops punctuation, so these must be added as explicit features. A one-rule "colon → Nonfiction" classifier already gets 81%. |
| **Image** | Grayscale vs colour. Colour histograms (the brief's own suggestion). Simple statistics like mean brightness or saturation. Possibly a downscaled image (e.g. 32×32) flattened into a vector. |

Within each set, compare a few variants (e.g. TF-IDF with vs without stop words, grayscale vs colour histograms). That gives the comparison table more rows.

**Then try a combined set.** Join the feature vectors, or train separate models and average their predicted probabilities. This answers the brief's *"could the text be combined with the image?"* question.

---

## Step 4: Model training (Days 3–4)

Keep the models simple and easy to explain. With about 175 samples, deep learning isn't worth it.

| Role | Model |
|------|-------|
| **Baseline** | Always predict the majority class (≈ 63% accuracy). Every model has to beat it. |
| **Text** | Multinomial Naive Bayes, Logistic Regression. Both are standard for TF-IDF features and easy to justify. |
| **Image** | Logistic Regression or Random Forest |
| **Optional (unsupervised)** | KMeans with k=2 on the TF-IDF vectors. See how well the clusters match the real labels. The brief explicitly invites this kind of exploration. |

> ⚠️ **Pitfall to avoid: data leakage**
> Don't fit the TF-IDF vectorizer or the scaler on all the data before splitting. Put them in a scikit-learn `Pipeline` so they're fitted only on the training folds. Otherwise information from the test data leaks into training. It's worth one sentence in the report.

---

## Step 5: Evaluation (Day 4)

- **Stratified 5-fold cross-validation** instead of a single train/test split. With 175 samples, one split is too noisy, and stratifying keeps the class ratio the same in every fold.
- **Metrics:**
  - Accuracy is misleading on imbalanced data.
  - Also report **precision, recall and F1**, macro-averaged or per class.
  - Include a **confusion matrix**.
- **Comparison table:** one row per model and feature set, with *mean ± standard deviation* over the folds.
- **Error analysis:** read a few misclassified books. Expect borderline cases like memoirs, historical fiction, and *"a novel based on the life of…"* (one of these is already in your scrape output). These make good discussion material.

---

## Step 6: Write the report (Days 5–6, but start notes now)

**Requirements:** 4–6 pages, **at most 2 images**. Use the brief's section headings.

### Suggested images

1. The comparison chart (F1 for text, image and combined) **or** the confusion matrix of the best model
2. A few example covers from each class, to support the image discussion

Everything else can go in tables, which don't count as images.

### Discussion points

- The small dataset
- The class imbalance
- The fuzzy boundary between fiction and nonfiction
- Why you kept only text and images (and dropped price, rating etc.)
- Why image features probably underperform
- What you'd do with more time:
  - Scrape related categories like Mystery and History as extra training data
  - Use pretrained text embeddings or a pretrained CNN for the covers

### References

- books.toscrape.com
- scikit-learn (Pedregosa et al., 2011)
- BeautifulSoup
- The paper for any model you name (e.g. Breiman, 2001 for Random Forest)

---

## Day 7: Buffer

- [ ] Proofread
- [ ] Check the page count
- [ ] Export to PDF and submit

---

## Suggested project layout

```
src/
├── scraper.py                # run once: writes data/raw/
└── clean.py                  # reads data/raw/, writes data/processed/
notebooks/
├── 01_scrapeTest.ipynb       # scratchpad for trying out selectors
├── 02_cleaning_eda.ipynb     # cleaning investigation + exploration (reads data/processed/)
└── 03_features_models.ipynb  # reads data/processed/
data/
├── raw/
│   ├── books.csv
│   └── images/
└── processed/
    └── books_clean.csv
report/
```

> 💡 `data/raw/` and `__pycache__/` are in `.gitignore`. `data/processed/` is still tracked, so cleaned data can be committed if you want to.
