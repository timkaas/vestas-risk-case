"""
Tests for main.py CLI arguments and parser options.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import main


class TestMainCLI(unittest.TestCase):
    def test_cli_sections_argument_parsing(self):
        with patch("sys.argv", ["main.py", "--sections", "50-51", "71-74", "118"]):
            with patch("main.run_pipeline") as mock_run:
                mock_run.return_value = MagicMock()
                # We need pdf to exist or mock Path.exists
                with patch.object(Path, "exists", return_value=True):
                    main.main()
                    mock_run.assert_called_once()
                    call_kwargs = mock_run.call_args.kwargs
                    sections = call_kwargs.get("sections")
                    self.assertIsNotNone(sections)
                    self.assertEqual(len(sections), 3)
                    self.assertEqual(sections[0].name, "Pages 50-51")
                    self.assertEqual(sections[0].pages, [49, 50])
                    self.assertEqual(sections[1].name, "Pages 71-74")
                    self.assertEqual(sections[1].pages, [70, 71, 72, 73])
                    self.assertEqual(sections[2].name, "Page 118")
                    self.assertEqual(sections[2].pages, [117])

    def test_cli_short_sections_argument(self):
        with patch("sys.argv", ["main.py", "-s", "118"]):
            with patch("main.run_pipeline") as mock_run:
                mock_run.return_value = MagicMock()
                with patch.object(Path, "exists", return_value=True):
                    main.main()
                    mock_run.assert_called_once()
                    sections = mock_run.call_args.kwargs.get("sections")
                    self.assertEqual(len(sections), 1)
                    self.assertEqual(sections[0].name, "Page 118")
                    self.assertEqual(sections[0].pages, [117])

    def test_cli_sections_comma_separated(self):
        with patch("sys.argv", ["main.py", "-s", "50-51,71-74,118"]):
            with patch("main.run_pipeline") as mock_run:
                mock_run.return_value = MagicMock()
                with patch.object(Path, "exists", return_value=True):
                    main.main()
                    mock_run.assert_called_once()
                    sections = mock_run.call_args.kwargs.get("sections")
                    self.assertEqual(len(sections), 3)


if __name__ == "__main__":
    unittest.main()
