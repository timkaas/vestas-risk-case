"""
Risk Extractor and LLM extraction chain for structured risk intelligence extraction.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI

from src.config import (
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_MODEL_NAME,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_TEMPERATURE,
)
from src.risk_pipeline.models import ExtractionResult, ParsedSection

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert corporate risk intelligence analyst. Extract all principal corporate risks, material ESG risks, operational, financial, cyber, supply chain, geopolitical, regulatory, and climate risks from the provided annual report text with high precision.

Follow these strict extraction guidelines:
1. Identify all distinct corporate and ESG risks mentioned in the text.
2. For each risk, extract:
   - title: Short, professional title of the risk.
   - description: 2-3 sentences explaining the risk context, drivers, and potential impact.
   - category: Select the most accurate category from: financial, operational, regulatory, market, climate, cyber, supply_chain, geopolitical, other.
   - section: The provided report section name.
   - pages: The 1-based page numbers where this risk is discussed.
   - mitigation: Direct corporate mitigations, controls, or transition plans if explicitly mentioned in the text; otherwise null.
   - evidence: Verbatim quotes from the text supporting the risk and their exact 1-based page number.
"""

HUMAN_PROMPT = """Section: {section_name}
Pages: {page_numbers}

Content:
{content}"""

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", HUMAN_PROMPT),
])


def build_extraction_chain(
    model_name: str = DEFAULT_MODEL_NAME,
    temperature: float = DEFAULT_TEMPERATURE,
    timeout: int = DEFAULT_REQUEST_TIMEOUT,
) -> Runnable:
    """
    Construct a LangChain structured extraction runnable for ExtractionResult.

    Args:
        model_name: OpenAI model identifier (e.g. 'gpt-4o', 'gpt-4o-mini').
        temperature: Sampling temperature (0.0 for deterministic extraction).
        timeout: Request timeout in seconds.

    Returns:
        Configured LangChain Runnable pipeline returning ExtractionResult instances.
    """
    prompt = EXTRACTION_PROMPT
    llm_kwargs: Dict[str, Any] = {
        "model": model_name,
        "temperature": temperature,
        "timeout": timeout,
    }

    llm = ChatOpenAI(**llm_kwargs)
    structured_llm = llm.with_structured_output(ExtractionResult)
    return prompt | structured_llm


class RiskExtractor:
    """
    Coordinates LLM-based structured risk extraction across parsed report sections.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        temperature: float = DEFAULT_TEMPERATURE,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    ):
        """
        Initialize RiskExtractor.

        Args:
            model_name: LLM model name to invoke.
            temperature: LLM sampling temperature.
            max_concurrency: Maximum number of concurrent LLM API calls.
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_concurrency = max_concurrency
        self.chain = build_extraction_chain(
            model_name=model_name,
            temperature=temperature,
        )

    @staticmethod
    def _prepare_section_payload(section: ParsedSection) -> Dict[str, Any]:
        """Convert ParsedSection into extraction prompt template inputs."""
        return {
            "section_name": section.name,
            "page_numbers": list(section.page_numbers),
            "content": section.formatted_content,
        }

    def extract_batch(
        self,
        sections: Sequence[ParsedSection],
        max_concurrency: Optional[int] = None,
    ) -> List[ExtractionResult]:
        """
        Extract risks from multiple sections in parallel batches.

        Args:
            sections: Sequence of ParsedSections to extract.
            max_concurrency: Maximum parallel requests (defaults to self.max_concurrency).

        Returns:
            List of ExtractionResult objects corresponding to each input section.
        """
        concurrency = max_concurrency or self.max_concurrency
        batch_inputs = [self._prepare_section_payload(sec) for sec in sections]
        logger.info(f"Running batch extraction for {len(batch_inputs)} sections (concurrency: {concurrency})")

        raw_results = self.chain.batch(
            batch_inputs,
            config=RunnableConfig(max_concurrency=concurrency),
        )

        return raw_results
        #risks = [rr.model_dump() for r in raw_results for rr in r.risks]
        #return ExtractionResult(risks=risks)

        results: List[ExtractionResult] = []
        for r in raw_results:
            if isinstance(r, ExtractionResult):
                results.append(r)
            else:
                results.append(ExtractionResult.model_validate(r))
        return results
