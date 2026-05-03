# Demo Walkthrough: AI Support Agent Lab

This walkthrough demonstrates how the AI Support Agent Lab processes support tickets end-to-end, from ingestion to evaluation.

---

## Overview

The system simulates a SaaS support workflow where an AI agent:

1. classifies incoming tickets  
2. retrieves the most relevant knowledge base article  
3. generates a grounded response  
4. decides whether to escalate  
5. evaluates its own performance  

All outputs are structured and saved for inspection.

---

## How to Run the System

From the project root:

```bash
python src/main.py
```

## Pipeline Execution Flow

### 1. Ticket Loading

Source:

`data/tickets/eval_tickets.json`

Tickets are:
- validated
- normalized
- prepared for processing

### 2. Classification

File:

`src/classifier.py`

The system predicts:
- category (e.g., quote_export, login_access)
- severity (low, medium, high)
- resolution path:
    - `kb_resolvable`
    - `partial_or_escalate`
    - `escalate`

### 3. Knowledge Base Retrieval

File:

`src/retriever.py`

The system:
- matches ticket text against KB tags
- uses category boosting
- selects the most relevant article

Example:
```text
Ticket: "Export to PDF not working"
→ Article: quote_export_issue.md
```

### 4. Response Generation

File:

`src/responder.py`

The system:
- extracts structured steps from KB articles
- generates a professional support reply
- ensures responses are grounded in known information

### 5. Escalation Decision

File:

`src/escalation.py`

The system determines:
- whether escalation is required
- escalation type:
    - support follow-up
    - engineering defect

### 6. Evaluation

File:

`src/evaluator.py`

Each ticket is evaluated on:
- category correctness
- retrieval correctness
- response grounding
- escalation correctness
- overall pass/fail

### 7. Metrics

File:

`src/metrics.py`

Aggregated metrics include:
- classification accuracy
- retrieval accuracy
- response grounded rate
- escalation rate
- false resolution rate
- overall pass rate

## Example Output

After running the system:
```text
=== AI Support Agent Lab Metrics Summary ===

Total tickets evaluated: 7
Classification accuracy: 1.0
Retrieval accuracy: 1.0
Response grounded rate: 1.0
Overall pass rate: 0.71
Escalation rate: 0.29
False resolution rate: 0.0
```
## Output Files

Generated in:

`data/outputs/`

Includes:

- `classification_results.json`
- `retrieval_results.json`
- `response_results.json`
- `escalation_results.json`
- `evaluation_results.json`
- `metrics_summary.json`

## Key Insight

The system performs perfectly on structured inputs but shows reduced pass rate when ambiguity is introduced.

This demonstrates:
- the importance of evaluation frameworks
- the need for failure analysis
- the challenge of handling real-world uncertainty

## What This Demo Shows

This project demonstrates:
- end-to-end AI workflow design
- structured reasoning pipelines
- grounded response generation
- escalation safety mechanisms
- evaluation-driven system improvement

## Next Steps

Future improvements include:
- handling more ambiguous ticket patterns
- refining escalation thresholds
- improving classification confidence scoring
- expanding knowledge base coverage