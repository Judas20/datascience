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
- **168 of 175 descriptions contain their opening text twice.** The site puts a short teaser (the first ~375 characters, cut off mid-word) in front of the full description. So each description is *teaser + full text + "...more"*. The 7 without a teaser are short descriptions where the teaser would be the whole text. This inflates word counts and counts the first ~60 words of each description twice, so it has to be removed when cleaning.
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

*Status: not started*

---

## 3. Feature engineering

*Status: not started*

---

## 4. Model training

*Status: not started*

---

## 5. Evaluation

*Status: not started*
