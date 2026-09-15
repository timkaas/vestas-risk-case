"""
Parser module for extracting structured sections from corporate PDF reports.
"""

from src.risk_pipeline.parser import (
    PDFReportParser,
    ReportParser,
    format_pages,
    format_sections,
    parse_page_ranges,
)
from src.risk_pipeline.models import (
    ParsedPage,
    ParsedSection,
    SectionSpec,
)

__all__ = [
    "ReportParser",
    "PDFReportParser",
    "parse_page_ranges",
    "format_pages",
    "format_sections",
    "ParsedPage",
    "ParsedSection",
    "SectionSpec",
]
