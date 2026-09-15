Before you write code, write a short PLAN.md (~½ page). Situate this single-report pipeline inside the
broader product:
• Who is the user, and how will they consume the output?
We might have two users
- The analysts for ingesting reports and do final evaluation/signoff
- The end-user (asset-manager, compliance-teams)

As we are building a small part of the product, we will focus on the poor developer that 
will need to eventually integrate our solution.

• Roughly what does the product surface look like (batch API, interactive UI, alerting, …)?
- Have an alert at each report have the report not been verified by an analyst yet. This can also be used for finetuning, 
- Alert when a report has been ingested but not yet verified by an analyst

• What are you optimizing for in this first slice: correctness, coverage, cost, throughput?
Correctness! Solution can be incomplete, but it should be correct. Can be optimized for cost and throughput later when we have POC.

• What assumptions are you making?
- Ingested reports contain no PII/GDPR
Given the exapmles of queries:
>"What are the top enterprise risks facing Vestas, and how frequently are they reviewed at
Board/Executive level?” \
> "What emerging risks have been newly elevated?" \
> “Show me every renewable-energy company that lists cyber security as a principal risk"

This might suggest a RAG system, but at the same time our job is to build a structured database.

• What are you explicitly not solving here but would tackle next?
Deployment, scalability, security (wrt PII/GDPR) the query system.
