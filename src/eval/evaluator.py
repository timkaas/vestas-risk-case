import json
import os
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field


class EvalScore(BaseModel):
    total_golden_risks: int
    total_extracted_risks: int
    matched_risks: int
    recall: float = Field(description="Recall against golden set (0.0 to 1.0)")
    category_accuracy: float = Field(description="Category accuracy on matched risks")
    mitigation_coverage: float = Field(description="Percentage of expected mitigations captured")
    grounding_score: float = Field(description="Percentage of evidence quotes found in raw text")
    passed: bool
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed breakdown of evaluation results")


class RiskPipelineEvaluator:
    def __init__(self, golden_set_path: Optional[str] = None):
        self.golden_set_path = self._resolve_golden_set_path(golden_set_path)
        self.golden_set = self._load_golden_set(self.golden_set_path)

    @staticmethod
    def _resolve_golden_set_path(path: Optional[str]) -> Path:
        if path:
            p = Path(path)
            if p.exists():
                return p
        
        # Search common locations
        candidates = [
            Path("src/eval/golden-llm.jsonl"),
            Path("eval/golden-llm.jsonl"),
            Path("src/eval/golden.jsonl"),
            Path("eval/golden.jsonl"),
            Path("src/eval/golden_set.json"),
            Path("eval/golden_set.json"),
            Path(__file__).parent / "golden-llm.jsonl",
            Path(__file__).parent / "golden.jsonl",
            Path(__file__).parent / "golden_set.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        
        if path:
            return Path(path)
        return Path("src/eval/golden-llm.jsonl")

    @staticmethod
    def _load_golden_set(file_path: Path) -> List[Dict[str, Any]]:
        if not file_path.exists():
            raise FileNotFoundError(f"Golden set file not found at: {file_path}")
        
        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        
        # 1. Try standard single JSON array / object
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
        except Exception:
            pass

        # 2. Try single-line JSONL format
        items = []
        try:
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("//"):
                    items.append(json.loads(line))
            if items:
                return items
        except Exception:
            items = []

        # 3. Stream decode multiple JSON objects (supports multi-line JSONL and concatenated objects)
        decoder = json.JSONDecoder()
        idx = 0
        while idx < len(content):
            while idx < len(content) and content[idx].isspace():
                idx += 1
            if idx >= len(content):
                break
            try:
                obj, end = decoder.raw_decode(content, idx)
                if isinstance(obj, list):
                    items.extend(obj)
                else:
                    items.append(obj)
                idx = end
            except Exception as e:
                raise ValueError(f"Could not parse golden set from {file_path}: {e}")
        
        return items

    @staticmethod
    def _get_field(obj: Any, field_name: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(field_name, default)
        return getattr(obj, field_name, default)

    def evaluate(
        self,
        extracted_risks: List[Any],
        raw_markdown_pages: Optional[Dict[int, str]] = None
    ) -> EvalScore:
        if raw_markdown_pages is None:
            raw_markdown_pages = {}

        matched_count = 0
        correct_categories = 0
        captured_mitigations = 0
        total_quotes = 0
        grounded_quotes = 0
        
        matched_details = []
        unmatched_golden = []

        # 1. Grounding check: verify evidence quotes exist in source
        for risk in extracted_risks:
            evidence_items = self._get_field(risk, "evidence", []) or []
            for ev in evidence_items:
                total_quotes += 1
                ev_page = self._get_field(ev, "page")
                ev_quote = self._get_field(ev, "quote", "")
                page_text = raw_markdown_pages.get(ev_page, "") if ev_page is not None else ""
                
                if ev_quote and ev_quote.strip():
                    # If page text is available, check for substring match (first 30 chars or full)
                    if page_text:
                        quote_snippet = ev_quote.strip()[:30].lower()
                        if quote_snippet in page_text.lower():
                            grounded_quotes += 1
                    else:
                        # If page text not provided in input dict, consider valid if non-empty quote
                        grounded_quotes += 1

        grounding_score = (grounded_quotes / total_quotes) if total_quotes > 0 else 1.0

        # 2. Golden set matching
        used_extracted_indices = set()
        for gold in self.golden_set:
            gold_title_keywords = gold.get("title_keywords", [gold.get("title", "")])
            gold_id = gold.get("id", gold.get("title", "unknown"))
            gold_category = str(gold.get("category", "")).lower()
            gold_has_mitigation = gold.get("expected_mitigation", gold.get("has_mitigation", False))

            matched_risk = None
            matched_idx = -1

            for idx, pred in enumerate(extracted_risks):
                if idx in used_extracted_indices:
                    continue
                pred_title = str(self._get_field(pred, "title", "")).lower()
                
                # Match by keywords in title or direct title match
                if any(kw.lower() in pred_title for kw in gold_title_keywords if kw):
                    matched_risk = pred
                    matched_idx = idx
                    used_extracted_indices.add(idx)
                    break

            if matched_risk is not None:
                matched_count += 1
                pred_cat_raw = self._get_field(matched_risk, "category", "")
                pred_cat = pred_cat_raw.value if hasattr(pred_cat_raw, "value") else str(pred_cat_raw).lower()
                
                cat_match = (pred_cat == gold_category)
                if cat_match:
                    correct_categories += 1

                pred_mitigation = self._get_field(matched_risk, "mitigation")
                has_pred_mitigation = bool(pred_mitigation and str(pred_mitigation).strip() and str(pred_mitigation).strip() != "None" and len(str(pred_mitigation).strip()) > 10)

                mitigation_match = False
                if gold_has_mitigation:
                    if has_pred_mitigation:
                        captured_mitigations += 1
                        mitigation_match = True
                else:
                    mitigation_match = True

                matched_details.append({
                    "golden_id": gold_id,
                    "golden_title": gold.get("title"),
                    "matched_title": self._get_field(matched_risk, "title"),
                    "category_match": cat_match,
                    "golden_category": gold_category,
                    "extracted_category": pred_cat,
                    "mitigation_match": mitigation_match,
                    "expected_mitigation": gold_has_mitigation,
                    "extracted_mitigation": pred_mitigation
                })
            else:
                unmatched_golden.append({
                    "golden_id": gold_id,
                    "golden_title": gold.get("title"),
                    "category": gold_category,
                    "pages": gold.get("pages")
                })

        total_gold = len(self.golden_set)
        recall = matched_count / total_gold if total_gold > 0 else 0.0
        cat_acc = correct_categories / matched_count if matched_count > 0 else 0.0
        
        expected_mitigations_total = sum(1 for g in self.golden_set if g.get("expected_mitigation", g.get("has_mitigation", False)))
        mit_cov = captured_mitigations / expected_mitigations_total if expected_mitigations_total > 0 else 1.0

        # Passing threshold criteria
        passed = (recall >= 0.75) and (cat_acc >= 0.70) and (grounding_score >= 0.80)

        return EvalScore(
            total_golden_risks=total_gold,
            total_extracted_risks=len(extracted_risks),
            matched_risks=matched_count,
            recall=round(recall, 2),
            category_accuracy=round(cat_acc, 2),
            mitigation_coverage=round(mit_cov, 2),
            grounding_score=round(grounding_score, 2),
            passed=passed,
            details={
                "matched_count": matched_count,
                "unmatched_golden_count": len(unmatched_golden),
                "matched_details": matched_details,
                "unmatched_golden": unmatched_golden,
                "unmatched_extracted_count": len(extracted_risks) - matched_count
            }
        )