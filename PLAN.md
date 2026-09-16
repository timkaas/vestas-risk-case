# Plan

Considering that we are joining a team at a research firm, and given the case
task of building a structured database, I will assume that the initial user 
of our pipeline is colleagues within the research firm.

The final goal of querying this database using natural language is considered a 
future feature – which would probably include again semantic understanding and 
automatic database query construction.

Considering the number of reports an analyst needs to review (~200 a quarter), the
product should expose a batch API. However, this is also considered a future feature,
and the initial focus will be on building a CLI for the extraction process for the 
provided report.

I consider the correctness and traceability of the extracted data to be the highest 
priority. While a generic llm (decoder) is not really intended for quote extraction 
and explainability, it will be a good starting point for this task, making a POC. A 
future version will likely use a more specialized model (encoder) that allows for 
token-extraction, explainability, and confidence estimation.

Given the limited amount of data, the golden set of test cases will be small. While 
the golden set will be curated, its size and quality (mostly given that I'm not a 
research analyst) will be limited. Evaluation of the golden set should include a 
content comparison and semantic similarity – again using a llm-as-a-judge. This 
is considered a future feature, and for now we will rely on simple keyword matching
and quote search/comparison.

Due to the complexity of the provided PDF, exact sections (with relevant naming) will
be extracted manually (as suggested in the case). In a future version, more effort 
should be put into parsing and extracting/understanding graphs/tables/layout and 
(using the TOC) sections.