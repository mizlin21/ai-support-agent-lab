# Architecture Overview


AI Support Agent Lab is a simulated SaaS support environment designed to model how AI agents can participate in real support operations while preserving clear escalation paths, measurable quality controls, and continuous improvement loops.


The system is intentionally built as a modular pipeline. Each stage has a defined responsibility, produces structured outputs, and can be evaluated independently. This design supports both technical experimentation and operational reasoning.


---


## System Goal


The goal of this project is to simulate a production-style support workflow where an AI agent can:


- classify incoming support tickets
- retrieve the most relevant knowledge base content
- generate grounded support responses
- decide when a case should be escalated
- produce structured defect triage outputs
- measure performance across key support and automation metrics
- improve over time through failure analysis and iteration


This project is not designed as a generic chatbot. It is designed as a support system with defined boundaries, operational logic, and measurable outcomes.


---


## Simulated Product Environment


The simulated SaaS platform in this project is a quoting and workflow application used by sales and operations teams to manage client records, pricing workflows, document exports, reporting, and CRM synchronization.


Example support scenarios include:


- login and password reset issues
- permission and role-access problems
- quote export failures
- report timeout and slow-loading issues
- CRM sync delays or missing updates
- browser cache or UI rendering problems


These ticket categories were chosen because they reflect common, repeatable SaaS support patterns while still requiring judgment around escalation, defect triage, and resolution quality.


---


## Design Principles


The architecture is built around five principles.


### 1. Grounded Resolution
Agent responses should be based on available knowledge base content rather than unsupported guesses.


### 2. Clear Escalation Boundaries
The system should recognize when a ticket is not safely auto-resolvable and route it for human or engineering review.


### 3. Structured Outputs
Each stage should produce outputs that are inspectable, testable, and reusable in later stages.


### 4. Evaluation as a First-Class Component
System quality is not assumed. It is measured through retrieval accuracy, classification accuracy, escalation correctness, and resolution outcomes.


### 5. Continuous Improvement
Failures are treated as useful signals. The system should support iterative improvement through prompt changes, KB changes, and logic refinement.


---


## High-Level Pipeline


The system follows this flow:


```text
Support Ticket
    ↓
Ticket Loader
    ↓
Classifier
    ↓
Knowledge Base Retriever
    ↓
Response Generator
    ↓
Escalation Decision
    ↓
Evaluator
    ↓
Metrics + Failure Analysis
```


Each stage is intentionally separated so that logic can be inspected and improved without treating the system as a black box.


In implementation, these stages are orchestrated as a sequential pipeline so that ticket handling, evaluation, and metrics generation can be executed consistently across the dataset.


## Component Breakdown


### 1. Ticket Loader


**File:** `src/ticket_loader.py`


The ticket loader is responsible for reading support ticket data from JSON files and preparing those records for downstream processing.


#### Responsibilities


- load raw and evaluation ticket datasets  
- validate required ticket fields  
- normalize ticket structure for pipeline use  
- provide consistent input objects to the rest of the system  


#### Example Ticket Fields


- `ticket_id`  
- `subject`  
- `customer_message`  
- `expected_category`  
- `expected_resolution_type`  
- `expected_kb_article`  
- `expected_escalation_behavior`  


This stage ensures that support tickets are treated as structured operational inputs rather than unstructured text, enabling consistent and reliable processing across the pipeline.


### 2. Classifier


**File:** `src/classifier.py`


The classifier assigns an initial interpretation to each incoming ticket, enabling downstream routing and decision-making.


#### Inputs


- `ticket_id`  
- `subject`  
- `customer_message`  


#### Outputs


- `predicted_category`  
- `severity`  
- `handling_path`  
- `confidence_score`  


#### Example Handling Paths


- `kb_resolvable`  
- `partially_resolvable`  
- `escalate`  


#### Responsibilities


- predict ticket category  
- estimate severity level  
- recommend a handling path  


#### Example Categories


- `login_access`  
- `permissions`  
- `quote_export`  
- `crm_sync`  
- `browser_ui`  
- `report_timeout`  


The initial implementation may use rule-based keyword matching for transparency and control. Future iterations may incorporate prompt-driven or model-assisted classification to improve flexibility and accuracy.


