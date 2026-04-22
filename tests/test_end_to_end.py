from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable when tests run from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from classifier import TicketClassifier, result_to_dict as classifier_result_to_dict
from escalation import EscalationEngine, result_to_dict as escalation_result_to_dict
from evaluator import SupportEvaluator, result_to_dict as evaluator_result_to_dict
from metrics import MetricsCalculator
from responder import SupportResponder, result_to_dict as responder_result_to_dict
from retriever import KnowledgeBaseRetriever, result_to_dict as retriever_result_to_dict
from ticket_loader import TicketLoader


def test_end_to_end_pipeline_runs_on_eval_tickets() -> None:
    loader = TicketLoader()
    classifier = TicketClassifier()
    retriever = KnowledgeBaseRetriever()
    responder = SupportResponder()
    escalation_engine = EscalationEngine()
    evaluator = SupportEvaluator()
    metrics_calculator = MetricsCalculator()

    eval_tickets = loader.load_eval_tickets()

    assert len(eval_tickets) > 0

    classification_results = []
    retrieval_results = []
    response_results = []
    escalation_results = []

    for ticket in eval_tickets:
        classification = classifier.classify(ticket)
        classification_dict = classifier_result_to_dict(classification)
        classification_results.append(classification_dict)

        retrieval = retriever.retrieve(
            ticket,
            predicted_category=classification_dict["category"],
        )
        retrieval_dict = retriever_result_to_dict(retrieval)
        retrieval_results.append(retrieval_dict)

        response = responder.respond(
            ticket=ticket,
            article_id=str(retrieval_dict["article_id"]),
            article_file=str(retrieval_dict["article_file"]),
            category=str(classification_dict["category"]),
            severity=str(classification_dict["severity"]),
            resolution_path=str(classification_dict["resolution_path"]),
        )
        response_dict = responder_result_to_dict(response)
        response_results.append(response_dict)

        escalation = escalation_engine.evaluate(
            ticket=ticket,
            category=str(classification_dict["category"]),
            severity=str(classification_dict["severity"]),
            resolution_path=str(classification_dict["resolution_path"]),
            article_id=str(retrieval_dict["article_id"]),
            responder_escalation_recommended=bool(
                response_dict["escalation_recommended"]
            ),
        )
        escalation_dict = escalation_result_to_dict(escalation)
        escalation_results.append(escalation_dict)

    evaluation_objects = evaluator.evaluate_many(
        tickets=eval_tickets,
        classification_results=classification_results,
        retrieval_results=retrieval_results,
        response_results=response_results,
        escalation_results=escalation_results,
    )
    evaluation_results = [
        evaluator_result_to_dict(result) for result in evaluation_objects
    ]

    metrics_summary = metrics_calculator.summarize(
        tickets=eval_tickets,
        evaluation_results=evaluation_results,
        classification_results=classification_results,
        escalation_results=escalation_results,
    )

    assert len(classification_results) == len(eval_tickets)
    assert len(retrieval_results) == len(eval_tickets)
    assert len(response_results) == len(eval_tickets)
    assert len(escalation_results) == len(eval_tickets)
    assert len(evaluation_results) == len(eval_tickets)

    for result in classification_results:
        assert "ticket_id" in result
        assert "category" in result
        assert "severity" in result
        assert "resolution_path" in result

    for result in retrieval_results:
        assert "ticket_id" in result
        assert "article_id" in result
        assert "confidence" in result

    for result in response_results:
        assert "ticket_id" in result
        assert "response_text" in result
        assert isinstance(result["response_text"], str)
        assert len(result["response_text"]) > 0

    for result in escalation_results:
        assert "ticket_id" in result
        assert "escalation_required" in result
        assert "escalation_type" in result

    for result in evaluation_results:
        assert "ticket_id" in result
        assert "overall_pass" in result
        assert "notes" in result

    assert "total_tickets" in metrics_summary
    assert metrics_summary["total_tickets"] == len(eval_tickets)

    assert "classification_accuracy" in metrics_summary
    assert "retrieval_accuracy" in metrics_summary
    assert "response_grounded_rate" in metrics_summary
    assert "overall_pass_rate" in metrics_summary
    assert "escalation_rate" in metrics_summary
    assert "false_resolution_rate" in metrics_summary
    assert "category_breakdown" in metrics_summary