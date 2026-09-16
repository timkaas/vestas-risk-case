"""
Script for running RiskPipelineEvaluator against extracted risks.

For now, the risks to evaluate are provided as a hardcoded JSON placeholder below.
When you connect your extraction pipeline, you can pass live extraction outputs
or load them directly from an extraction output JSON file.
"""

import argparse
import sys
import pathlib as pl

from src.config import DEFAULT_GOLDEN_SET_PATH, DEFAULT_PDF_PATH, DEFAULT_SECTIONS_DEF_PATH, \
    DEFAULT_MODEL_NAME, DEFAULT_TEMPERATURE, DEFAULT_MAX_CONCURRENCY

from src.eval.evaluator import RiskPipelineEvaluator, EvalScore
from src.risk_pipeline.models import ExtractionResult
from src.risk_pipeline.parser import ReportParser, parse_report_definition

def format_evaluation_report(score: EvalScore, golden_path: pl.Path, source_desc: str) -> str:
    """Build the human-readable report used for both stdout and saved artifacts."""
    lines = [
        "=" * 80,
        " 🎯 RISK PIPELINE EVALUATION REPORT",
        "=" * 80,
        f"📁 Golden Set Source:   {golden_path}",
        f"📊 Extracted Input:      {source_desc}",
        "-" * 80,
        "📈 SUMMARY METRICS:",
        f"  • Total Golden Risks:       {score.total_golden_risks}",
        f"  • Total Extracted Risks:    {score.total_extracted_risks}",
        f"  • Matched Golden Risks:     {score.matched_risks} / {score.total_golden_risks}",
        f"  • Risk Extraction Recall:   {score.recall * 100:.1f}%  (target >= 75%)",
        f"  • Category Accuracy:        {score.category_accuracy * 100:.1f}%  (target >= 70%)",
        f"  • Mitigation Coverage:      {score.mitigation_coverage * 100:.1f}%  (target >= 70%)",
        f"  • Grounding Score:          {score.grounding_score * 100:.1f}%  (target >= 80%)",
        "-" * 80,
    ]
    
    status_str = "✅ PASSED" if score.passed else "❌ FAILED (Regression Detected)"
    lines.extend([f"🏁 Overall Status:           {status_str}", "=" * 80])
    
    matched_details = score.details.get("matched_details", [])
    if matched_details:
        lines.extend([
            "",
            "🔍 MATCHED RISKS BREAKDOWN:",
            f"{'Golden ID':<28} | {'Category Match':<16} | {'Mitigation Match':<16} | {'Matched Title'}",
            "-" * 85,
        ])
        for d in matched_details:
            cat_status = "✅ " + str(d['extracted_category']) if d['category_match'] else f"❌ ({d['golden_category']} vs {d['extracted_category']})"
            mit_status = "✅ Captured" if d['mitigation_match'] else "❌ Missed"
            lines.append(f"{d['golden_id']:<28} | {cat_status:<16} | {mit_status:<16} | {d['matched_title'][:35]}")

    unmatched_golden = score.details.get("unmatched_golden", [])
    if unmatched_golden:
        lines.extend(["", "⚠️ UNMATCHED GOLDEN RISKS (False Negatives / Missed):"])
        for ug in unmatched_golden:
            lines.append(f"  - [{ug['golden_id']}] {ug['golden_title']} (Category: {ug['category']}, Pages: {ug['pages']})")

    lines.extend(["", "=" * 80])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate risk extraction pipeline against golden set.")
    parser.add_argument(
        "--pdf", "-p",
        type=pl.Path,
        default=DEFAULT_PDF_PATH,
        help=f"Path to input annual report PDF file for live extraction. (Default: data/VestasAnnualReport2025.pdf)"
    )
    parser.add_argument(
        "--input", "-i",
        type=pl.Path,
        default=DEFAULT_SECTIONS_DEF_PATH,
        help=f"Path to a report-definition JSON file containing the report and target sections. (Default: {DEFAULT_SECTIONS_DEF_PATH})"
    )
    parser.add_argument(
        "--golden-set", "-g",
        type=pl.Path,
        default=DEFAULT_GOLDEN_SET_PATH,
        help="Path to golden set (.json)"
    )
    parser.add_argument(
        "--results", "-r",
        type=pl.Path,
        default=None,
        help="Optional extraction-results JSON file; otherwise runs the live pipeline."
    )
    parser.add_argument(
        "--output", "-o",
        type=pl.Path,
        default=None,
        help="Optional path to save the human-readable evaluation report."
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
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: JSON input file '{args.input}' does not exist.", file=sys.stderr)
        sys.exit(1)

    definition = parse_report_definition(args.input)
    pdf_path, sections = definition.report_path, definition.sections

    if args.results:
        extracted_risks = ExtractionResult.from_file(args.results).risks
        source_desc = f"File: {args.results} ({len(extracted_risks)} items)"
    else:
        from src.risk_pipeline.pipeline import RiskExtractionPipeline
        """Run risk extraction pipeline and optionally save and evaluate output."""
        pipeline = RiskExtractionPipeline(
            model_name=args.model,
            temperature=args.temperature,
            max_concurrency=args.concurrency,
        )
        res = pipeline.run(pdf_path=pdf_path, sections=sections, show_progress=True)
        extracted_risks = res.risks
        source_desc = f"Live Extraction Pipeline on {pdf_path} ({len(extracted_risks)} items)"

    evaluator = RiskPipelineEvaluator(golden_set_path=args.golden_set)
    md_pages = ReportParser().load_page_text_map(args.pdf, sections)

    score = evaluator.evaluate(extracted_risks=extracted_risks, raw_markdown_pages=md_pages)

    report = format_evaluation_report(score, args.golden_set, source_desc)
    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
        print(f"\nSaved evaluation report to {args.output}")

    if not score.passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
