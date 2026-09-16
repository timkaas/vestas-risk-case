import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.risk_pipeline.models import RiskCategory, Risk


@dataclass
class GoldenData:
    id: str
    section: str
    pages: List[int]
    category: RiskCategory
    title_keywords: List[str]
    expected_mitigation: bool
    title: Optional[str] = None
    key_mitigation_keywords: Optional[List[str]] = None
    evidence: Optional[List[Dict[str, Any]]] = None

def load_from_json(file_path) -> List[GoldenData]:
    with open(file_path, 'r') as file:
        reader = json.load(file)
    return [GoldenData(**data) for data in reader]

@dataclass(frozen=True)
class EvalScore:
    total_golden_risks: int
    total_extracted_risks: int
    matched_risks: int
    recall: float
    category_accuracy: float
    mitigation_coverage: float
    grounding_score: float
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)


class RiskPipelineEvaluator:
    def __init__(self, golden_set_path: Path):
        self.golden_set_path = golden_set_path
        self.golden_set = load_from_json(self.golden_set_path)

    @staticmethod
    def _normalize_mitigation_text(text: str) -> str:
        """Normalize hyphenated and whitespace variants before phrase matching."""
        return " ".join(text.lower().replace("-", " ").split())

    def evaluate(
        self,
        extracted_risks: List[Risk],
        raw_markdown_pages: Dict[int, str]
    ) -> EvalScore:

        matched_count = 0
        correct_categories = 0
        captured_mitigations = 0
        total_quotes = 0
        grounded_quotes = 0
        
        matched_details = []
        unmatched_golden = []

        # 1. Grounding check: verify evidence quotes exist in source
        if raw_markdown_pages:
            for risk in extracted_risks:
                evidence_items = risk.evidence
                for ev in evidence_items:
                    total_quotes += 1
                    ev_page = ev.page
                    ev_quote = ev.quote.strip()
                    page_text = raw_markdown_pages.get(ev_page, "") if ev_page is not None else ""
                    
                    if ev_quote:
                        quote_snippet = ev_quote[:30].lower()
                        if page_text and quote_snippet in page_text.lower():
                            grounded_quotes += 1
            grounding_score = (grounded_quotes / total_quotes) if total_quotes > 0 else 1.0
        else:
            grounding_score = 1.0

        # 2. Golden set matching
        used_extracted_indices = set()
        for gold in self.golden_set:
            best_idx = -1
            best_score = 0
            gold_pages = set(gold.pages)
            gold_sec = gold.section.lower()

            for idx, pred in enumerate(extracted_risks):
                if idx in used_extracted_indices:
                    continue

                pred_title = pred.title.lower()
                pred_norm = pred_title.replace(" ", "").replace("-", "")
                pred_pages = set(pred.pages)
                pred_sec = pred.section.lower()

                # Check keyword overlap
                kw_matches = sum(1 for kw in gold.title_keywords if kw and (
                    kw.lower() in pred_title or pred_title in kw.lower() or 
                    kw.lower().replace(" ", "").replace("-", "") in pred_norm
                ))
                if kw_matches == 0:
                    continue

                score = kw_matches * 10
                if gold_pages & pred_pages:
                    score += 25
                if gold_sec in pred_sec or pred_sec in gold_sec:
                    score += 10

                if score > best_score:
                    best_score = score
                    best_idx = idx

            if best_idx != -1:
                matched_risk = extracted_risks[best_idx]
                used_extracted_indices.add(best_idx)
                matched_count += 1

                pred_cat = matched_risk.category.value if hasattr(matched_risk.category, "value") else str(matched_risk.category).lower()
                gold_cat = gold.category.value if hasattr(gold.category, "value") else str(gold.category).lower()
                cat_match = (pred_cat == gold_cat)
                if cat_match:
                    correct_categories += 1

                mitigation_match = False
                if gold.expected_mitigation:
                    mitigation = self._normalize_mitigation_text(
                        str(matched_risk.mitigation or "")
                    )
                    mitigation_keywords = gold.key_mitigation_keywords or []
                    if mitigation and any(
                        self._normalize_mitigation_text(keyword) in mitigation
                        for keyword in mitigation_keywords
                    ):
                        captured_mitigations += 1
                        mitigation_match = True
                else:
                    mitigation_match = True

                matched_details.append({
                    "golden_id": gold.id,
                    "golden_title": gold.title,
                    "matched_title": matched_risk.title,
                    "category_match": cat_match,
                    "golden_category": gold_cat,
                    "extracted_category": pred_cat,
                    "mitigation_match": mitigation_match,
                    "expected_mitigation": gold.expected_mitigation,
                    "extracted_mitigation": matched_risk.mitigation
                })
            else:
                unmatched_golden.append({
                    "golden_id": gold.id,
                    "golden_title": gold.title,
                    "category": gold.category.value if hasattr(gold.category, "value") else str(gold.category),
                    "pages": gold.pages
                })

        total_gold = len(self.golden_set)
        recall = matched_count / total_gold if total_gold > 0 else 0.0
        cat_acc = correct_categories / matched_count if matched_count > 0 else 0.0
        
        expected_mitigations_total = sum(1 for g in self.golden_set if g.expected_mitigation)
        mit_cov = captured_mitigations / expected_mitigations_total if expected_mitigations_total > 0 else 1.0

        # Passing threshold criteria across all four essential quality dimensions
        passed = (recall >= 0.75) and (cat_acc >= 0.70) and (mit_cov >= 0.70) and (grounding_score >= 0.80)

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
