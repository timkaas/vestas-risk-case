1.
Bootstrapping Strategy:
◦
"We generated candidate extractions using gpt-4o with structured outputs, then performed human verification against the source PDF to validate risk categorization, page references, and mitigation existence."
2.
Preventing Circular Evaluation:
◦
Explain that you didn't just test gpt-4o against gpt-4o verbatim output. By human-verifying the items, setting keyword matches, and defining explicit flags (has_mitigation: true/false), the golden set acts as an objective test suite.
3.
Regression Testing:
◦
You can now run a weaker model (gpt-4o-mini), a modified prompt (e.g. omitting mitigations), or an altered chunker against this golden set to show that your evaluator successfully flags drops in recall and category accuracy.