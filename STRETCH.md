# If I had another week

### Somewhat prioritized:

- Expand on the golden set to include all risks in the report, catching hallucinations, 
and allowing for a precision metric.

- Use llm-as-a-judge for extracted risks for a semantic comparison with the golden set.

- Proper regression run comparison report of extracted risks with the golden set for 
different prompts, models, etc.  

- Further refinement of the pdf-parsing with automatic extraction of risk sections. A 
simple heuristic to identify risk sections could be enough and further refinement e.g., sentence 
segmentation for filtering for relevant segments for llm-processing.

- Finish, test, and evaluate on a document splitting strategy (currently unused – can 
be found in the prototyping-notebook, possibly solving a `lost-in-the-middle` where 
we see some manually identified risks are not being extracted. Alternatively, or 
combined with a sentence segmentation strategy for further refinement.

- Develop a strategy for deduplication. Use a small embedding model for comparing extracted 
risks could be used. The embedding model could further be used to do a grounding check on 
the extracted risks.

- The current solution is blunt in its approach using a llm (decoder/generator) as a 
feature extractor, with no repercussion for hallucination. Given the quality of todays 
llm, I think this serves as a good starting point for a POC, but I would definitely look 
into encoding models for e.g. NER.

### Further down the line:

- Implement explicit human-in-the-loop review of extracted risks for quality control,
and potential future improvements to both the parsing and the extraction step.

- Distill/fine-tune the extraction task into a compact, fine-tuned model, further
reducing inference costs while maintaining deterministic outputs – this is where the 
fun begins.
