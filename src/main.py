from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from classifier import TicketClassifier, result_to_dict as classifier_result_to_dict
from escalation import EscalationEngine, result_to_dict as escalation_result_to_dict
from evaluator import SupportEvaluator, result_to_dict as evaluator_result_to_dict
from metrics import MetricsCalculator
from responder import SupportResponder, result_to_dict as responder_result_to_dict
from retriever import KnowledgeBaseRetriever, result_to_dict as retriever_result_to_dict
from ticket_loader import TicketLoader


OUTPUT_DIR = Path("data/outputs")


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_json(filename: str, data: Any) -> None:
    path = OUTPUT_DIR / filename
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def build_predicted_category_map(
    classification_results: List[Dict[str, Any]],
) -> Dict[str, str]:
    return {
        str(result.get("ticket_id", "UNKNOWN")): str(result.get("category", "unknown"))
        for result in classification_results
    }


def print_summary(metrics_summary: Dict[str, Any]) -> None:
    print("\n=== AI Support Agent Lab Metrics Summary ===")
    print(f"Total tickets evaluated: {metrics_summary['total_tickets']}")
    print(f"Classification accuracy: {metrics_summary['classification_accuracy']}")
    print(f"Retrieval accuracy: {metrics_summary['retrieval_accuracy']}")
    print(f"Response grounded rate: {metrics_summary['response_grounded_rate']}")
    print(f"Overall pass rate: {metrics_summary['overall_pass_rate']}")
    print(f"Escalation rate: {metrics_summary['escalation_rate']}")
    print(f"False resolution rate: {metrics_summary['false_resolution_rate']}")

    print("\nCategory breakdown:")
    for category, stats in metrics_summary["category_breakdown"].items():
        print(
            f"- {category}: total={stats['total']}, "
            f"pass_rate={stats['pass_rate']}, "
            f"classification_accuracy={stats['classification_accuracy']}, "
            f"retrieval_accuracy={stats['retrieval_accuracy']}"
        )


def run_pipeline() -> None:
    ensure_output_dir()

    loader = TicketLoader()
    classifier = TicketClassifier()
    retriever = KnowledgeBaseRetriever()
    responder = SupportResponder()
    escalation_engine = EscalationEngine()
    evaluator = SupportEvaluator()
    metrics_calculator = MetricsCalculator()

    eval_tickets = loader.load_eval_tickets()

    classification_results: List[Dict[str, Any]] = []
    retrieval_results: List[Dict[str, Any]] = []
    response_results: List[Dict[str, Any]] = []
    escalation_results: List[Dict[str, Any]] = []

    for ticket in eval_tickets:
        classification = classifier.classify(ticket)
        classification_dict = classifier_result_to_dict(classification)
        classification_results.append(classification_dict)

    predicted_categories = build_predicted_category_map(classification_results)

    for ticket in eval_tickets:
        ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
        predicted_category = predicted_categories.get(ticket_id, "unknown")

        retrieval = retriever.retrieve(ticket, predicted_category=predicted_category)
        retrieval_dict = retriever_result_to_dict(retrieval)
        retrieval_results.append(retrieval_dict)

    classification_map = {
        result["ticket_id"]: result for result in classification_results
    }
    retrieval_map = {
        result["ticket_id"]: result for result in retrieval_results
    }

    for ticket in eval_tickets:
        ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
        classification_result = classification_map[ticket_id]
        retrieval_result = retrieval_map[ticket_id]

        response = responder.respond(
            ticket=ticket,
            article_id=str(retrieval_result["article_id"]),
            article_file=str(retrieval_result["article_file"]),
            category=str(classification_result["category"]),
            severity=str(classification_result["severity"]),
            resolution_path=str(classification_result["resolution_path"]),
        )
        response_dict = responder_result_to_dict(response)
        response_results.append(response_dict)

        escalation = escalation_engine.evaluate(
            ticket=ticket,
            category=str(classification_result["category"]),
            severity=str(classification_result["severity"]),
            resolution_path=str(classification_result["resolution_path"]),
            article_id=str(retrieval_result["article_id"]),
            responder_escalation_recommended=bool(
                response_dict["escalation_recommended"]
            ),
        )
        escalation_dict = escalation_result_to_dict(escalation)
        escalation_results.append(escalation_dict)

    evaluation_results_objects = evaluator.evaluate_many(
        tickets=eval_tickets,
        classification_results=classification_results,
        retrieval_results=retrieval_results,
        response_results=response_results,
        escalation_results=escalation_results,
    )
    evaluation_results = [
        evaluator_result_to_dict(result) for result in evaluation_results_objects
    ]

    metrics_summary = metrics_calculator.summarize(
        tickets=eval_tickets,
        evaluation_results=evaluation_results,
        classification_results=classification_results,
        escalation_results=escalation_results,
    )

    write_json("classification_results.json", classification_results)
    write_json("retrieval_results.json", retrieval_results)
    write_json("response_results.json", response_results)
    write_json("escalation_results.json", escalation_results)
    write_json("evaluation_results.json", evaluation_results)
    write_json("metrics_summary.json", metrics_summary)

    print_summary(metrics_summary)
    print("\nOutput files written to: data/outputs/")


if __name__ == "__main__":
    run_pipeline()