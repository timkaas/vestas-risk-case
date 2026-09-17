"""
Main entry point and CLI for the Vestas Risk Intelligence Pipeline.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

from dotenv import load_dotenv

from run_eval import format_evaluation_report

load_dotenv()

from src.config import (
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_MODEL_NAME,
    DEFAULT_TEMPERATURE, DEFAULT_SECTIONS_DEF_PATH, DEFAULT_PDF_PATH, DEFAULT_GOLDEN_SET_PATH,
)
from src.risk_pipeline.models import ExtractionResult, SectionSpec
from src.risk_pipeline.parser import ReportParser, parse_report_definition
from src.risk_pipeline.pipeline import RiskExtractionPipeline
from src.eval.evaluator import RiskPipelineEvaluator


def setup_logging(verbose: bool = False):
    """Configure logging format and level."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def run_pipeline(
        pdf_path: Path,
        output_path: Optional[Path] = None,
        output_format: str = "json",
        model_name: str = DEFAULT_MODEL_NAME,
        temperature: float = DEFAULT_TEMPERATURE,
        concurrency: int = DEFAULT_MAX_CONCURRENCY,
        evaluate: bool = False,
        golden_set_path: Optional[Path] = None,
        show_progress: bool = True,
        sections: Optional[Sequence[SectionSpec]] = None,
) -> ExtractionResult:
    """Run risk extraction pipeline and optionally save and evaluate output."""
    pipeline = RiskExtractionPipeline(
        model_name=model_name,
        temperature=temperature,
        max_concurrency=concurrency,
    )

    print(f"\n🚀 Running Risk Intelligence Extraction Pipeline...")
    print(f"📄 Target Report: {pdf_path}")
    print(f"🤖 LLM Model:     {model_name} (temperature: {temperature})")
    print(f"⚡ Concurrency:    {concurrency}")
    if sections:
        section_desc = ", ".join(
            f"{s.name} (pp. {min(s.page_range) + 1}-{max(s.page_range) + 1})" if min(s.page_range) != max(
                s.page_range) else f"{s.name} (p. {min(s.page_range) + 1})" for s in sections)
        print(f"📑 Sections:      {section_desc}")
    print()

    result = pipeline.run(pdf_path=pdf_path, sections=sections, show_progress=show_progress)

    print(f"\n✅ Extraction complete! Identified {len(result.risks)} corporate risks.")

    # Save output if path specified
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save_json(output_path)
        print(f"💾 Extracted risks saved to: {output_path} (format: {output_format})")

    # Run evaluation if requested
    if evaluate and golden_set_path:
        print("\n📊 Running evaluation against golden dataset...")
        evaluator = RiskPipelineEvaluator(golden_set_path=golden_set_path)

        raw_pages = ReportParser().load_page_text_map(pdf_path, sections)

        score = evaluator.evaluate(
            extracted_risks=result.risks,
            raw_markdown_pages=raw_pages,
        )
        report = format_evaluation_report(
            score=score,
            golden_path=evaluator.golden_set_path,
            source_desc=f"Live Pipeline Run ({len(result.risks)} risks)",
        )
        print(report)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Risk Intelligence Extraction Pipeline CLI"
    )
    parser.add_argument(
        "--pdf", "-p",
        type=Path,
        default=DEFAULT_PDF_PATH,
        help=f"Path to input annual report PDF file. (Default: {DEFAULT_PDF_PATH})"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=DEFAULT_SECTIONS_DEF_PATH,
        help=f"Path to a report-definition JSON file containing the target sections. (Default: {DEFAULT_SECTIONS_DEF_PATH})"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Optional output file path to save extracted risks (e.g. 'data/extracted_risks.json')"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=DEFAULT_MODEL_NAME,
        help=f"OpenAI LLM model for extraction. (Default: {DEFAULT_MODEL_NAME})"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=f"LLM temperature (Default: {DEFAULT_TEMPERATURE})"
    )
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=DEFAULT_MAX_CONCURRENCY,
        help=f"Max concurrent LLM requests (Default: {DEFAULT_MAX_CONCURRENCY})"
    )
    parser.add_argument(
        "--eval", "-e",
        action="store_true",
        help="Evaluate extraction output against the golden set after running."
    )
    parser.add_argument(
        "--golden-set", "-g",
        type=str,
        default=DEFAULT_GOLDEN_SET_PATH,
        help=f"Path to golden set file (.json) for evaluation. (Default: {DEFAULT_GOLDEN_SET_PATH})"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging."
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    if not args.pdf.exists():
        print(f"Error: PDF file '{args.pdf}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if not args.input.exists():
        print(f"Error: JSON input file '{args.input}' does not exist.", file=sys.stderr)
        sys.exit(1)

    definition = parse_report_definition(args.input)
    parsed_sections = definition.sections

    if args.eval and not args.golden_set:
        parser.error("Error: --golden-set is required when --eval is specified.")

    result = run_pipeline(
        pdf_path=args.pdf,
        output_path=args.output,
        model_name=args.model,
        temperature=args.temperature,
        concurrency=args.concurrency,
        evaluate=args.eval,
        golden_set_path=args.golden_set,
        show_progress=True,
        sections=parsed_sections,
    )

    if not args.output:
        print("\n" + result._repr_markdown_())


if __name__ == "__main__":
    main()
