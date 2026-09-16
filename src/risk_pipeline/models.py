"""
Data models for the Risk Intelligence Extraction Pipeline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union
from pydantic import BaseModel, Field, field_validator


class RiskCategory(str, Enum):
    """Standardized risk categories for corporate risk intelligence."""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    REGULATORY = "regulatory"
    MARKET = "market"
    CLIMATE = "climate"
    CYBER = "cyber"
    SUPPLY_CHAIN = "supply_chain"
    GEOPOLITICAL = "geopolitical"
    OTHER = "other"

    @classmethod
    def _missing_(cls, value: object) -> Optional["RiskCategory"]:
        if isinstance(value, str):
            val_clean = value.strip().lower().replace("-", "_").replace(" ", "_")
            for member in cls:
                if member.value == val_clean:
                    return member
                # Handle common aliases
                if val_clean in ("supplychain", "supply_chain_disruption"):
                    return cls.SUPPLY_CHAIN
                if val_clean in ("geo_political", "geopolitics"):
                    return cls.GEOPOLITICAL
                if val_clean in ("cybersecurity", "cyber_security", "it_security"):
                    return cls.CYBER
                if val_clean in ("environmental", "climate_change", "esg"):
                    return cls.CLIMATE
        return cls.OTHER


class Evidence(BaseModel):
    """Evidence quote supporting the identified risk."""
    page: int = Field(description="1-based page number in the report where evidence is found")
    quote: str = Field(description="Direct verbatim quote from the report supporting the risk")


class Risk(BaseModel):
    """Structured corporate risk entry extracted from report."""
    title: str = Field(description="Short, descriptive title of the risk")
    description: str = Field(description="2-3 sentence description summarizing the risk context, drivers, and potential impact")
    category: RiskCategory = Field(description="Categorization of the risk according to standard taxonomies")
    section: str = Field(description="Report section name where found (e.g. 'Risk Management', 'Climate Change')")
    pages: List[int] = Field(description="1-based page numbers where this risk is discussed")
    mitigation: Optional[str] = Field(None, description="Stated corporate mitigation actions, controls, or transition plans, if any")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidence quotes and citations supporting the risk")

    @field_validator("mitigation", mode="before")
    @classmethod
    def clean_mitigation(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            v_strip = v.strip()
            if v_strip.lower() in ("none", "n/a", "null", "not stated", "no mitigation mentioned", ""):
                return None
            return v_strip
        return str(v)


class ExtractionResult(BaseModel):
    """Aggregated extraction result containing a list of identified corporate risks."""
    risks: List[Risk] = Field(default_factory=list, description="List of extracted corporate risks")

    def __len__(self) -> int:
        return len(self.risks)

    def __iter__(self) -> Iterable[Risk]:  # type: ignore[override]
        return iter(self.risks)

    def __getitem__(self, index: int) -> Risk:
        return self.risks[index]

    def to_dict(self) -> Dict[str, Any]:
        """Convert extraction result to a standard serializable dictionary."""
        return self.model_dump(mode="json")

    def to_json(self, indent: int = 2) -> str:
        """Serialize an extraction result to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save_json(self, file_path: Union[str, Path], indent: int = 2) -> Path:
        """Save extraction result to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(indent=indent), encoding="utf-8")
        return path


    @classmethod
    def from_file(cls, file_path: Path) -> ExtractionResult:
        """Load ExtractionResult from a JSON file."""
        content = file_path.read_text(encoding="utf-8").strip()
        data = json.loads(content)
        if isinstance(data, dict):
            return cls.model_validate(data)
        else:
            # Assumed a list of risks
            return cls(risks=[Risk.model_validate(item) for item in data])

    def _repr_markdown_(self) -> str:
        """Rich Jupyter notebook / markdown representation."""
        md_output = [f"### 📋 Extracted Risks ({len(self.risks)})\n"]
        for i, r in enumerate(self.risks, 1):
            pages_str = ", ".join(map(str, r.pages)) if r.pages else "N/A"
            category_val = r.category.value if hasattr(r.category, "value") else str(r.category)
            mitigation_block = f">\n> 🛡️ **Mitigation:** {r.mitigation}" if r.mitigation else ""
            evidence_lines = "\n".join(f'  - Page {e.page}: "{e.quote}"' for e in r.evidence) if r.evidence else "  - *No evidence quotes provided*"
            md_output.append(
                f"#### {i}. {r.title}\n"
                f"- **Category:** `{category_val.upper()}`\n"
                f"- **Section:** *{r.section}* (pp. {pages_str})\n"
                f"- **Description:** {r.description}\n"
                f"- **Evidence:**\n"
                f"{evidence_lines}"
                f"{mitigation_block}"
            )
        return "\n\n---\n\n".join(md_output)

@dataclass(frozen=True)
class SectionSpec:
    """Specification of a document section to extract."""
    name: str
    page_range: range
    description: Optional[str] = None

    @property
    def pages(self) -> List[int]:
        return list(self.page_range)


@dataclass(frozen=True)
class ReportDefinition:
    """Typed representation of a report-definition JSON input file."""
    report_path: Path
    sections: List[SectionSpec]
    source_path: Optional[Path] = None

@dataclass(frozen=True)
class ParsedPage:
    """Parsed single page content and metadata."""
    page_number: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ParsedSection:
    """Structured representation of a parsed section containing one or more pages."""
    name: str
    page_numbers: Sequence[int]
    pages: List[ParsedPage]

    @property
    def formatted_content(self) -> str:
        return "\n\n".join(f"=== PDF PAGE {page.page_number} ===\n\n{page.text.strip()}" for page in self.pages)
