# Vestas Structured Risk Intelligence Pipeline

## 🚀 Quickstart & Setup

### 1. Prerequisites & Environment
Ensure Python 3.14+ is installed.:

```bash
# Clone and enter the repository
cd vestas-risk-case

# Install dependencies (using uv)
uv sync
```

Create a `.env` file in the project root:
```bash
OPENAI_API_KEY="your-openai-api-key-here"
```

The notebook extperiments with sentence segmentation. Install the spaCy model using if you want to continue those experiments.
```bash
uv run python -m spacy download en_core_web_sm
```

---

## 🛠️ Usage

### 1. Run the Risk Extraction Pipeline
Extract structured risks from the Vestas Annual Report PDF:
```bash
# Run extraction with default settings (outputs markdown summary to console)
uv run main.py

# With extracted risks saved to file and evaluation report to console
uv run main.py --output ./eval/extracted_risks2.json --eval

# For a local PDF-file (default is `data/VestasAnnualReport2025.pdf`). 
# Note that the report must be accompanied by a report definition JSON file (see data/vestas-report.json)
uv run main.py --pdf ./path/to/local/report.pdf -input ./path/to/local/report.json
```

#### CLI Options
| Flag                  | Description                                            | Default                           |
|:----------------------|:-------------------------------------------------------|:----------------------------------|
| `--pdf`, `-p`         | Path to annual report PDF                              | `data/VestasAnnualReport2025.pdf` |
| `--input`, `-i`       | Path to report definition JSON                         | `data/vestas-report.json`         |
| `--output`, `-o`      | Output file path (`.json`)                             | Print to console                  |
| `--model`, `-m`       | OpenAI model identifier                                | `gpt-4o`                          |
| `--temperature`, `-t` | Sampling temperature                                   | `0.0`                             |
| `--eval`, `-e`        | Run evaluation against golden dataset after extraction | `False`                           |

---

### 2. Run Golden Dataset Evaluation
Evaluate existing extraction results against the curated golden dataset:

```bash
uv run ./run_eval.py --output ./eval/runs/baseline-report.txt
uv run ./run_eval.py --output ./eval/runs/gpt-41-nano-report.txt --model gpt-4.1-nano-2025-04-14
uv run ./run_eval.py --output ./eval/runs/gpt-41-mini-report.txt --model gpt-4.1-mini-2025-04-14
uv run ./run_eval.py --output ./eval/runs/temp-1-report.txt --temperature 1

# Run an evaluation on an existing extraction result
uv run ./run_eval.py --results ./eval/runs/report.txt
```
---

### 3. Run the Regression Testing Suite
Demonstrates the evaluation harness detecting realistic degradation modes:

```bash
uv run pytest src/eval/test_regression.py
```