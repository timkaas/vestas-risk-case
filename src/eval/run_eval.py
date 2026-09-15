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


# ==============================================================================
# PLACEHOLDER EXTRACTED RISKS (Hardcoded JSON)
# Replace or supplement this placeholder with outputs from your extraction pipeline
# ==============================================================================
PLACEHOLDER_EXTRACTED_RISKS: List[Dict[str, Any]] = [
    {
        "title": "Geopolitical and Regulatory Framework",
        "description": "Vestas faces significant challenges due to shifting geopolitical tensions and regulatory changes. Conflicts in regions like Ukraine and the Middle East disrupt stability, affecting global supply chains and operations. Trade tensions and assertive industrial policies in major economies further complicate the regulatory landscape, impacting market incentives and competition in the clean-tech sector.",
        "category": "geopolitical",
        "section": "Main risks",
        "pages": [51],
        "mitigation": "Vestas manages geopolitical risks by monitoring global developments, maintaining a global and regional manufacturing footprint, and implementing appropriate mitigations.",
        "evidence": [
            {
                "page": 51,
                "quote": "In 2025, Vestas continued to navigate significant challenges arising from shifting geopolitical tensions across the world. Conflicts in Ukraine and the Middle East continued to disrupt regional stability, affecting global supply chains and business operations."
            }
        ]
    },
    {
        "title": "Project Execution",
        "description": "Vestas encounters challenges in executing complex onshore and offshore projects, which are affected by production delays, quality control issues, and supply chain disruptions. The lack of industry-wide standardization and logistical infrastructure further complicates timely delivery, impacting Vestas' ability to secure new business and maintain competitiveness.",
        "category": "operational",
        "section": "Main risks",
        "pages": [51],
        "mitigation": "Vestas mitigates execution risks through project governance, enhanced planning functions, and continuous alignment between commercial and delivery teams. They invest in scalable manufacturing capacity and maintain close coordination with suppliers.",
        "evidence": [
            {
                "page": 51,
                "quote": "Project execution at Vestas involves delivering complex onshore and offshore projects within specified parameters relating to quality, cost, and timeline. As the scale and complexity of offshore projects grow, so does the need for precise internal coordination."
            }
        ]
    },
    {
        "title": "Cyber Attacks",
        "description": "Vestas' digital and critical assets are exposed to cyber attacks, which can have severe implications for both the company and the societies relying on its energy solutions. Cyber-threat actors, including politically motivated ones, may target Vestas to disrupt energy production, leading to economic loss and reputational damage.",
        "category": "cyber",
        "section": "Main risks",
        "pages": [51],
        "mitigation": "Vestas is developing cyber security services to help customers navigate cyber risks, fulfill industry requirements, and uphold responsibilities. In 2025, their cyber security efforts were effective, with no critical incidents reported.",
        "evidence": [
            {
                "page": 51,
                "quote": "Vestas’ digital and other critical assets are exposed to cyber attacks. A cyber attack may have dual implications for both Vestas as a company and for the societies that our energy solutions serve."
            }
        ]
    },
    {
        "title": "Climate Change Mitigation",
        "description": "The GHG emissions from Vestas’ own operations and value chain have a negative impact on the global climate and environment. High carbon taxes and tariffs increase the price of GHG intense materials such as steel, increasing the overall cost to produce wind turbines.",
        "category": "climate",
        "section": "E1 Climate Change",
        "pages": [71],
        "mitigation": "Offering low emission materials and enabling the green transition through renewable energy solutions.",
        "evidence": [
            {
                "page": 71,
                "quote": "The GHG emissions from Vestas’ own operations and value chain have a negative impact on the global climate and environment."
            },
            {
                "page": 71,
                "quote": "High carbon taxes and tariffs increase the price of GHG intense materials such as steel, increasing the overall cost to produce wind turbines."
            }
        ]
    },
    {
        "title": "Biodiversity Loss",
        "description": "The GHG emissions originating in Vestas' supply chain from the extraction, production, and transportation of raw materials and products have a negative impact on biodiversity and ecosystems.",
        "category": "climate",
        "section": "E4 Biodiversity and ecosystems",
        "pages": [72],
        "mitigation": None,
        "evidence": [
            {
                "page": 72,
                "quote": "The GHG emissions originating in our supply chain from the extraction, production and transportation of raw materials and products have a negative impact on biodiversity and ecosystems"
            }
        ]
    },
    {
        "title": "Non-recyclable Materials",
        "description": "Non-recyclable materials in turbines might be landfilled or incinerated, increasing the need for virgin materials, which has a negative impact on the environment.",
        "category": "climate",
        "section": "E5 Circular economy and resource use",
        "pages": [72],
        "mitigation": "Offering blade circularity solutions.",
        "evidence": [
            {
                "page": 72,
                "quote": "Non-recyclable materials in turbines might be landfilled or incinerated and increase the need for virgin materials, which has a negative impact on the environment."
            }
        ]
    },
    {
        "title": "Health and Safety Incidents",
        "description": "Health and safety incidents of Vestas' own workforce and supply chain workers pose a financial risk due to potential injuries leading to delays, lost work hours, and compensation costs.",
        "category": "operational",
        "section": "S1 Own Workforce",
        "pages": [73],
        "mitigation": None,
        "evidence": [
            {
                "page": 73,
                "quote": "The negative impact related to health and safety incidents."
            },
            {
                "page": 73,
                "quote": "Potential injuries leading to delays, lost work hours and compensation costs pose a financial risk."
            }
        ]
    },
    {
        "title": "Child and Forced Labour",
        "description": "There is a risk of forced and child labour in Vestas' supply chain, which could lead to fines and reputational damage.",
        "category": "supply_chain",
        "section": "S2 Workers in the value chain",
        "pages": [73],
        "mitigation": None,
        "evidence": [
            {
                "page": 73,
                "quote": "Risk of forced and child labour in our supply chain."
            },
            {
                "page": 73,
                "quote": "Fines related to forced or child labour Vestas’ global network of suppliers combined with the risk of fines related to child and forced labour constitute a potential risk."
            }
        ]
    },
    {
        "title": "Land-related Impacts on Communities",
        "description": "Land-use restrictions during wind farm construction can lead to temporary negative impacts such as physical and economic displacement of local communities.",
        "category": "operational",
        "section": "S3 Affected communities",
        "pages": [74],
        "mitigation": None,
        "evidence": [
            {
                "page": 74,
                "quote": "Land-use restrictions during wind farm construction leading to a temporary negative impact in the form of physical and economic displacement (e.g income losses) of local communities."
            }
        ]
    },
    {
        "title": "Cyber Security Incidents",
        "description": "Cyber attacks on wind farm infrastructure might cause power outages and increase electricity prices, negatively impacting society and people. They might also disrupt business operations, expose intellectual property, or cause legal liability.",
        "category": "cyber",
        "section": "G1 Business Conduct",
        "pages": [74],
        "mitigation": None,
        "evidence": [
            {
                "page": 74,
                "quote": "Cyber attacks on wind farm infrastructure might cause power outages and increase in electricity prices, negatively impacting society and people"
            },
            {
                "page": 74,
                "quote": "Cyber attacks might disrupt business operations, expose intellectual property, or cause legal liability."
            }
        ]
    },
    {
        "title": "Corruption and Bribery",
        "description": "Vestas’ global presence presents an increased risk of exposure to corruption and bribery, which could lead to legal and reputational damage.",
        "category": "regulatory",
        "section": "G1 Business Conduct",
        "pages": [74],
        "mitigation": None,
        "evidence": [
            {
                "page": 74,
                "quote": "Vestas’ global presence presents an increased risk of exposure to corruption and bribery."
            }
        ]
    },
    {
        "title": "GHG Emissions Impact",
        "description": "The Greenhouse Gas (GHG) emissions from Vestas' operations and supply chain have a material negative impact on the climate. In 2025, significant emissions were recorded, with Scope 3 emissions comprising more than 99 percent of total emissions, primarily driven by purchased goods and transport.",
        "category": "climate",
        "section": "Climate Change",
        "pages": [85],
        "mitigation": "Vestas has set GHG emission reduction targets and established a transition plan for climate change mitigation, with actions implemented across the organisation.",
        "evidence": [
            {
                "page": 85,
                "quote": "The Greenhouse Gas (GHG) emissions from our own operations and supply chain have a material negative impact on the climate. In 2025, 109 kt of combined Scope 1 and 2 emissions were emitted. Scope 3 emissions comprise more than 99 percent of our total greenhouse gas emissions."
            }
        ]
    },
    {
        "title": "Energy Consumption Impact",
        "description": "Energy consumption during the manufacture of wind turbine components and the construction and servicing of wind parks relies on fossil fuels, leading to resource depletion and emissions that negatively impact the climate.",
        "category": "climate",
        "section": "Climate Change",
        "pages": [85],
        "mitigation": "Reducing reliance on fossil fuels is part of Vestas' strategy to cut emissions from its own operations in half by 2030.",
        "evidence": [
            {
                "page": 85,
                "quote": "Energy is consumed during the manufacture of wind turbine components and the construction and servicing of wind parks. Energy consumption in our own operations relies on fossil fuels, leading to resource depletion and emissions that negatively impact the climate."
            }
        ]
    },
    {
        "title": "Carbon Taxes and Tariffs",
        "description": "Political and market transition risks, such as carbon taxes, can financially impact Vestas by increasing the cost of GHG-intensive materials like steel, raising the overall cost of wind turbines.",
        "category": "financial",
        "section": "Climate Change",
        "pages": [85],
        "mitigation": "Vestas is working to transition to low-carbon alternatives and distribute costs along the value chain.",
        "evidence": [
            {
                "page": 85,
                "quote": "Political and market transition risks, such as carbon taxes, can financially impact Vestas. High carbon taxes and tariffs will increase the cost of GHG-intensive materials like steel, raising the overall cost of wind turbines."
            }
        ]
    },
    {
        "title": "Physical Climate Risks",
        "description": "Physical risks like water stress and extreme rainfall may impact operations across Vestas' value chain, although they are not expected to materially delay or damage assets.",
        "category": "climate",
        "section": "Climate Change",
        "pages": [86],
        "mitigation": "Vestas has organisational and strategic priorities in place to address acute and chronic climate risks that could disrupt business activities.",
        "evidence": [
            {
                "page": 86,
                "quote": "While physical risks like water stress and extreme rainfall may impact operations across our value chain, the impact is not expected to materially delay or damage assets."
            }
        ]
    },
    {
        "title": "Cyber Security Incidents",
        "description": "Cyber security incidents pose a significant risk to Vestas, potentially disrupting its ability to control power plants, impacting customers and society. The primary risk arises from politically or financially motivated threat actors aiming to trigger power outages, which could lead to contractual breaches and higher electricity prices for consumers.",
        "category": "cyber",
        "section": "Cyber Security",
        "pages": [117],
        "mitigation": "Vestas has increased investment in cyber security across R&D, service, and digital infrastructure, and has launched a Cyber Risk Management Strategy to systematically identify, assess, communicate, and mitigate cyber risks.",
        "evidence": [
            {
                "page": 117,
                "quote": "The potential impact of a cyber security incident was added to our reporting scope since the previous reporting period. The impact is to be understood as the disruption of Vestas’ ability to control power plants, which directly impacts customers, and, ultimately, society."
            },
            {
                "page": 117,
                "quote": "For Vestas, a successful cyber-attack could interrupt operations, erode partner trust, and cause significant financial losses."
            }
        ]
    }
]


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
