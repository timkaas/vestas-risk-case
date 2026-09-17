"""
Tests for PDF and Markdown ReportParser.
"""

import unittest

from src.config import DEFAULT_PDF_PATH
from src.risk_pipeline.models import ParsedPage, SectionSpec
from src.risk_pipeline.parser import ReportParser, format_pages, parse_page_ranges


class TestReportParser(unittest.TestCase):
    def test_parse_page_ranges_single_pages(self):
        # Single page string
        specs = parse_page_ranges("118")
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0].name, "Page 118")
        self.assertEqual(specs[0].pages, [117])

        # Single page integer
        specs_int = parse_page_ranges([5])
        self.assertEqual(len(specs_int), 1)
        self.assertEqual(specs_int[0].name, "Page 5")
        self.assertEqual(specs_int[0].pages, [4])

    def test_parse_page_ranges_multiple_ranges(self):
        # List of range strings and single pages
        specs = parse_page_ranges(["50-51", "71-74", "118"])
        self.assertEqual(len(specs), 3)
        self.assertEqual(specs[0].name, "Pages 50-51")
        self.assertEqual(specs[0].pages, [49, 50])
        self.assertEqual(specs[1].name, "Pages 71-74")
        self.assertEqual(specs[1].pages, [70, 71, 72, 73])
        self.assertEqual(specs[2].name, "Page 118")
        self.assertEqual(specs[2].pages, [117])

    def test_parse_page_ranges_comma_separated(self):
        specs = parse_page_ranges("50-51, 71-74, 85-92, 118")
        self.assertEqual(len(specs), 4)
        self.assertEqual(specs[0].pages, [49, 50])
        self.assertEqual(specs[1].pages, [70, 71, 72, 73])
        self.assertEqual(specs[2].pages, [84, 85, 86, 87, 88, 89, 90, 91])
        self.assertEqual(specs[3].pages, [117])

    def test_parse_page_ranges_alternative_separators(self):
        specs_colon = parse_page_ranges("50:51")
        self.assertEqual(specs_colon[0].pages, [49, 50])

        specs_dot = parse_page_ranges("50..51")
        self.assertEqual(specs_dot[0].pages, [49, 50])

    def test_parse_page_ranges_invalid_inputs(self):
        with self.assertRaises(ValueError):
            parse_page_ranges("0")

        with self.assertRaises(ValueError):
            parse_page_ranges("-5")

        with self.assertRaises(ValueError):
            parse_page_ranges("50-40")

        with self.assertRaises(ValueError):
            parse_page_ranges("abc")

        with self.assertRaises(ValueError):
            parse_page_ranges("50-xyz")

    def test_format_pages_and_sections(self):
        p1 = ParsedPage(page_number=50, text="Content of page 50")
        p2 = ParsedPage(page_number=51, text="Content of page 51")

        formatted = format_pages([p1, p2])
        self.assertIn("=== PDF PAGE 50 ===", formatted)
        self.assertIn("=== PDF PAGE 51 ===", formatted)
        self.assertIn("Content of page 50", formatted)

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
