from __future__ import annotations

import csv
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Iterator

from . import config as Config
from .types import Paper


def read_papers_csv(csvfile: str | Path) -> Iterator[Paper]:
    if not os.path.isfile(csvfile):
        raise ValueError(f'"{csvfile}" is not a file!')
    with open(csvfile, encoding="utf8") as fp:
        R = csv.reader(fp)
        r = next(R)  # skip header pylint: disable=stop-iteration-return
        if tuple(r) != ("pmid", "issn", "name", "year", "doi", "pmcid", "title"):
            raise ValueError(f'"{csvfile}" is not a papers file!')
        # print(header)
        for row in R:
            pmid, issn, journal, year, doi, pmcid, title = row
            if not issn or issn == "missing-issn":
                # click.secho("missing %s" % pmid, fg='yellow')
                continue
            yield Paper(
                doi=doi,
                pmid=pmid,
                year=int(year),
                issn=issn,
                journal=journal or None,
                pmcid=pmcid or None,
                title=title or None,
            )


def read_pubmed_csv(
    csvfile: str | Path,
    pcol: int = 0,
) -> Iterator[str]:
    """File csvfile is a list of *all* pubmed IDs."""
    with open(csvfile, encoding="utf8") as fp:
        R = csv.reader(fp)
        for row in R:
            ret = row[pcol]
            if not ret.isdigit():
                continue
            yield ret


@dataclass(kw_only=True)
class UserConfig:
    papers_csv: str
    data_dir: str
    email: str | None = None
    api_key: str | None = None


_CONF: UserConfig | None = None


def getconfig() -> UserConfig:

    global _CONF
    if _CONF is not None:
        return _CONF
    default = dict(
        papers_csv=Config.JCSV,
        data_dir=Config.DATADIR,
    )
    if not os.path.exists(Config.CONFIG_FILE):
        _CONF = UserConfig(**default)
    else:
        with open(Config.CONFIG_FILE, "rb") as fp:
            _CONF = UserConfig(**{**default, **tomllib.load(fp)})
    return _CONF


def data_dir() -> str:
    return getconfig().data_dir


def has_package(package: str) -> bool:
    return get_package(package) is not None


def get_package(package: str) -> ModuleType | None:
    import importlib

    try:
        return importlib.import_module(package)

    except ModuleNotFoundError:
        return None


def check_imports(*imports: str, exit: bool = True) -> bool:
    import sys
    import click

    missing = set()
    for i in imports:
        if not has_package(i):
            missing.add(i)
    if missing:

        m = " ".join(missing)
        if "undetected_chromedriver" in missing:
            m = "setuptools " + m
        click.secho(
            f"Missing packages! Please `pip install {m}`",
            fg="yellow",
            bold=True,
            err=True,
        )
        if exit:
            sys.exit(1)
        return False
    return True
