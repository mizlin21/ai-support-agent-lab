from __future__ import annotations

from typing import Any, Dict, List


class MetricsCalculator:
    """
    Aggregate evaluation and pipeline results into support-oriented metrics.

    Responsibilities:
    - compute classification accuracy
    - compute retrieval accuracy
    - compute response groundedness rate
    - compute escalation rate
    - compute overall pass rate
    - summarize performance by ticket category
    """

    def summarize(
        self,
        tickets: List[Dict[str, Any]],
        evaluation_results: List[Dict[str, Any]],
        classification_results: List[Dict[str, Any]],
        escalation_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build a metrics summary across the evaluated ticket set.
        """
        total_tickets = len(tickets)

        if total_tickets == 0:
            return {
                "total_tickets": 0,
                "classification_accuracy": 0.0,
                "retrieval_accuracy": 0.0,
                "response_grounded_rate": 0.0,
                "overall_pass_rate": 0.0,
                "escalation_rate": 0.0,
                "false_resolution_rate": 0.0,
                "category_breakdown": {},
            }

        category_correct_count = sum(
            1 for result in evaluation_results if result.get("category_correct", False)
        )
        retrieval_correct_count = sum(
            1 for result in evaluation_results if result.get("retrieval_correct", False)
        )
        grounded_count = sum(
            1 for result in evaluation_results if result.get("response_grounded", False)
        )
        overall_pass_count = sum(
            1 for result in evaluation_results if result.get("overall_pass", False)
        )
        escalation_count = sum(
            1 for result in escalation_results if result.get("escalation_required", False)
        )

        false_resolution_count = self._count_false_resolutions(
            tickets=tickets,
            classification_results=classification_results,
            escalation_results=escalation_results,
        )

        category_breakdown = self._build_category_breakdown(
            tickets=tickets,
            evaluation_results=evaluation_results,
        )

        return {
            "total_tickets": total_tickets,
            "classification_accuracy": self._safe_rate(category_correct_count, total_tickets),
            "retrieval_accuracy": self._safe_rate(retrieval_correct_count, total_tickets),
            "response_grounded_rate": self._safe_rate(grounded_count, total_tickets),
            "overall_pass_rate": self._safe_rate(overall_pass_count, total_tickets),
            "escalation_rate": self._safe_rate(escalation_count, total_tickets),
            "false_resolution_rate": self._safe_rate(false_resolution_count, total_tickets),
            "category_breakdown": category_breakdown,
        }

    def _count_false_resolutions(
        self,
        tickets: List[Dict[str, Any]],
        classification_results: List[Dict[str, Any]],
        escalation_results: List[Dict[str, Any]],
    ) -> int:
        """
        Count cases where the system did not escalate even though the expected
        resolution type was 'escalate'.
        """
        classification_map = self._index_by_ticket_id(classification_results)
        escalation_map = self._index_by_ticket_id(escalation_results)

        false_resolution_count = 0

        for ticket in tickets:
            ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
            expected_resolution = str(ticket.get("resolution_expected", "")).strip().lower()

            classification_result = classification_map.get(ticket_id, {})
            escalation_result = escalation_map.get(ticket_id, {})

            predicted_resolution_path = str(
                classification_result.get("resolution_path", "")
            ).strip().lower()
            escalation_required = bool(escalation_result.get("escalation_required", False))

            if expected_resolution == "escalate":
                if predicted_resolution_path != "escalate" and not escalation_required:
                    false_resolution_count += 1

        return false_resolution_count

    def _build_category_breakdown(
        self,
        tickets: List[Dict[str, Any]],
        evaluation_results: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build per-category counts and overall pass rates.
        """
        evaluation_map = self._index_by_ticket_id(evaluation_results)
        grouped: Dict[str, Dict[str, Any]] = {}

        for ticket in tickets:
            ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
            category = str(ticket.get("category_expected", "unknown")).strip().lower()
            evaluation = evaluation_map.get(ticket_id, {})

            if category not in grouped:
                grouped[category] = {
                    "total": 0,
                    "passed": 0,
                    "category_correct": 0,
                    "retrieval_correct": 0,
                }

            grouped[category]["total"] += 1

            if evaluation.get("overall_pass", False):
                grouped[category]["passed"] += 1

            if evaluation.get("category_correct", False):
                grouped[category]["category_correct"] += 1

            if evaluation.get("retrieval_correct", False):
                grouped[category]["retrieval_correct"] += 1

        for category, stats in grouped.items():
            total = stats["total"]
            stats["pass_rate"] = self._safe_rate(stats["passed"], total)
            stats["classification_accuracy"] = self._safe_rate(stats["category_correct"], total)
            stats["retrieval_accuracy"] = self._safe_rate(stats["retrieval_correct"], total)

        return grouped

    def _index_by_ticket_id(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        indexed: Dict[str, Dict[str, Any]] = {}
        for result in results:
            ticket_id = str(result.get("ticket_id", "UNKNOWN"))
            indexed[ticket_id] = result
        return indexed

    def _safe_rate(self, numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 2)