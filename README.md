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
