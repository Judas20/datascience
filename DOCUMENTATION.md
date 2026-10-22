# Project Documentation

A running log of what has been done in the project, which decisions were made and why, and what the results were. It is the raw material for the report: each section maps to a part of the report, and the **For the report** notes point out what is worth writing up.

---

## 1. Data collection

*Status: done (2026-10-19)*

### Source

- Website: [books.toscrape.com](https://books.toscrape.com), a demo bookshop made for practising web scraping.
- Categories scraped: **Fiction** and **Nonfiction** (these two categories are the class labels).
- Tools: Python with `requests` (downloading pages) and `BeautifulSoup` (parsing HTML).

### How the scraper works

The final scraper is [src/scraper.py](src/scraper.py), run once from the project root with `python src/scraper.py`. For each category it:

1. Finds the category link in the sidebar of the homepage.
2. Goes through every page of the category, following the "next" button until there is none (pagination).
3. Opens each book's own page and reads the title, the description and the cover image URL.
4. Downloads the cover image to `data/raw/images/`.
5. After both categories, writes all books to `data/raw/books.csv`, one row per book.

The scraper waits 0.5 seconds between requests and checks the status code of every response.

### Development process

The scraper was built step by step in the notebook [notebooks/01_scrapeTest.ipynb](notebooks/01_scrapeTest.ipynb):

1. Scraped all book titles from the homepage.
2. Scraped the links to each book's page.
3. Followed the links and scraped the descriptions.
4. Added the cover image URLs.
5. Limited the scrape to one category (Fiction) instead of the whole site.
6. Turned the code into a function `scrape_category(category_name)` that works for any category.
7. Added pagination, since categories are spread over several pages (`page-2.html`, `page-3.html`, ...).
8. Stored the data in a CSV file instead of printing it.

Finally the code was moved from the notebook into the script `src/scraper.py`.

### Decisions and why

| Decision | Reason |
|----------|--------|
| Scraper as a script (`src/scraper.py`), not a notebook | Scraping only has to run once. A script always runs from top to bottom with no hidden state from earlier cells, and keeps data collection separate from the analysis. |
| Scrape once, analyse from the CSV | The analysis notebooks never re-scrape the site. This is faster, kinder to the server, and every analysis uses exactly the same data. |
| Keep only title, category, description and cover image | These describe the content of the book, which is what decides fiction vs nonfiction. The product page also has UPC, price, stock, rating, product type, tax and number of reviews. These were left out on purpose: product type, tax and number of reviews are identical for every book, and price, stock and rating say nothing about the book's content. |
| Download the cover images, not just their URLs | The assignment asks for the images themselves to be scraped, and the image features need the files. |
| Name images by the book's URL slug (e.g. `soumission_998.jpg`) and store the path in an `image_path` column | The slug is unique per book, so each image stays paired with its row in the CSV. |
| Wait 0.5 s between requests | Good scraping practice so the server isn't overloaded. With ~350 requests the full scrape still takes only about 3 minutes. |
| Skip images that already exist | If the scraper crashes halfway, a re-run doesn't download everything again. |
| Save the CSV as UTF-8 | The descriptions contain special characters (curly quotes, accented letters in French text). |
| Keep the raw data out of git (`data/raw/` in `.gitignore`) | The data can be recreated at any time by running the scraper, and the 175 images would bloat the repository. |

### Result

| | Count |
|---|---|
| Fiction | 65 |
| Nonfiction | 110 |
| **Total** | **175** |

- CSV columns: `title`, `category`, `description`, `image_url`, `image_path`.
- Every book has a description and a cover image (175 images, all files present).
- No duplicate titles.
- Nonfiction makes up about 63% of the data, so a model that always guesses "Nonfiction" is right 63% of the time. That is the baseline every model has to beat.

### Observations for the next steps

- 171 of 175 descriptions end with `...more`, which has to be removed when cleaning the text.
- **171 of 175 descriptions contain their opening text twice.** The site puts a short teaser (the first ~375 characters, cut off mid-word) in front of the full description. So each description is *teaser + full text + "...more"*. The 4 without a teaser are short descriptions (30–364 characters) where the teaser would be the whole text. This inflates word counts and counts the first ~60 words of each description twice, so it has to be removed when cleaning.
  - In 3 of the 171, the teaser is not an exact copy: the full text contains non-breaking spaces (`\xa0`) that are missing from the teaser (e.g. *Becoming Wise*, *Trespassing Across America*, *The Name of God is Mercy*). Matching on the first 40 characters misses these; matching on the first 20 finds all 171, always at position 372–377 in the text.
- **Special whitespace characters:** 34 descriptions contain non-breaking spaces (`\xa0`, 247 in total) and a few contain soft hyphens (`\xad`, 3 in total, invisible characters inside words). Most non-breaking spaces act as normal word separators (41 sit directly between two letters), so they should be replaced by a normal space, not deleted, otherwise words get glued together. Soft hyphens should be deleted, otherwise word tokenizers split the word in two (`some\xadthing` → `some`, `thing`). Normalizing these alone does not fix the teaser matching: the teaser is missing the space completely (`wit,Trespassing` vs `wit,\xa0Trespassing`), so with a 40-character match 2 teasers are still missed.
- At least one book is not in English: *Soumission* (Fiction) has a French description.
- After removing the teaser and `...more`, descriptions are of similar length in both classes (median 173 words for Fiction, 201.5 for Nonfiction; before cleaning it was 237 vs 265), so description length alone probably won't separate the classes well.
- Garbled characters (`�`) showed up when printing descriptions in the notebook. Checking the raw data showed this is only a display problem in the notebook output. The data itself is decoded correctly.

> **For the report:**
> - *Data collection* section: the source, the two categories, the step-by-step scraping method and the final counts (65 / 110 / 175).
> - *"Is anything unnecessary?"*: explain which fields were deliberately left out and why (see the decisions table).
> - Mention the class imbalance and the 63% baseline already in the introduction.
> - *Soumission* is a good example for the discussion: a text model trained mostly on English won't handle a French description well.

---

## 2. Cleaning and exploration

*Status: in progress (2026-10-19). Description cleaning done and saved; non-English books and exploration not started.*

The cleaning was worked out in [notebooks/02_cleaning_eda.ipynb](notebooks/02_cleaning_eda.ipynb) using pandas, then moved into the script [src/clean.py](src/clean.py), run with `python src/clean.py`. It reads `data/raw/books.csv`, replaces the `description` column with the cleaned text, and saves `data/processed/books_clean.csv` (175 rows, same 5 columns as the raw file). The script has no built-in checks, to keep it simple: the cleaning was verified once on the full dataset (results below), and since the raw data doesn't change, that verification still holds. It only needs repeating if the data is re-scraped. Like the scraper, the cleaning is a fixed step from raw to processed data, so a script keeps one version of the code and can't break from cells run twice or out of order. The notebook keeps the investigation behind each decision.

### Inspection

- 175 rows, 5 columns, no missing values in any column. Class counts confirmed: 110 Nonfiction, 65 Fiction.
- Reading the first descriptions showed the two problems from section 1: a repeated teaser at the start and `...more` at the end.

### Description cleaning: `clean_description()`

Steps, in this order:

1. Remove `...more` from the end, then strip surrounding whitespace.
2. Find the teaser: search for the first 20 characters of the description again, starting from position 1.
3. Only cut if that repeat is found at position 350–400; keep the text from there.
4. Remove soft hyphens (`\xad`).
5. Collapse all whitespace (non-breaking spaces, double spaces) into single normal spaces with `" ".join(text.split())`.

| Decision | Reason |
|----------|--------|
| Match on the first **20** characters | Tested lengths: 40 characters missed 3 teasers, because the full text contains non-breaking spaces that the teaser lacks. 15–25 found all 171. 10 caused a false match at position 304, in the middle of a teaser. 20 sits in the middle of the safe range. |
| Only cut when the repeat is at position **350–400** | Every real teaser ends at position 372–377. Without this check, cleaning *Crazy Rich Asians* twice cut it from 1423 to 265 characters, because its title genuinely appears again later in the text. The range check makes the function safe to run twice and guards against false matches. |
| Remove the teaser **before** cleaning whitespace | The tested positions were measured on the raw text; cleaning whitespace first would shift them. |
| Replace non-breaking spaces with a normal space, delete soft hyphens | See the special whitespace characters in section 1. |
| Overwrite `description` with the cleaned text instead of adding a second column | The raw text is already preserved in `data/raw/books.csv`, so a second column would only duplicate it. With a single `description` column, later steps can't accidentally use the uncleaned text. For before/after comparisons, load both files. |

**Verified on all 175 descriptions:** none ends with `...more`, none is empty, all 171 teasers removed (only *Crazy Rich Asians* still repeats its opening, which is real text), no non-breaking spaces, soft hyphens, double spaces or surrounding whitespace left, and running the function twice gives the same result.

### Non-English books

**Only 1 of 175 books is not in English: *Soumission* (Fiction, French).** Decision: **keep it** (dataset stays at 175 books: 65 Fiction, 110 Nonfiction).

How this was found (2026-10-20):

1. An "English score" per description: the share of words that are very common English words (*the, and, or, but, in, on, at, to, for, of, with, by*). Books scoring below 0.1 were read by hand.
2. Four books scored below 0.1, but only *Soumission* (score 0.0) is foreign. The other three are short English texts: *Kindle Paperwhite User's Guide* (0.0, the description is just the title, 4 words), *Data, A Love Story* (0.069) and *The Bourne Identity* (0.087).
3. Cross-checked with two other methods: counting common French/German/Spanish/Italian/Dutch words (*Soumission* has 16, no other book more than 2), and the share of accented letters (*Soumission* 2.6%, every other book below 0.4%). Both point only to *Soumission*.

| Decision | Reason |
|----------|--------|
| Keep *Soumission* instead of dropping it | It is only 1 book, and the dataset is already small. Its cover is a normal image, so it is still useful for the image features. It is also an interesting test case: can the text model classify a French description at all? |
| Read the low-scoring books instead of trusting the threshold | The score alone can't separate the classes cleanly: short English descriptions also score low (0.069 and 0.087 vs 0.0 for the French one), so there is no clear gap. |

> **For the report:** a simple word-frequency heuristic plus manual reading was enough to check the language; mention that short texts make such a score unreliable, which is why the results were read and cross-checked.
>
> *Kindle Paperwhite User's Guide* has a description that is only its own title (4 words). Worth keeping in mind for the error analysis.

### Exploration: class balance

110 Nonfiction (63%) vs 65 Fiction (37%). A model that always predicts Nonfiction is right 63% of the time, so that is the baseline. Because of the imbalance, accuracy alone is misleading; report precision/recall/F1 per class and a confusion matrix, and use stratified cross-validation.

### Exploration: lengths

| Words | Fiction median (middle 50%) | Nonfiction median (middle 50%) | Overlap |
|---|---|---|---|
| Description | 173 (147–212) | 201.5 (145–255) | Large: the middle ranges almost coincide |
| Title | 4 (2–5) | 9 (5–13) | Almost none |

- Description length is a **weak** signal: Nonfiction is slightly longer on average, but the ranges overlap heavily. Nonfiction also has the extremes (4 words for *Kindle Paperwhite User's Guide*, up to 746 words), which explains its larger spread (std 107 vs 62).
- Title length is a **strong** signal: Nonfiction titles are about twice as long. The title patterns below explain why.
- **Report image:** the side-by-side box plots of description length and title length per class (matplotlib, made in `02_cleaning_eda.ipynb`) are chosen as one of the report's images. See [Report images](#report-images).

### Exploration: title patterns

Found by reading random samples of titles from each class (`groupby("category").sample(...)`), then counting with `str.contains`:

| Pattern | Fiction | Nonfiction | Explanation |
|---|---|---|---|
| **Colon** (`:`) | 1 of 65 (1.5%) | 78 of 110 (71%) | Nonfiction titles usually have a subtitle explaining the topic (*Black Flags: The Rise of ISIS*). The only Fiction one is *Hystopia: A Novel*, whose subtitle literally says it's fiction. |
| **Series marker** (`#` + digit, regex `r"#\d"`) | 17 of 65 (26%) | 4 of 110 (3.6%) | Novels often belong to a series, e.g. *The Bourne Identity (Jason Bourne #1)*. The 4 Nonfiction matches are real series too (e.g. *Night (The Night Trilogy #1)*). |

- Matching a plain `#` also caught hashtags (*#HigherSelfie: …*), so the pattern was narrowed to `#` followed by a digit.
- Together: 82 of 110 Nonfiction titles have a colon or a series marker, against 18 of 65 Fiction titles (mostly series markers). A simple rule "colon in title → Nonfiction, otherwise Fiction" alone would already classify 142 of 175 books correctly (81%), well above the 63% baseline.
- **Important for feature engineering:** TF-IDF's default tokenizer drops punctuation, so a text model on title + description would *not* see the colon or `#`. To use these signals, they need to be added as explicit features (e.g. `has_colon`, `has_series`, `title_words`).

> **For the report:** the title patterns are a strong, explainable finding from the exploration, and they came from simply reading the data. The 81% of the one-rule "colon" classifier is a nice second reference point next to the 63% baseline. Discuss whether this generalises: subtitles are common for nonfiction in general, but the series share depends on which books this site happens to include.

### Exploration: most frequent words (in progress)

- Counting words per class with `collections.Counter`: the top 10 of both classes is almost entirely stop words (*the, and, a, of, to, in, is*), so raw counts say little about the difference between the classes.
- Exception: **personal pronouns are much more frequent in Fiction**, per 1,000 words (Fiction 12,009 words in total, Nonfiction 23,705):

| Word | Fiction | Nonfiction |
|---|---|---|
| her | 14.7 | 5.1 |
| his | 9.3 | 5.3 |
| she | 7.6 | 3.2 |
| he | 5.2 | 3.3 |

  Fiction descriptions tell the story of characters ("*she* discovers…", "*his* past…"), while Nonfiction descriptions talk about a topic.
- **Important for feature engineering:** these pronouns are on standard stop-word lists (including scikit-learn's English list), so "TF-IDF with stop-word removal" would throw this signal away. That makes the with/without stop words comparison in Step 3 more interesting, and is a reason to consider a custom stop-word list.
- Compare classes with **relative frequencies** (per 1,000 words), not raw counts: Nonfiction has about twice as many words in total, so its raw counts are higher for almost every word.
- **Words that differ most between the classes** (difference in frequency per 1,000 words, after removing 17 basic stop words; words seen fewer than 10 times ignored), shown as a diverging bar chart in `02_cleaning_eda.ipynb`:
  - More frequent in **Fiction**: *her* (+13.1), *she* (+6.0), *his* (+5.5), *novel* (+4.1), *family* (+3.0), *love* (+2.8), *he* (+2.6), *secrets* (+1.9). Characters, relationships and the word "novel" itself.
  - More frequent in **Nonfiction**: *our* (−5.9), *we* (−4.8), *us* (−2.9), *book* (−2.9), *your* (−2.7), *i* (−2.2), *you* (−2.2), *how* (−2.3). First and second person: the author speaking ("*I*", "*we*") and addressing the reader ("*you*", "*how* to…"), typical of memoirs and self-help.
  - Grammatical words that are common in both classes ended up near 0, which confirms they are filler.
- Descriptions use both straight (`'`, 230×) and curly (`’`, 318×) apostrophes. A word regex must accept both, otherwise *Jane’s* splits into *jane* and *s*.

### Image integrity check

All **175 of 175** cover images open without errors (checked 2026-10-20 with Pillow).

| Decision | Reason |
|----------|--------|
| Check with `img.load()` inside `try`/`except`, not `img.verify()` | `verify()` always returns `None` and only raises an error on some problems. In a test, it did not notice a JPEG cut off halfway (like an interrupted download), while `load()` reads the whole image and caught it. |

> **For the report:** the teaser is a good data-quality example. It was only found by reading the raw data, and a naive fix (40-character match) silently missed 3 cases. Explain the 20-character choice with the tested range, and the two independent checks (the text matches *and* it is at the expected position).

---

## Report images

The report may contain **at most 2 images**. Tables don't count.

| # | Image | Source | Status | Why |
|---|---|---|---|---|
| 1 | Box plots: description length and title length per class, side by side | `notebooks/02_cleaning_eda.ipynb` (matplotlib) | Chosen (2026-10-20). Not yet saved to a file. | Shows at a glance that title length separates Fiction and Nonfiction (medians 4 vs 9 words, boxes barely overlap) while description length doesn't (boxes almost coincide). |
| 2 | Open | | | PLAN.md suggests either the model comparison chart (F1 per feature set) or the confusion matrix of the best model. |

Choosing the box plots uses one of the two slots, so the "example covers per class" image suggested in PLAN.md no longer fits. Covers can still be described in words or in a table (e.g. average brightness per class).

> To use the plot in the report, save it as a file from the notebook, e.g. `plt.savefig("../report/figures/length_boxplots.png", dpi=200, bbox_inches="tight")` (before `plt.show()`).

---

## 3. Feature engineering

*Status: not started*

---

## 4. Model training

*Status: not started*

---

## 5. Evaluation

*Status: not started*
