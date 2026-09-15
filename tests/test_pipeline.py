"""
Tests for RiskExtractionPipeline and Extractor components.
"""

import unittest
from unittest.mock import MagicMock
from src.risk_pipeline.models import (
    Evidence,
    ExtractionResult,
    ParsedPage,
    ParsedSection,
    Risk,
    RiskCategory,
)
from src.risk_pipeline.pipeline import RiskExtractionPipeline
from src.risk_pipeline.extractor import RiskExtractor, build_extraction_chain


class TestPipeline(unittest.TestCase):
    def test_pipeline_deduplication(self):
        risk1 = Risk(
            title="Cyber Attack Risk",
            description="Threat to critical infrastructure.",
            category=RiskCategory.CYBER,
            section="Main risks",
            pages=[51],
            mitigation="SOC monitoring",
            evidence=[Evidence(page=51, quote="Cyber attacks on grid...")],
        )
        risk1_dup = Risk(
            title="Cyber Attack Risk",
            description="Duplicate entry.",
            category=RiskCategory.CYBER,
            section="Main risks",
            pages=[51],
            mitigation="SOC monitoring",
            evidence=[],
        )
        risk2 = Risk(
            title="GHG Emissions Impact",
            description="Scope 1, 2, 3 emissions.",
            category=RiskCategory.CLIMATE,
            section="Climate Change",
            pages=[85],
            mitigation="Decarbonization strategy",
            evidence=[Evidence(page=85, quote="Scope 3 emissions...")],
        )

        sec1_res = ExtractionResult(risks=[risk1, risk1_dup])
        sec2_res = ExtractionResult(risks=[risk2])

        aggregated = RiskExtractionPipeline._aggregate_and_deduplicate([sec1_res, sec2_res])
        self.assertEqual(len(aggregated.risks), 2)
        self.assertEqual(aggregated.risks[0].title, "Cyber Attack Risk")
        self.assertEqual(aggregated.risks[1].title, "GHG Emissions Impact")

    def test_pipeline_with_mock_extractor(self):
        mock_extractor = MagicMock(spec=RiskExtractor)
        mock_risk = Risk(
            title="Project Execution",
            description="Risks around project execution.",
            category=RiskCategory.OPERATIONAL,
            section="Risk Management",
            pages=[50],
            mitigation="Quality gates",
            evidence=[Evidence(page=50, quote="Project execution involves...")],
        )
        mock_extractor.extract_batch.return_value = [ExtractionResult(risks=[mock_risk])]

        pipeline = RiskExtractionPipeline(extractor=mock_extractor)
        dummy_sec = ParsedSection(
            name="Risk Management",
            page_numbers=[50],
            pages=[ParsedPage(page_number=50, text="Dummy text")],
            formatted_content="=== PDF PAGE 50 ===\n\nDummy text",
        )

        result = pipeline.run_from_sections([dummy_sec])
        self.assertEqual(len(result.risks), 1)
        self.assertEqual(result.risks[0].title, "Project Execution")
        self.assertEqual(result.risks[0].category, RiskCategory.OPERATIONAL)

    def test_extractor_payload_preparation(self):
        sec = ParsedSection(
            name="Climate Change",
            page_numbers=[85, 86],
            pages=[],
            formatted_content="Content text",
        )
        payload = RiskExtractor._prepare_section_payload(sec)
        self.assertEqual(payload["section_name"], "Climate Change")
        self.assertEqual(payload["page_numbers"], [85, 86])
        self.assertEqual(payload["content"], "Content text")


if __name__ == "__main__":
    unittest.main()