The purpose of this stage extends beyond categorization—it enables operational routing decisions that determine how each ticket is handled within the system.


### 3. Knowledge Base Retriever


**File:** `src/retriever.py`


The retriever identifies the most relevant knowledge base (KB) article for a given ticket.


#### Responsibilities


- match ticket symptoms to KB articles  
- rank candidate articles using category, keyword, and tag overlap  
- return the best-matching article along with a retrieval confidence score  


Knowledge base structure and metadata are as important as retrieval logic. Poorly organized or insufficiently tagged KB content will degrade system performance, even with strong downstream components.


This stage reflects a core reality of support systems: retrieval quality directly determines resolution quality.


### 4. Response Generator


**File:** `src/responder.py`


The response generator creates a draft support reply using the selected knowledge base (KB) article and the ticket context.


#### Responsibilities


- acknowledge the user’s issue  
- explain likely causes when supported by the KB  
- provide clear, step-by-step resolution guidance  
- remain grounded in retrieved knowledge  
- avoid unsupported or speculative troubleshooting steps  


The response layer should behave like a careful support operator: structured, professional, and constrained by known information.


#### Desired Qualities


- clear  
- actionable  
- professional  
- concise  
- grounded  


This stage simulates the type of response a support agent would deliver when an issue can be safely resolved using existing documentation.


### 5. Escalation Decision Layer


**File:** `src/escalation.py`


Not all tickets should be auto-resolved. The escalation layer identifies cases that require human intervention or engineering review.


#### Responsibilities


- determine whether a ticket should be escalated  
- distinguish between support follow-up and engineering/QA defect escalation  
- generate structured defect reports when escalation is required  


#### Escalation Triggers


- no strong knowledge base (KB) match  
- high-severity or ambiguous symptoms  
- repeated failures after known troubleshooting steps  
- multi-user or cross-browser issues  
- behavior consistent with potential product defects  


This stage is critical for safe automation: system reliability depends not only on what is resolved automatically, but also on correctly identifying when not to auto-resolve.


### 6. Evaluator


**File:** `src/evaluator.py`


The evaluator compares system behavior against predefined expected outcomes to assess correctness, safety, and overall performance.


#### Responsibilities


- validate category prediction correctness  
- validate knowledge base (KB) retrieval accuracy  
- verify that responses remain grounded in retrieved knowledge  
- evaluate escalation decision correctness  
- determine overall pass/fail for each evaluated ticket  


#### Evaluation Dimensions


- `category_correct`  
- `retrieval_correct`  
- `response_grounded`  
- `escalation_correct`  
- `overall_pass`  


The evaluator transforms the system from a prototype into a measurable, testable support automation pipeline by enforcing objective evaluation criteria.


### 7. Metrics Layer


**File:** `src/metrics.py`


The metrics layer aggregates results across evaluation tickets and provides a high-level view of system performance.


#### Responsibilities


- compute classification accuracy  
- compute retrieval accuracy  
- compute auto-resolution rate  
- compute escalation rate  
- compute false-resolution rate  
- summarize performance by ticket category  


#### Example Outputs


- total tickets evaluated  
- percentage correctly classified  
- percentage correctly retrieved  
- percentage safely auto-resolved  
- percentage incorrectly resolved without escalation  


This stage aligns the project with production support practices, where system performance must be quantified through clear, operationally meaningful metrics.


### 8. Continuous Improvement Loop


This is a core architectural component of the system.


The pipeline is not considered complete after generating a response. Instead, each failure is treated as a signal that feeds a loop of analysis and iterative improvement.


#### Common Failure Sources


- incorrect category prediction  
- insufficient knowledge base (KB) coverage  
- poor article structure or tagging  
- overly broad or inaccurate escalation rules  
- insufficient response grounding  
- missing edge-case handling  


#### Improvement Actions


- updating ticket classification logic or rules  
- improving KB article structure, tagging, or coverage  
- refining response prompts or generation logic  
- adjusting escalation thresholds and decision criteria  
- expanding the evaluation dataset with new scenarios  


This feedback loop transforms the system from a static prototype into a continuously improving support automation platform, aligning with real-world support operations where performance is iteratively refined over time.


