"""
Risk Extraction Pipeline Package.
"""

from src.config import (
    DEFAULT_GOLDEN_SET_PATH,
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_MODEL_NAME,
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
    ReportDefinition,
    SectionSpec,
)
from src.risk_pipeline.parser import (
    PDFReportParser,
    ReportParser,
    format_pages,
    format_sections,
    parse_page_ranges,
    parse_report_definition,
)
from src.risk_pipeline.pipeline import RiskExtractionPipeline

__all__ = [
    "RiskCategory",
    "Evidence",
    "Risk",
    "ExtractionResult",
    "SectionSpec",
    "ReportDefinition",
    "ParsedPage",
    "ParsedSection",
    "ReportParser",
    "PDFReportParser",
    "parse_page_ranges",
    "parse_report_definition",
    "format_pages",
    "format_sections",
    "RiskExtractor",
    "build_extraction_chain",
    "EXTRACTION_PROMPT",
    "RiskExtractionPipeline",
    "DEFAULT_MODEL_NAME",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_CONCURRENCY",
    "DEFAULT_GOLDEN_SET_PATH",
]
