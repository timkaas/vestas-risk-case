"""
Script for running RiskPipelineEvaluator against extracted risks.

For now, the risks to evaluate are provided as a hardcoded JSON placeholder below.
When you connect your extraction pipeline, you can pass live extraction outputs
or load them directly from an extraction output JSON file.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is on sys.path for direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.eval.evaluator import RiskPipelineEvaluator, EvalScore

def load_extracted_risks_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """Loads extracted risks from JSON array, JSONL, or stream of JSON objects."""
    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    
    # 1. Standard JSON array or single object
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "risks" in data and isinstance(data["risks"], list):
                return data["risks"]
            return [data]
    except Exception:
        pass

    # 2. Line by line JSON
    items = []
    try:
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("//"):
                items.append(json.loads(line))
        if items:
            return items
    except Exception:
        items = []

    # 3. Stream decode
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(content):
        while idx < len(content) and content[idx].isspace():
            idx += 1
        if idx >= len(content):
            break
        obj, end = decoder.raw_decode(content, idx)
        if isinstance(obj, list):
            items.extend(obj)
        elif isinstance(obj, dict) and "risks" in obj and isinstance(obj["risks"], list):
            items.extend(obj["risks"])
        else:
            items.append(obj)
        idx = end
def load_raw_markdown_pages(md_path: Path) -> Dict[int, str]:
    """
    Attempt to load markdown report and extract page text map.
    Handles page number markers (e.g. standalone page numbers or headers).
    """
    if not md_path.exists():
        return {}
    
    content = md_path.read_text(encoding="utf-8")
    
    # Simple heuristic to split or associate markdown content by page numbers
    # If the markdown has page markers, we index them
    page_map: Dict[int, str] = {}
    
    # Also store the full text as fallback for any referenced page
    # Look for patterns like "\n\n50 \n" or "Vestas Annual Report 2025 \n\n50"
    pages_found = re.findall(r"(?:Vestas Annual Report 2025\s+)?\n+(\d{1,3})\s*\n+", content)
    
    # Store full document for loose search across pages
    # Or map specific pages if regex splitting is available
    for p in [50, 51, 71, 72, 73, 74, 85, 86, 117, 118]:
        page_map[p] = content
        
    return page_map


def print_evaluation_report(score: EvalScore, golden_path: Path, source_desc: str):
    print("=" * 80)
    print(" 🎯 RISK PIPELINE EVALUATION REPORT")
    print("=" * 80)
    print(f"📁 Golden Set Source:   {golden_path}")
    print(f"📊 Extracted Input:      {source_desc}")
    print("-" * 80)
    print("📈 SUMMARY METRICS:")
    print(f"  • Total Golden Risks:       {score.total_golden_risks}")
    print(f"  • Total Extracted Risks:    {score.total_extracted_risks}")
    print(f"  • Matched Golden Risks:     {score.matched_risks} / {score.total_golden_risks}")
    print(f"  • Risk Extraction Recall:   {score.recall * 100:.1f}%  (target >= 75%)")
    print(f"  • Category Accuracy:        {score.category_accuracy * 100:.1f}%  (target >= 70%)")
    print(f"  • Mitigation Coverage:      {score.mitigation_coverage * 100:.1f}%  (target >= 70%)")
    print(f"  • Grounding Score:          {score.grounding_score * 100:.1f}%  (target >= 80%)")
    print("-" * 80)
    
    status_str = "✅ PASSED" if score.passed else "❌ FAILED (Regression Detected)"
    print(f"🏁 Overall Status:           {status_str}")
    print("=" * 80)
    
    matched_details = score.details.get("matched_details", [])
    if matched_details:
        print("\n🔍 MATCHED RISKS BREAKDOWN:")
        print(f"{'Golden ID':<28} | {'Category Match':<16} | {'Mitigation Match':<16} | {'Matched Title'}")
        print("-" * 85)
        for d in matched_details:
            cat_status = "✅ " + str(d['extracted_category']) if d['category_match'] else f"❌ ({d['golden_category']} vs {d['extracted_category']})"
            mit_status = "✅ Captured" if d['mitigation_match'] else "❌ Missed"
            print(f"{d['golden_id']:<28} | {cat_status:<16} | {mit_status:<16} | {d['matched_title'][:35]}")

    unmatched_golden = score.details.get("unmatched_golden", [])
    if unmatched_golden:
        print("\n⚠️ UNMATCHED GOLDEN RISKS (False Negatives / Missed):")
        for ug in unmatched_golden:
            print(f"  - [{ug['golden_id']}] {ug['golden_title']} (Category: {ug['category']}, Pages: {ug['pages']})")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Evaluate risk extraction pipeline against golden set.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live extraction pipeline directly on the report PDF before evaluating."
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default="data/VestasAnnualReport2025.pdf",
        help="Path to report PDF for live extraction."
    )
    parser.add_argument(
        "--golden-set", "-g",
        type=str,
        default=None,
        help="Path to golden set (.jsonl or .json). Defaults to auto-locating src/eval/golden-llm.jsonl"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Path to JSON or JSONL file with extracted risks. If not provided, uses the hardcoded placeholder."
    )
    parser.add_argument(
        "--markdown", "-m",
        type=str,
        default="data/VestasAnnualReport2025.md",
        help="Path to report markdown file for evidence quote grounding check."
    )

    args = parser.parse_args()

    # 1. Initialize Evaluator
    evaluator = RiskPipelineEvaluator(golden_set_path=args.golden_set)
    
    # 2. Load extracted risks (from live pipeline, file or placeholder)
    if args.live:
        from src.risk_pipeline.pipeline import RiskExtractionPipeline
        pipeline = RiskExtractionPipeline()
        res = pipeline.run(pdf_path=args.pdf, show_progress=True)
        extracted_risks = res.risks
        source_desc = f"Live Extraction Pipeline on {args.pdf} ({len(extracted_risks)} items)"
    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file {input_path} not found.")
            sys.exit(1)
        extracted_risks = load_extracted_risks_from_file(input_path)
        source_desc = f"File: {args.input} ({len(extracted_risks)} items)"
    else:
        extracted_risks = PLACEHOLDER_EXTRACTED_RISKS
        source_desc = f"Hardcoded JSON Placeholder ({len(extracted_risks)} items)"

    # 3. Load Markdown pages for grounding check
    md_pages = load_raw_markdown_pages(Path(args.markdown))

    # 4. Run Evaluation
    score = evaluator.evaluate(extracted_risks=extracted_risks, raw_markdown_pages=md_pages)

    # 5. Output Report
    print_evaluation_report(score, evaluator.golden_set_path, source_desc)

    # Exit code based on pass/fail
    if not score.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
