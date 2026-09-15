"""
Main entry point and CLI for the Vestas Risk Intelligence Pipeline.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables (.env)
load_dotenv()

from src.risk_pipeline.config import (
    DEFAULT_GOLDEN_SET_PATH,
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_MODEL_NAME,
    DEFAULT_PDF_PATH,
    DEFAULT_TEMPERATURE,
)
from src.risk_pipeline.models import ExtractionResult
from src.risk_pipeline.pipeline import RiskExtractionPipeline
from src.eval.evaluator import RiskPipelineEvaluator
from src.eval.run_eval import print_evaluation_report, load_raw_markdown_pages


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
    golden_set_path: Optional[str] = None,
    markdown_path: Optional[str] = None,
    show_progress: bool = True,
) -> ExtractionResult:
    """Run risk extraction pipeline and optionally save and evaluate output."""
    pipeline = RiskExtractionPipeline(
        model_name=model_name,
        temperature=temperature,
        max_concurrency=concurrency,
    )

    print(f"\n🚀 Running Risk Intelligence Extraction Pipeline...")
    print(f"📄 Target Report: {pdf_path}")
    print(f"🤖 LLM Model:    {model_name} (temperature: {temperature})")
    print(f"⚡ Concurrency:  {concurrency}\n")

    result = pipeline.run(pdf_path=pdf_path, show_progress=show_progress)

    print(f"\n✅ Extraction complete! Identified {len(result.risks)} corporate risks.")

    # Save output if path specified
    if output_path:
        out_file = Path(output_path)
        if output_format == "jsonl":
            result.save_jsonl(out_file)
        elif output_format == "markdown" or output_format == "md":
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(result._repr_markdown_(), encoding="utf-8")
        else:
            result.save_json(out_file)
        print(f"💾 Extracted risks saved to: {out_file} (format: {output_format})")

    # Run evaluation if requested
    if evaluate:
        print("\n📊 Running evaluation against golden dataset...")
        evaluator = RiskPipelineEvaluator(golden_set_path=golden_set_path)
        
        md_file = Path(markdown_path) if markdown_path else PROJECT_ROOT / "data" / "VestasAnnualReport2025.md"
        raw_pages = load_raw_markdown_pages(md_file)
        
        score = evaluator.evaluate(
            extracted_risks=result.risks,
            raw_markdown_pages=raw_pages,
        )
        print_evaluation_report(
            score=score,
            golden_path=evaluator.golden_set_path,
            source_desc=f"Live Pipeline Run ({len(result.risks)} risks)",
        )

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Risk Intelligence Extraction Pipeline CLI"
    )
    parser.add_argument(
        "--pdf", "-p",
        type=str,
        default=str(DEFAULT_PDF_PATH),
        help=f"Path to input annual report PDF file. (Default: {DEFAULT_PDF_PATH})"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Optional output file path to save extracted risks (e.g. 'data/extracted_risks.json')"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "jsonl", "markdown", "md"],
        default="json",
        help="Output serialization format (json, jsonl, markdown). Default: json"
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
        default=None,
        help="Path to golden set file (.jsonl or .json) for evaluation."
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose debug logging."
    )
    parser.add_argument(
        "--print-md",
        action="store_true",
        help="Print full formatted markdown summary of extracted risks to console."
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    pdf_file = Path(args.pdf)
    if not pdf_file.exists():
        print(f"Error: PDF file '{pdf_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    result = run_pipeline(
        pdf_path=pdf_file,
        output_path=Path(args.output) if args.output else None,
        output_format=args.format,
        model_name=args.model,
        temperature=args.temperature,
        concurrency=args.concurrency,
        evaluate=args.eval,
        golden_set_path=args.golden_set,
        show_progress=True,
    )

    if args.print_md:
        print("\n" + result._repr_markdown_())


if __name__ == "__main__":
    main()
