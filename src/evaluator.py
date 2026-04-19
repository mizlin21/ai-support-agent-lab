from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class EvaluationResult:
    ticket_id: str
    category_correct: bool
    retrieval_correct: bool
    resolution_path_correct: bool
    escalation_correct: bool
    response_grounded: bool
    overall_pass: bool
    notes: List[str]


class SupportEvaluator:
    """
    Evaluate end-to-end support pipeline behavior against expected outcomes.

    Responsibilities:
    - compare predicted category to expected category
    - compare retrieved KB article to expected article
    - compare routing/escalation behavior to expected resolution behavior
    - check whether the response stayed grounded in KB content
    - produce an overall pass/fail result per ticket
    """

    def evaluate_ticket(
        self,
        ticket: Dict[str, Any],
        classification_result: Dict[str, Any],
        retrieval_result: Dict[str, Any],
        response_result: Dict[str, Any],
        escalation_result: Dict[str, Any],
    ) -> EvaluationResult:
        """
        Evaluate a single ticket across classification, retrieval, response, and escalation.
        """
        ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
        notes: List[str] = []

        expected_category = str(ticket.get("category_expected", "")).strip().lower()
        expected_resolution = str(ticket.get("resolution_expected", "")).strip().lower()
        expected_article_id = str(ticket.get("correct_article_id", "")).strip()

        predicted_category = str(classification_result.get("category", "")).strip().lower()
        predicted_resolution_path = str(classification_result.get("resolution_path", "")).strip().lower()
        retrieved_article_id = str(retrieval_result.get("article_id", "")).strip()

        response_grounded = bool(response_result.get("grounded", False))
        escalation_required = bool(escalation_result.get("escalation_required", False))

        category_correct = predicted_category == expected_category
        retrieval_correct = retrieved_article_id == expected_article_id
        resolution_path_correct = self._is_resolution_path_correct(
            expected_resolution=expected_resolution,
            predicted_resolution_path=predicted_resolution_path,
            escalation_required=escalation_required,
        )
        escalation_correct = self._is_escalation_correct(
            expected_resolution=expected_resolution,
            escalation_required=escalation_required,
        )

        if not category_correct:
            notes.append(
                f"Expected category '{expected_category}' but got '{predicted_category}'."
            )

        if not retrieval_correct:
            notes.append(
                f"Expected article '{expected_article_id}' but got '{retrieved_article_id}'."
            )

        if not resolution_path_correct:
            notes.append(
                f"Expected resolution behavior '{expected_resolution}' but routing was '{predicted_resolution_path}'."
            )

        if not escalation_correct:
            notes.append(
                f"Escalation behavior did not match expected resolution type '{expected_resolution}'."
            )

        if not response_grounded:
            notes.append("Response was not grounded in KB-derived steps.")

        overall_pass = all(
            [
                category_correct,
                retrieval_correct,
                resolution_path_correct,
                escalation_correct,
                response_grounded,
            ]
        )

        return EvaluationResult(
            ticket_id=ticket_id,
            category_correct=category_correct,
            retrieval_correct=retrieval_correct,
            resolution_path_correct=resolution_path_correct,
            escalation_correct=escalation_correct,
            response_grounded=response_grounded,
            overall_pass=overall_pass,
            notes=notes,
        )

    def evaluate_many(
        self,
        tickets: List[Dict[str, Any]],
        classification_results: List[Dict[str, Any]],
        retrieval_results: List[Dict[str, Any]],
        response_results: List[Dict[str, Any]],
        escalation_results: List[Dict[str, Any]],
    ) -> List[EvaluationResult]:
        """
        Evaluate many tickets by matching results on ticket_id.
        """
        classification_map = self._index_by_ticket_id(classification_results)
        retrieval_map = self._index_by_ticket_id(retrieval_results)
        response_map = self._index_by_ticket_id(response_results)
        escalation_map = self._index_by_ticket_id(escalation_results)

        evaluations: List[EvaluationResult] = []

        for ticket in tickets:
            ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))

            classification_result = classification_map.get(ticket_id, {})
            retrieval_result = retrieval_map.get(ticket_id, {})
            response_result = response_map.get(ticket_id, {})
            escalation_result = escalation_map.get(ticket_id, {})

            evaluations.append(
                self.evaluate_ticket(
                    ticket=ticket,
                    classification_result=classification_result,
                    retrieval_result=retrieval_result,
                    response_result=response_result,
                    escalation_result=escalation_result,
                )
            )

        return evaluations

    def _is_resolution_path_correct(
        self,
        expected_resolution: str,
        predicted_resolution_path: str,
        escalation_required: bool,
    ) -> bool:
        """
        Compare expected resolution type with predicted routing behavior.
        """
        if expected_resolution == "kb_resolvable":
            return predicted_resolution_path == "kb_resolvable" and not escalation_required

        if expected_resolution == "partial_or_escalate":
            return predicted_resolution_path in {"partial_or_escalate", "escalate"}

        if expected_resolution == "escalate":
            return escalation_required or predicted_resolution_path == "escalate"

        return False

    def _is_escalation_correct(
        self,
        expected_resolution: str,
        escalation_required: bool,
    ) -> bool:
        """
        Compare expected escalation behavior.
        """
        if expected_resolution == "kb_resolvable":
            return not escalation_required

        if expected_resolution == "partial_or_escalate":
            return True

        if expected_resolution == "escalate":
            return escalation_required

        return False

    def _index_by_ticket_id(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Convert a list of result dictionaries into a ticket_id-indexed map.
        """
        indexed: Dict[str, Dict[str, Any]] = {}
        for result in results:
            ticket_id = str(result.get("ticket_id", "UNKNOWN"))
            indexed[ticket_id] = result
        return indexed


def result_to_dict(result: EvaluationResult) -> Dict[str, Any]:
    """
    Convert an EvaluationResult into a serializable dictionary.
    """
    return {
        "ticket_id": result.ticket_id,
        "category_correct": result.category_correct,
        "retrieval_correct": result.retrieval_correct,
        "resolution_path_correct": result.resolution_path_correct,
        "escalation_correct": result.escalation_correct,
        "response_grounded": result.response_grounded,
        "overall_pass": result.overall_pass,
        "notes": result.notes,
    }