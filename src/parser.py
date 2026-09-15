"""
Parser module for extracting structured sections from corporate PDF reports.
"""

from src.risk_pipeline.parser import (
    PDFReportParser,
    ReportParser,
    format_pages,
    format_sections,
)
from src.risk_pipeline.models import (
    ParsedPage,
    ParsedSection,
    SectionSpec,
)

__all__ = [
    "ReportParser",
    "PDFReportParser",
    "format_pages",
    "format_sections",
    "ParsedPage",
    "ParsedSection",
    "SectionSpec",
]
