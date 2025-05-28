# Journal Scraper

Scraping journal websites for papers using selenium. Installs a command `biolit`.
Use `biolit --help`.

The standard package is light weight (wthout selenium) so you can install it in other environments
if you just want to process previously downloded pages.


If you want to do the full page capture use `pip install journal-scraper[selenium]`


## Location

There is a database of `Location`s  based on journal ISSN numbers

```python
    @dataclass
    class Location:
        article_css: str
        remove_css: str = ""
        wait_css: str = ""
```

that indicate to selenium which part of the page is the "article", what part
of this article needs stripping (we strip references) and what to wait for to
ensure the pages is fully loaded. Usually this is the same as `article_css` but
sometimes there are better tests.


## Workflow

1. gather a list of pubmed IDs that you want and place them in a file one pubmed ID
  per line (say as `pubmed.csv`).
2. run `biolit fetch-metadata pubmed.csv --email=your.email@uni.org` to fetch paper metadata from NCBI.
3. run `biolit selenium journals-paper.csv` To download the HTML. A CSV of the current state of download
   will be written to `journals-paper.csv.done`. You can stop and restart at any time. Unless specified
   the html will be stored in `journals-cache/html/{pubmed_id}.html` (If succcesful!)
