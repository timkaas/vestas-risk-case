"""
Configuration defaults and constants for the Risk Pipeline.
"""

from pathlib import Path
from typing import List
from src.risk_pipeline.models import SectionSpec

# Default paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PDF_PATH = PROJECT_ROOT / "data" / "VestasAnnualReport2025.pdf"
DEFAULT_MARKDOWN_PATH = PROJECT_ROOT / "data" / "VestasAnnualReport2025.md"
DEFAULT_GOLDEN_SET_PATH = PROJECT_ROOT / "src" / "eval" / "golden-llm.jsonl"

# Default LLM settings
DEFAULT_MODEL_NAME = "gpt-4o"
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_CONCURRENCY = 4
DEFAULT_REQUEST_TIMEOUT = 120

# Default sections of interest from Vestas Annual Report (0-based page indices in PDF)
DEFAULT_SECTIONS_OF_INTEREST: List[SectionSpec] = [
    SectionSpec(
        name="Risk Management",
        page_range=range(49, 51),  # Pages 50-51
        description="Enterprise risk governance, geopolitical tensions, execution, and critical asset cyber exposure."
    ),
    SectionSpec(
        name="Material Risk",
        page_range=range(70, 74),  # Pages 71-74
        description="CSRD / ESG double materiality assessment: climate mitigation, circularity, workforce safety, supply chain labour, community impact, bribery."
    ),
    SectionSpec(
        name="Climate Change",
        page_range=range(84, 92),  # Pages 85-92
        description="E1 Climate Change detailed disclosures: GHG emissions, energy consumption, carbon taxes/tariffs, physical risks, transition plans."
    ),
    SectionSpec(
        name="Cyber Security",
        page_range=range(117, 118),  # Page 118
        description="G1 Governance cyber security reporting, grid disruption risks, IT/OT defense and cyber risk management strategy."
    ),
]
