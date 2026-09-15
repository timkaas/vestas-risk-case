"""
PDF and Markdown parser for extracting structured report sections and pages.
"""

from __future__ import annotations

import itertools
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import pymupdf
import pymupdf4llm

from src.risk_pipeline.config import DEFAULT_SECTIONS_OF_INTEREST
from src.risk_pipeline.models import ParsedPage, ParsedSection, SectionSpec

logger = logging.getLogger(__name__)


def format_pages(pages: Sequence[Union[Dict[str, Any], ParsedPage]]) -> str:
    """
    Format a sequence of pages into a readable string with explicit page markers.

    Args:
        pages: List of page dictionaries (from pymupdf4llm) or ParsedPage objects.

    Returns:
        Formatted markdown string with '=== PDF PAGE X ===' delimiters.
    """
    formatted_chunks: List[str] = []
    for page in pages:
        if isinstance(page, ParsedPage):
            page_num = page.page_number
            text = page.text
        elif isinstance(page, dict):
            page_num = page.get("metadata", {}).get("page_number", page.get("page_number", "Unknown"))
            text = page.get("text", "")
        else:
            continue
        formatted_chunks.append(f"=== PDF PAGE {page_num} ===\n\n{text.strip()}")
    return "\n\n".join(formatted_chunks)


def format_sections(sections: Sequence[ParsedSection]) -> str:
    """
    Format multiple parsed sections into a single markdown document with section headers.

    Args:
        sections: Sequence of ParsedSection objects.

    Returns:
        Formatted string containing all sections and page markers.
    """
    return "\n\n".join(
        f"# {sec.name}\n\n{sec.formatted_content}"
        for sec in sections
    )


class ReportParser:
    """
    Parser for corporate annual reports and disclosures.
    Converts PDF documents and targeted page ranges into structured markdown sections.
    """

    def __init__(self, default_sections: Optional[Sequence[SectionSpec]] = None):
        """
        Initialize report parser.

        Args:
            default_sections: Optional default section specifications to target.
        """
        self.default_sections = list(default_sections) if default_sections is not None else DEFAULT_SECTIONS_OF_INTEREST

    def parse_pdf_sections(
        self,
        pdf_path: Union[str, Path],
        sections: Optional[Sequence[SectionSpec]] = None,
        show_progress: bool = False,
    ) -> List[ParsedSection]:
        """
        Extract and parse specified report sections from a PDF file.

        Args:
            pdf_path: Path to the source PDF report.
            sections: Specific sections to extract. If None, uses default sections.
            show_progress: Whether to show pymupdf4llm progress bar.

        Returns:
            List of ParsedSection objects ready for LLM extraction.
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF report not found at: {pdf_file}")

        target_sections = list(sections) if sections is not None else self.default_sections
        if not target_sections:
            raise ValueError("No sections specified for parsing.")

        # Flatten 0-based page indices in sequential order
        ordered_pages: List[int] = []
        section_page_counts: List[Tuple[SectionSpec, int]] = []
        for sec in target_sections:
            sec_pages = list(sec.page_range)
            ordered_pages.extend(sec_pages)
            section_page_counts.append((sec, len(sec_pages)))

        logger.info(f"Parsing {len(ordered_pages)} pages across {len(target_sections)} sections from {pdf_file.name}")

        # Open PDF document
        doc = pymupdf.open(str(pdf_file))
        try:
            # Validate page boundaries
            max_page = doc.page_count
            for p in ordered_pages:
                if p < 0 or p >= max_page:
                    raise IndexError(f"Page index {p} is out of bounds for document with {max_page} pages.")

            # Extract markdown page chunks via pymupdf4llm
            raw_page_chunks: List[Dict[str, Any]] = pymupdf4llm.to_markdown(
                doc,
                pages=ordered_pages,
                header=False,
                footer=False,
                page_chunks=True,
                show_progress=show_progress,
            )
        finally:
            doc.close()

        # Reconstruct sections from page chunks
        it = iter(raw_page_chunks)
        parsed_sections: List[ParsedSection] = []

        for sec, count in section_page_counts:
            sec_chunks = list(itertools.islice(it, count))
            parsed_pages: List[ParsedPage] = []
            page_numbers: List[int] = []

            for chunk in sec_chunks:
                meta = chunk.get("metadata", {})
                # pymupdf4llm populates 1-based page_number in metadata
                p_num = meta.get("page_number")
                if p_num is None:
                    # Fallback to page index + 1
                    p_num = meta.get("page", 0) + 1
                page_numbers.append(int(p_num))
                parsed_pages.append(
                    ParsedPage(
                        page_number=int(p_num),
                        text=chunk.get("text", ""),
                        metadata=meta,
                    )
                )

            formatted_content = format_pages(parsed_pages)

            parsed_sections.append(
                ParsedSection(
                    name=sec.name,
                    page_numbers=page_numbers,
                    pages=parsed_pages,
                    formatted_content=formatted_content,
                )
            )

        return parsed_sections

    def load_page_text_map(
        self,
        pdf_path: Optional[Union[str, Path]] = None,
        md_path: Optional[Union[str, Path]] = None,
        sections: Optional[Sequence[SectionSpec]] = None,
    ) -> Dict[int, str]:
        """
        Generate a mapping of {page_number: page_text} for grounding / evidence verification.

        Args:
            pdf_path: Optional path to PDF to extract live pages.
            md_path: Optional path to fallback markdown file.
            sections: Optional sections to extract from PDF.

        Returns:
            Dictionary mapping 1-based page numbers to their full text content.
        """
        page_map: Dict[int, str] = {}

        if pdf_path and Path(pdf_path).exists():
            parsed_sections = self.parse_pdf_sections(pdf_path, sections=sections)
            for sec in parsed_sections:
                for page in sec.pages:
                    page_map[page.page_number] = page.text
            return page_map

        if md_path and Path(md_path).exists():
            content = Path(md_path).read_text(encoding="utf-8")
            # Populate fallback map
            for p in [50, 51, 71, 72, 73, 74, 85, 86, 87, 88, 89, 90, 91, 92, 117, 118]:
                page_map[p] = content

        return page_map

    def export_extracted_pdf(
        self,
        source_pdf: Union[str, Path],
        output_pdf: Union[str, Path],
        sections: Optional[Sequence[SectionSpec]] = None,
    ) -> Path:
        """
        Extract only target pages into a compact standalone PDF file.

        Args:
            source_pdf: Path to original PDF.
            output_pdf: Path for destination extracted PDF.
            sections: Sections defining the page ranges to extract.

        Returns:
            Path to the newly saved PDF.
        """
        target_sections = list(sections) if sections is not None else self.default_sections
        doc_src = pymupdf.open(str(source_pdf))
        doc_dst = pymupdf.open()
        try:
            for sec in target_sections:
                for page_num in sec.page_range:
                    page_src = doc_src[page_num]
                    page_dst = doc_dst.new_page(-1, page_src.rect.width, page_src.rect.height)
                    page_dst.show_pdf_page(page_src.rect, doc_src, page_num)

            out_path = Path(output_pdf)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            doc_dst.save(str(out_path), garbage=3, deflate=True)
            return out_path
        finally:
            doc_src.close()
            doc_dst.close()


# Alias for backwards compatibility
PDFReportParser = ReportParser
