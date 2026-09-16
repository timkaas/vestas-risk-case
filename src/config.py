"""
Configuration defaults and constants for the Risk Pipeline.
"""

from pathlib import Path

# Default paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_PATH = PROJECT_ROOT / "eval"
DEFAULT_PDF_PATH = PROJECT_ROOT / "data" / "VestasAnnualReport2025.pdf"
DEFAULT_SECTIONS_DEF_PATH = PROJECT_ROOT / "data" / "vestas-report.json"
DEFAULT_GOLDEN_SET_PATH = PROJECT_ROOT / "eval" / "ground-truth.json"

# Default LLM settings
DEFAULT_MODEL_NAME = "gpt-4o"
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_CONCURRENCY = 4
DEFAULT_REQUEST_TIMEOUT = 120
