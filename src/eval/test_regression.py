"""Regression tests for the risk-extraction quality gates.

These tests exercise the evaluator, not a live LLM or PDF parser. Their inputs
are deterministic mutations of the checked-in golden set, so they are fast and
reliable in CI while still proving that each quality gate catches its intended
failure mode.
"""
import dataclasses
import sys
from pathlib import Path
from collections import defaultdict
from collections.abc import Callable

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import DEFAULT_GOLDEN_SET_PATH, EVAL_PATH
from src.eval.evaluator import RiskPipelineEvaluator
from src.risk_pipeline.models import Evidence, Risk, RiskCategory


@pytest.fixture(scope="module")
def evaluator() -> RiskPipelineEvaluator:
    return RiskPipelineEvaluator(golden_set_path=DEFAULT_GOLDEN_SET_PATH)


@pytest.fixture(scope="module")
def baseline_risks(evaluator: RiskPipelineEvaluator) -> list[Risk]:
    """Build the known-good extraction directly from the immutable golden set."""
    return [
        Risk(
            title=gold.title or gold.id,
            description="Golden-set risk description.",
            category=gold.category,
            section=gold.section,
            pages=gold.pages,
            mitigation=", ".join(gold.key_mitigation_keywords),
            evidence=[Evidence(**evidence) for evidence in gold.evidence or []],
        )
        for gold in evaluator.golden_set
    ]


@pytest.fixture(scope="module")
def source_pages(baseline_risks: list[Risk]) -> dict[int, str]:
    """Minimal source corpus that makes every golden evidence quote verifiable."""
    pages: defaultdict[int, list[str]] = defaultdict(list)
    for risk in baseline_risks:
        for evidence in risk.evidence:
            pages[evidence.page].append(evidence.quote)
    return {page: "\n".join(quotes) for page, quotes in pages.items()}


def test_baseline_evaluation_is_approved(
    evaluator: RiskPipelineEvaluator,
    baseline_risks: list[Risk],
    source_pages: dict[int, str],
    data_regression: pytest.RegressionFixture,
) -> None:
    """Detect unintended changes to the complete approved evaluator result."""
    score = evaluator.evaluate(baseline_risks, source_pages)
    assert score.passed
    data_regression.check(dataclasses.asdict(score), fullpath=EVAL_PATH / "eval_regression.yml")


def omit_mitigations(risks: list[Risk]) -> list[Risk]:
    return [risk.model_copy(update={"mitigation": None}) for risk in risks]


def replace_one_mitigation_with_unrelated_text(risks: list[Risk]) -> list[Risk]:
    """Keep a mitigation present but remove the golden-set mitigation signals."""
    return [
        risk.model_copy(update={"mitigation": "General risk awareness training."})
        if risk.title == "Geopolitical and Regulatory Framework"
        else risk
        for risk in risks
    ]


def drop_half_of_risks(risks: list[Risk]) -> list[Risk]:
    return risks[: len(risks) // 2]


def corrupt_model_output(risks: list[Risk]) -> list[Risk]:
    fabricated_evidence = [Evidence(page=999, quote="Fabricated evidence absent from the report.")]
    return [
        risk.model_copy(
            update={"category": RiskCategory.OTHER, "evidence": fabricated_evidence}
        )
        for risk in risks
    ]


@pytest.mark.parametrize(
    ("mutate", "metric", "maximum"),
    [
        pytest.param(omit_mitigations, "mitigation_coverage", 0.0, id="prompt-omits-mitigations"),
        pytest.param(drop_half_of_risks, "recall", 0.50, id="parser-drops-sections"),
        pytest.param(corrupt_model_output, "grounding_score", 0.0, id="model-hallucinates-evidence"),
    ],
)
def test_evaluator_rejects_known_regressions(
    evaluator: RiskPipelineEvaluator,
    baseline_risks: list[Risk],
    source_pages: dict[int, str],
    mutate: Callable[[list[Risk]], list[Risk]],
    metric: str,
    maximum: float,
) -> None:
    """Each realistic degradation must trip the corresponding quality gate."""
    score = evaluator.evaluate(mutate(baseline_risks), source_pages)
    assert not score.passed
    assert getattr(score, metric) <= maximum


def test_mitigation_must_contain_a_golden_keyword(
    evaluator: RiskPipelineEvaluator,
    baseline_risks: list[Risk],
    source_pages: dict[int, str],
) -> None:
    """A generic mitigation must not count as the expected mitigation."""
    score = evaluator.evaluate(
        replace_one_mitigation_with_unrelated_text(baseline_risks), source_pages
    )

    detail = next(
        detail
        for detail in score.details["matched_details"]
        if detail["golden_id"] == "risk_geopolitical_p51"
    )
    assert not detail["mitigation_match"]
    assert score.mitigation_coverage == 0.86


def test_mitigation_keyword_matching_accepts_hyphen_variants(
    evaluator: RiskPipelineEvaluator,
    baseline_risks: list[Risk],
    source_pages: dict[int, str],
) -> None:
    risks = [
        risk.model_copy(update={"mitigation": "Offering low-emission materials."})
        if risk.title == "Climate Change Mitigation"
        else risk
        for risk in baseline_risks
    ]

    score = evaluator.evaluate(risks, source_pages)

    detail = next(
        detail
        for detail in score.details["matched_details"]
        if detail["golden_id"] == "risk_climate_mitigation_p71"
    )
    assert detail["mitigation_match"]
