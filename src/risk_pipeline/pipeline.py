"""
End-to-end Risk Intelligence Extraction Pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from src.risk_pipeline.config import (
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_MODEL_NAME,
    DEFAULT_PDF_PATH,
    DEFAULT_SECTIONS_OF_INTEREST,
    DEFAULT_TEMPERATURE,
)
from src.risk_pipeline.extractor import RiskExtractor
from src.risk_pipeline.models import (
    ExtractionResult,
    ParsedSection,
    Risk,
    SectionSpec,
)
from src.risk_pipeline.parser import ReportParser

logger = logging.getLogger(__name__)


class RiskExtractionPipeline:
    """
    Production-grade end-to-end orchestrator for extracting structured corporate risks
    from annual report PDFs using modular parsing, LLM-based extraction, and aggregation.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        temperature: float = DEFAULT_TEMPERATURE,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        api_key: Optional[str] = None,
        default_sections: Optional[Sequence[SectionSpec]] = None,
        parser: Optional[ReportParser] = None,
        extractor: Optional[RiskExtractor] = None,
    ):
        """
        Initialize the Risk Extraction Pipeline.

        Args:
            model_name: LLM model identifier (e.g. 'gpt-4o').
            temperature: LLM sampling temperature.
            max_concurrency: Max parallel LLM extraction calls.
            api_key: Optional OpenAI API key override.
            default_sections: Default report sections and page ranges to extract.
            parser: Optional custom ReportParser instance.
            extractor: Optional custom RiskExtractor instance.
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_concurrency = max_concurrency
        self.default_sections = list(default_sections) if default_sections is not None else DEFAULT_SECTIONS_OF_INTEREST

        self.parser = parser or ReportParser(default_sections=self.default_sections)
        self.extractor = extractor or RiskExtractor(
            model_name=model_name,
            temperature=temperature,
            api_key=api_key,
            max_concurrency=max_concurrency,
        )

    @staticmethod
    def _aggregate_and_deduplicate(section_results: Sequence[ExtractionResult]) -> ExtractionResult:
        """
        Flatten and deduplicate extracted risks across sections.
        """
        combined_risks: List[Risk] = []
        seen_keys = set()

        for res in section_results:
            for r in res.risks:
                # Key by title normalized + section
                key = (r.title.strip().lower(), r.section.strip().lower())
                if key not in seen_keys:
                    seen_keys.add(key)
                    combined_risks.append(r)
                else:
                    logger.debug(f"Skipping duplicate risk: '{r.title}' in section '{r.section}'")

        return ExtractionResult(risks=combined_risks)

    def run(
        self,
        pdf_path: Union[str, Path] = DEFAULT_PDF_PATH,
        sections: Optional[Sequence[SectionSpec]] = None,
        show_progress: bool = False,
    ) -> ExtractionResult:
        """
        Execute the full extraction pipeline synchronously on a PDF report.

        Args:
            pdf_path: Path to the report PDF.
            sections: Optional custom section specifications.
            show_progress: Whether to show parsing progress bar.

        Returns:
            Aggregated ExtractionResult containing all identified risks.
        """
        pdf_file = Path(pdf_path)
        logger.info(f"Starting risk extraction pipeline for: {pdf_file}")

        # 1. Parse target sections from PDF
        parsed_sections = self.parser.parse_pdf_sections(
            pdf_path=pdf_file,
            sections=sections or self.default_sections,
            show_progress=show_progress,
        )
        logger.info(f"Parsed {len(parsed_sections)} sections from report")

        # 2. Extract risks via batch LLM chain
        section_results = self.extractor.extract_batch(
            sections=parsed_sections,
            max_concurrency=self.max_concurrency,
        )

        # 3. Aggregate and deduplicate
        aggregated = self._aggregate_and_deduplicate(section_results)
        logger.info(f"Successfully extracted {len(aggregated)} total corporate risks")

        return aggregated

    async def arun(
        self,
        pdf_path: Union[str, Path] = DEFAULT_PDF_PATH,
        sections: Optional[Sequence[SectionSpec]] = None,
        show_progress: bool = False,
    ) -> ExtractionResult:
        """
        Execute the full extraction pipeline asynchronously.

        Args:
            pdf_path: Path to the report PDF.
            sections: Optional custom section specifications.
            show_progress: Whether to show parsing progress bar.

        Returns:
            Aggregated ExtractionResult containing all identified risks.
        """
        pdf_file = Path(pdf_path)
        logger.info(f"Starting async risk extraction pipeline for: {pdf_file}")

        # 1. Parse target sections
        parsed_sections = self.parser.parse_pdf_sections(
            pdf_path=pdf_file,
            sections=sections or self.default_sections,
            show_progress=show_progress,
        )

        # 2. Async batch extraction
        section_results = await self.extractor.aextract_batch(
            sections=parsed_sections,
            max_concurrency=self.max_concurrency,
        )

        # 3. Aggregate and deduplicate
        aggregated = self._aggregate_and_deduplicate(section_results)
        logger.info(f"Async extraction completed with {len(aggregated)} total corporate risks")

        return aggregated

    def run_from_sections(self, parsed_sections: Sequence[ParsedSection]) -> ExtractionResult:
        """
        Extract risks directly from pre-parsed sections.

        Args:
            parsed_sections: Sequence of ParsedSection instances.

        Returns:
            Aggregated ExtractionResult.
        """
        section_results = self.extractor.extract_batch(
            sections=parsed_sections,
            max_concurrency=self.max_concurrency,
        )
        return self._aggregate_and_deduplicate(section_results)
