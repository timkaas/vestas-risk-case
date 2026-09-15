"""
Tests for PDF and Markdown ReportParser.
"""

import unittest
from pathlib import Path
from src.risk_pipeline.config import DEFAULT_PDF_PATH
from src.risk_pipeline.models import ParsedPage, ParsedSection, SectionSpec
from src.risk_pipeline.parser import ReportParser, format_pages, format_sections


class TestReportParser(unittest.TestCase):
    def test_format_pages_and_sections(self):
        p1 = ParsedPage(page_number=50, text="Content of page 50")
        p2 = ParsedPage(page_number=51, text="Content of page 51")

        formatted = format_pages([p1, p2])
        self.assertIn("=== PDF PAGE 50 ===", formatted)
        self.assertIn("=== PDF PAGE 51 ===", formatted)
        self.assertIn("Content of page 50", formatted)

        sec = ParsedSection(
            name="Risk Management",
            page_numbers=[50, 51],
            pages=[p1, p2],
            formatted_content=formatted,
        )
        full_doc = format_sections([sec])
        self.assertIn("# Risk Management", full_doc)
        self.assertIn("=== PDF PAGE 50 ===", full_doc)

    def test_parser_with_vestas_pdf(self):
        if not DEFAULT_PDF_PATH.exists():
            self.skipTest(f"PDF not found at {DEFAULT_PDF_PATH}")

        parser = ReportParser()
        test_sections = [
            SectionSpec(name="Risk Management", page_range=range(49, 51)),
            SectionSpec(name="Cyber Security", page_range=range(117, 118)),
        ]
        parsed_sections = parser.parse_pdf_sections(
            pdf_path=DEFAULT_PDF_PATH,
            sections=test_sections,
        )

        self.assertEqual(len(parsed_sections), 2)
        self.assertEqual(parsed_sections[0].name, "Risk Management")
        self.assertEqual(parsed_sections[0].page_numbers, [50, 51])
        self.assertEqual(len(parsed_sections[0].pages), 2)

        self.assertEqual(parsed_sections[1].name, "Cyber Security")
        self.assertEqual(parsed_sections[1].page_numbers, [118])

    def test_page_text_map_loading(self):
        if not DEFAULT_PDF_PATH.exists():
            self.skipTest(f"PDF not found at {DEFAULT_PDF_PATH}")

        parser = ReportParser()
        page_map = parser.load_page_text_map(
            pdf_path=DEFAULT_PDF_PATH,
            sections=[SectionSpec(name="Test", page_range=range(49, 51))],
        )

        self.assertIn(50, page_map)
        self.assertIn(51, page_map)
        self.assertGreater(len(page_map[51]), 0)


if __name__ == "__main__":
    unittest.main()
