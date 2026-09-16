"""Load report JSON and extract its configured PDF pages."""
import itertools
import json
from pathlib import Path
from typing import Dict, List, Sequence, Union

import pymupdf
import pymupdf4llm

from src.risk_pipeline.models import ReportDefinition, SectionSpec, ParsedPage, ParsedSection


def _page_range(value: str) -> range:
    """Turn ``'50-51'`` (or ``'118'``) into zero-based PDF page indices."""
    try:
        start, _, end = value.replace("..", "-").replace(":", "-").partition("-")
        first = int(start)
        last = int(end or start)
    except ValueError as exc:
        raise ValueError(f"Invalid page range: {value!r}") from exc
    if first < 1 or last < first:
        raise ValueError(f"Invalid page range: {value!r}")
    return range(first - 1, last)


def parse_report_definition(path: Path) -> ReportDefinition:
    """Parse the small ``report`` / ``sections`` JSON definition file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    report_path = Path(data["report"])
    if not report_path.is_absolute():
        report_path = path.parent / report_path
    sections = [
        SectionSpec(section["name"], _page_range(str(section["pages"])))
        for section in data["sections"]
    ]
    return ReportDefinition(report_path, sections, path)


def parse_page_ranges(values: Union[str, Sequence[Union[str, int]]]) -> List[SectionSpec]:
    """Support the existing ``--sections`` CLI shorthand."""
    values = [values] if isinstance(values, str) else values
    ranges = [item for value in values for item in str(value).replace(",", " ").split()]
    return [
        SectionSpec(
            f"Page {item}" if "-" not in item and ":" not in item and ".." not in item else f"Pages {item}",
            _page_range(item),
        )
        for item in ranges
    ]


def format_pages(pages: Sequence[ParsedPage]) -> str:
    return "\n\n".join(f"=== PDF PAGE {page.page_number} ===\n\n{page.text.strip()}" for page in pages)


def format_sections(sections: Sequence[ParsedSection]) -> str:
    return "\n\n".join(f"# {section.name}\n\n{section.formatted_content()}" for section in sections)

class ReportParser:
    def __init__(self, split=False):
        self.split = split

    def parse_pdf_sections(
        self,
        pdf_path: Union[str, Path],
        sections: Sequence[SectionSpec],
        show_progress: bool = False,
    ) -> List[ParsedSection]:
        assert not self.split

        sections = list(sections)

        with pymupdf.open(pdf_path) as pdf:
            pages = [page for section in sections for page in section.page_range]
            if not pages:
                return []
            md = pymupdf4llm.to_markdown(pdf, pages=pages, header=False, footer=False, page_chunks=True,
                                         show_progress=show_progress)

        # Reconstruct sections
        it = iter(md)
        return [
            ParsedSection(name=section.name, pages=[
                ParsedPage(page_number=chunk['metadata']['page_number'], text=chunk["text"], metadata=chunk.get("metadata", {}))
                for chunk in list(itertools.islice(it, len(section.page_range)))
            ], page_numbers=[p + 1 for p in section.page_range])
            for section in sections
        ]

    def load_page_text_map(self, pdf_path: Path, sections: Sequence[SectionSpec]) -> Dict[int, str]:
        return {
            page.page_number: page.text
            for section in self.parse_pdf_sections(pdf_path, sections)
            for page in section.pages
        }


PDFReportParser = ReportParser
parse_from_json = parse_report_definition
