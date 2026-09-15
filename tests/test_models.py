"""
Tests for Risk Intelligence Data Models.
"""

import tempfile
import unittest
from pathlib import Path
from src.risk_pipeline.models import (
    Evidence,
    ExtractionResult,
    ParsedPage,
    ParsedSection,
    Risk,
    RiskCategory,
    SectionSpec,
)


class TestRiskModels(unittest.TestCase):
    def test_risk_category_parsing(self):
        self.assertEqual(RiskCategory("financial"), RiskCategory.FINANCIAL)
        self.assertEqual(RiskCategory("cyber"), RiskCategory.CYBER)
        self.assertEqual(RiskCategory("cybersecurity"), RiskCategory.CYBER)
        self.assertEqual(RiskCategory("supply chain"), RiskCategory.SUPPLY_CHAIN)
        self.assertEqual(RiskCategory("geopolitical"), RiskCategory.GEOPOLITICAL)
        self.assertEqual(RiskCategory("unknown_category_xyz"), RiskCategory.OTHER)

    def test_evidence_and_risk_model(self):
        ev = Evidence(page=51, quote="Sample quote here")
        risk = Risk(
            title="Test Risk",
            description="A detailed description of the risk.",
            category=RiskCategory.OPERATIONAL,
            section="Main risks",
            pages=[51],
            mitigation="Mitigation actions taken",
            evidence=[ev],
        )
        self.assertEqual(risk.title, "Test Risk")
        self.assertEqual(risk.category, RiskCategory.OPERATIONAL)
        self.assertEqual(risk.mitigation, "Mitigation actions taken")
        self.assertEqual(len(risk.evidence), 1)
        self.assertEqual(risk.evidence[0].page, 51)

    def test_risk_mitigation_cleaner(self):
        risk1 = Risk(
            title="Risk 1",
            description="Desc",
            category=RiskCategory.FINANCIAL,
            section="Sec",
            pages=[1],
            mitigation="None",
            evidence=[],
        )
        self.assertIsNone(risk1.mitigation)

        risk2 = Risk(
            title="Risk 2",
            description="Desc",
            category=RiskCategory.FINANCIAL,
            section="Sec",
            pages=[1],
            mitigation="  N/A  ",
            evidence=[],
        )
        self.assertIsNone(risk2.mitigation)

    def test_extraction_result_serialization(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            ev = Evidence(page=51, quote="Evidence text")
            risk = Risk(
                title="Cyber Attacks",
                description="Cyber threats targeting assets.",
                category=RiskCategory.CYBER,
                section="Main risks",
                pages=[51],
                mitigation="Strong firewalls",
                evidence=[ev],
            )
            res = ExtractionResult(risks=[risk])

            # Test indexing, length, iteration
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0].title, "Cyber Attacks")
            self.assertEqual([r.title for r in res], ["Cyber Attacks"])

            # Test JSON save/load
            json_file = tmp_path / "risks.json"
            res.save_json(json_file)
            loaded_res = ExtractionResult.from_file(json_file)
            self.assertEqual(len(loaded_res), 1)
            self.assertEqual(loaded_res[0].title, "Cyber Attacks")
            self.assertEqual(loaded_res[0].category, RiskCategory.CYBER)

            # Test JSONL save/load
            jsonl_file = tmp_path / "risks.jsonl"
            res.save_jsonl(jsonl_file)
            loaded_jsonl = ExtractionResult.from_file(jsonl_file)
            self.assertEqual(len(loaded_jsonl), 1)
            self.assertEqual(loaded_jsonl[0].title, "Cyber Attacks")

            # Test markdown representation
            md = res._repr_markdown_()
            self.assertIn("### 📋 Extracted Risks", md)
            self.assertIn("Cyber Attacks", md)
            self.assertIn("`CYBER`", md)


if __name__ == "__main__":
    unittest.main()
