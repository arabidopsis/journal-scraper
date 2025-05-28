from __future__ import annotations

import csv
import time
from abc import ABC
from abc import abstractmethod
from itertools import batched
from pathlib import Path
from typing import Any
from typing import cast
from typing import Iterator
from typing import TYPE_CHECKING

from .cache import Cache
from .cache import FFSTR
from .cache import FileFormat
from .issn import ISSN_MAP
from .utils import read_papers_csv

if TYPE_CHECKING:
    from tqdm import tqdm
    from .types import Paper


class Runner(ABC):
    cache: Cache | None

    def __init__(
        self,
        papers_csv: str | Path,
        *,
        done_csv: str | Path | None = None,
        batch_size: int = 1,
        sleep: float = 0.0,
        data_dir: str | Path | None = None,
        **kwargs: Any,
    ):
        self.papers_csv = Path(papers_csv)
        if done_csv is None:
            done_csv = self.papers_csv.parent / (self.papers_csv.name + ".done")
        self.done_csv = Path(done_csv)
        self.batch_size = batch_size
        self.sleep = sleep
        # self.data_dir = data_dir
        if data_dir is not None:
            self.cache = Cache(data_dir)
        else:
            self.cache = None
        self.init(**kwargs)

    def init(self, **kwargs: Any) -> None:
        pass

    def start(self) -> None:
        pass

    def end(self) -> None:
        pass

    def get_done(self) -> set[str]:
        if self.done_csv.exists():
            with self.done_csv.open("r", encoding="utf8") as fp:
                R = csv.reader(fp)
                done = {row[0] for row in R}
        else:
            done = set()
        return done

    def ok(self, paper: Paper) -> bool:
        return bool(paper.doi and paper.issn and paper.issn in ISSN_MAP)

    def run(self, notebook: bool = False):

        if notebook:
            from tqdm.notebook import tqdm
        else:
            from tqdm import tqdm

        done = self.get_done()

        todo = [
            paper
            for paper in read_papers_csv(self.papers_csv)
            if paper.pmid not in done and self.ok(paper)
        ]
        self.start()
        try:
            with self.done_csv.open("a", encoding="utf8") as fp:
                W = csv.writer(fp)
                with tqdm(total=len(todo)) as pbar:
                    for papers in batched(todo, self.batch_size):
                        for paper, status in self.batch_worker(papers, pbar):
                            W.writerow([paper.pmid, status])
                            fp.flush()
                        pbar.update(len(papers))
                        if self.sleep:
                            time.sleep(self.sleep)
        finally:
            self.end()

    def batch_worker(
        self,
        batch: tuple[Paper, ...],
        progress: tqdm,
    ) -> Iterator[tuple[Paper, str]]:
        for paper in batch:
            yield paper, self.work(paper, progress)

    @abstractmethod
    def work(self, paper: Paper, progress: tqdm) -> str:
        raise NotImplementedError


class Converter(ABC):

    def __init__(
        self,
        papers_csv: str | Path,
        data_dir: str | Path,
        **kwargs: Any,
    ):
        self.papers_csv = Path(papers_csv)
        self.data_dir = Path(data_dir)
        self._db: dict[str, Paper] | None = None
        self.init(**kwargs)

    def init(self, **kwargs: Any) -> None:
        pass

    def start(self) -> None:
        pass

    def end(self) -> None:
        pass

    @property
    def db(self) -> dict[str, Paper]:
        if self._db is not None:
            return self._db
        self._db = {paper.pmid: paper for paper in read_papers_csv(self.papers_csv)}
        return self._db

    def ok(self, pmid: str) -> bool:
        return pmid in self.db

    def walk(self) -> Iterator[tuple[Path, str, FileFormat]]:
        import os

        for root, dirs, files in os.walk(self.data_dir):
            for d in dirs:
                if d not in FFSTR:
                    dirs.remove(d)

            ff = os.path.basename(root)
            if ff not in FFSTR:
                continue
            for f in files:
                if not f.endswith((".xml", ".html")):
                    continue
                pmid, _ = os.path.splitext(f)
                if not self.ok(pmid):
                    continue

                yield Path(os.path.join(root, f)), pmid, cast(FileFormat, ff)

    def run(self):

        self.start()
        try:
            for path, pmid, ff in self.walk():
                paper = self.db[pmid]
                self.work(paper, Path(path), ff, None)

        finally:
            self.end()

    def trun(self, notebook: bool = False):
        if notebook:
            from tqdm.notebook import tqdm
        else:
            from tqdm import tqdm

        self.start()
        try:
            with tqdm(list(self.walk())) as pbar:
                for path, pmid, ff in pbar:
                    paper = self.db[pmid]
                    pbar.set_description(pmid)
                    self.work(paper, Path(path), ff, pbar)

        finally:
            self.end()

    @abstractmethod
    def work(
        self,
        paper: Paper,
        path: Path,
        ff: FileFormat,
        tqdm: tqdm | None = None,
    ) -> None:
        raise NotImplementedError