## Data Model Overview


The project uses structured JSON and Markdown files to ensure transparency, traceability, and ease of inspection across all stages of the system.


### Ticket Data


Stored in:


- `data/tickets/raw_tickets.json`  
- `data/tickets/eval_tickets.json`  
- `data/tickets/expected_outcomes.json`  


### Knowledge Base


Stored in:


- `data/kb/articles/*.md`  
- `data/kb/kb_index.json`  


### Defect Templates


Stored in:


- `data/defects/defect_templates.json`  


### Output Artifacts


Stored in:


- `data/outputs/`  


This file-based design supports straightforward testing, version control, and reproducibility, while allowing each stage of the pipeline to be independently inspected and validated.


## Output Types


The system is designed to generate several structured output types that support decision-making, evaluation, and system improvement.


### 1. Resolution Output


A structured representation of the system’s decision for tickets that are auto-resolved:


- predicted category  
- selected knowledge base (KB) article  
- drafted support response  
- resolution status  


### 2. Escalation Output


Generated when a ticket cannot be safely auto-resolved:


- escalation type (e.g., support follow-up, engineering defect)  
- summary of the issue  
- suspected product area  
- reproduction steps (if identifiable)  
- evidence requested from the user  


### 3. Evaluation Output


Per-ticket scoring used to assess system performance:


- category correctness  
- retrieval correctness  
- response grounding check  
- escalation correctness  


### 4. Metrics Summary


An aggregated view of system performance across the evaluation set.


Example contents may include:


- total tickets evaluated  
- classification accuracy  
- retrieval accuracy  
- auto-resolution rate  
- escalation rate  
- false-resolution rate  


These outputs support both engineering-style review and support operations analysis.


## Example End-to-End Flow


A simplified example:


1. A ticket arrives reporting that quote export to PDF does nothing.  
2. The classifier predicts `quote_export` with medium severity.  
3. The retriever selects the `quote_export_issue.md` knowledge base article.  
4. The responder drafts a KB-grounded reply with browser, cache, and pop-up blocker troubleshooting steps.  
5. The escalation layer evaluates whether the issue is safely resolvable or indicative of a broader defect.  
6. The evaluator compares system behavior against the expected outcome for the ticket.  
7. Metrics are updated to reflect whether the pipeline handled the ticket correctly.  


This flow mirrors real support operations, where each decision directly impacts both customer experience and support efficiency.


## Why This Architecture Matters


Many AI support prototypes stop at simply generating an answer. That approach is insufficient for production-oriented support systems.


This architecture addresses the broader operational problem by modeling:


- how tickets are routed  
- how knowledge is retrieved  
- how responses are constrained and grounded  
- how uncertainty is identified and handled  
- how defects are escalated appropriately  
- how performance is measured through defined metrics  
- how failures drive continuous system improvement  


This is the difference between a basic AI demo and a structured, production-oriented AI support system.


## Current Scope


The initial version of this project focuses on:


- simulated SaaS support ticket workflows  
- structured knowledge base (KB) retrieval  
- deterministic or prompt-guided response generation  
- explicit escalation and defect triage logic  
- evaluation pipelines with measurable metrics  
- documented failure analysis for continuous improvement  


## Future Scope


Future iterations of this project may extend to:


- model-assisted or hybrid classification approaches  
- more advanced retrieval methods (e.g., semantic search, embeddings)  
- mock Zendesk-style import/export formats for realism  
- dashboarding and visualization of support metrics  
- comparative testing across multiple prompts, policies, or agent strategies  


## Summary


AI Support Agent Lab is a modular, measurable support automation system designed to simulate real-world SaaS support operations—not a generic conversational chatbot.


The architecture is built around a practical operational question:


**How can AI handle repeatable support work safely, measurably, and within clearly defined boundaries?**


This project answers that question by combining:


- structured support workflow simulation  
- knowledge base–driven retrieval and resolution  
- explicit escalation and defect triage logic  
- evaluation pipelines with measurable outcomes  
- a continuous improvement loop driven by failure analysis  


The result is a system that models how AI can augment support operations while maintaining control, transparency, and reliability.
