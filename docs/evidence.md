# Failure Analysis

## Initial System Behavior
The system achieved perfect accuracy on structured evaluation tickets:
- Classification: 100%
- Retrieval: 100%
- Pass Rate: 100%

However, this performance was limited to well-defined, predictable inputs.

## Introduced Imperfection
Additional tickets were introduced to simulate real-world ambiguity:
- unclear user intent
- inconsistent issue behavior
- overlapping categories

## Observed Behavior
- classification confidence dropped on ambiguous tickets
- some cases shifted from kb_resolvable → partial_or_escalate
- escalation decisions became more conservative

## Key Insight
High performance on clean data does not guarantee real-world reliability.

The system must handle:
- incomplete information
- conflicting signals
- uncertain categorization

## Improvements Identified
- refine classification thresholds
- improve ambiguity detection
- enhance escalation decision logic

## Takeaway
This project demonstrates not just system design, but iterative improvement based on failure analysis — a critical requirement for production AI systems.