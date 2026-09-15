"""
Risk Extraction Pipeline Package.
"""

from src.risk_pipeline.config import (
    DEFAULT_GOLDEN_SET_PATH,
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_MODEL_NAME,
    DEFAULT_PDF_PATH,
    DEFAULT_SECTIONS_OF_INTEREST,
    DEFAULT_TEMPERATURE,
)
from src.risk_pipeline.extractor import (
    EXTRACTION_PROMPT,
    RiskExtractor,
    build_extraction_chain,
)
from src.risk_pipeline.models import (
    Evidence,
    ExtractionResult,
    ParsedPage,
    ParsedSection,
    Risk,
    RiskCategory,
    SectionSpec,
)
from src.risk_pipeline.parser import (
    PDFReportParser,
    ReportParser,
    format_pages,
    format_sections,
    parse_page_ranges,
)
from src.risk_pipeline.pipeline import RiskExtractionPipeline

__all__ = [
    "RiskCategory",
    "Evidence",
    "Risk",
    "ExtractionResult",
    "SectionSpec",
    "ParsedPage",
    "ParsedSection",
    "ReportParser",
    "PDFReportParser",
    "parse_page_ranges",
    "format_pages",
    "format_sections",
    "RiskExtractor",
    "build_extraction_chain",
    "EXTRACTION_PROMPT",
    "RiskExtractionPipeline",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_CONCURRENCY",
    "DEFAULT_PDF_PATH",
    "DEFAULT_SECTIONS_OF_INTEREST",
    "DEFAULT_GOLDEN_SET_PATH",
]
