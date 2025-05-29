from __future__ import annotations

from pathlib import Path
from typing import Any

from .issn import ISSN_MAP
from .ncbi import NCBI
from .runner import Converter


class HTMLConverter(Converter):

    def __init__(
        self,
        papers_csv: str | Path,
        data_dir: str | Path,
        outdir: str | Path,
        small: int = 0,
        **kwargs: Any,
    ):
        super().__init__(papers_csv, data_dir, **kwargs)
        self.od = Path(outdir)
        self.small = small

    def start(self):
        self.od.mkdir(parents=True, exist_ok=True)

    def work(self, paper, path, ff, progress=None):
        if ff == "html" and paper.issn not in ISSN_MAP:
            return
        if ff in {"ncbi", "html"}:

            ncbi = NCBI.from_file(path)
            css = ISSN_MAP[paper.issn] if ff == "html" else None  # type: ignore
            a = ncbi.article(css=css)
            a = a.strip()
            if a:
                out = self.od / f"{paper.pmid}.md"
                with out.open("wt", encoding="utf8") as fp:
                    fp.write(a)

            # print(paper.pmid, a)
            if progress and len(a) < self.small:
                progress.write(f"{paper.pmid} is small [{len(a)}]")
