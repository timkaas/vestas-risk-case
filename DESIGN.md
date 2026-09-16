# Design

## Stack

- **PDF parsing:** `PyMuPDF` + `pymupdf4llm` — Markdown output is preferable to plain text as several disclosures are table-shaped, and page numbers are preserved for traceability.
- **Extraction:** LangChain + OpenAI `gpt-4o` (`temperature=0`) with structured output bound to a Pydantic schema, giving deterministic, schema-valid results without post-processing.
- **Eval:** Hand-curated golden set + keyword/page-based matcher + quote grounding check. A pytest regression suite applies deterministic degradations to verify the evaluator catches real failure modes without LLM calls.

## Pipeline decomposition

```
PDF + section config 
└─► Parse target pages → Markdown (per page, with page-number tags) 
    └─► LLM extraction per section (concurrent, structured output) 
        └─► Deduplicate across sections (normalised title + section key) 
            └─► Write JSON / evaluate against golden set
```

Splitting parsing from extraction was a deliberate choice: it keeps the two failure modes (bad text, bad extraction) separately observable and testable, and lets sections be extracted in parallel.

## Why LLM-only extraction (for now)

A decoder LLM with structured output handles the full extraction task — entity recognition, classification, summarisation, and mitigation identification — in a single pass. For a POC on dense financial prose, this is the fastest path to useful recall. The cost is that there is no repercussion for hallucination; the grounding check in the evaluator is the current guard. A hybrid approach (sentence segmentation as a pre-filter, encoder-based NER as a post-validation signal) is the natural next step and is noted in STRETCH.md.

## Key trade-offs

| Decision | Benefit | Cost |
|---|---|---|
| Manually configured section page ranges | Cheap, inspectable, no layout ML needed | Requires per-report configuration; misses risks disclosed elsewhere |
| One LLM call per section (not per page) | Fewer calls, cross-page context preserved | Risk of lost-in-the-middle on long sections |
| Title + section deduplication | Simple, zero cost | Misses semantic duplicates with different wording |
| Keyword-based golden set matcher | No LLM needed in eval | Brittle on paraphrase; not a substitute for semantic similarity |

## Scaling considerations

At 200 reports per quarter, the per-report cost and latency are the main levers. Concurrency across sections already helps; the larger gains come from:
1. a pre-filter that reduces tokens sent to the LLM, and 
2. distilling the extraction task into a smaller, fine-tuned model. 
 
Storing report, sections, and risks separately in a database enables incremental re-extraction when only a section or model changes, without reprocessing the full document.