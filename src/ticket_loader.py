from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_TICKET_FIELDS = ["ticket_id", "subject", "message"]


class TicketLoader:
    """
    Load and validate support ticket datasets from JSON files.

    Responsibilities:
    - load raw and evaluation ticket files
    - validate required ticket structure
    - normalize ticket fields for downstream use
    """

    def __init__(self, base_path: str = "data/tickets") -> None:
        self.base_path = Path(base_path)

    def load_raw_tickets(self) -> List[Dict[str, Any]]:
        """
        Load raw ticket dataset from data/tickets/raw_tickets.json
        """
        return self.load_file("raw_tickets.json")

    def load_eval_tickets(self) -> List[Dict[str, Any]]:
        """
        Load evaluation ticket dataset from data/tickets/eval_tickets.json
        """
        return self.load_file("eval_tickets.json")

    def load_expected_outcomes(self) -> Dict[str, Any]:
        """
        Load expected outcomes config from data/tickets/expected_outcomes.json
        """
        path = self.base_path / "expected_outcomes.json"
        data = self._read_json(path)

        if not isinstance(data, dict):
            raise ValueError(f"Expected a JSON object in {path}, but found {type(data).__name__}")

        return data

    def load_file(self, filename: str) -> List[Dict[str, Any]]:
        """
        Load a ticket file and return normalized ticket records.
        """
        path = self.base_path / filename
        data = self._read_json(path)

        if not isinstance(data, list):
            raise ValueError(f"Expected a JSON array in {path}, but found {type(data).__name__}")

        normalized_tickets: List[Dict[str, Any]] = []

        for index, ticket in enumerate(data, start=1):
            if not isinstance(ticket, dict):
                raise ValueError(
                    f"Ticket #{index} in {path} must be a JSON object, got {type(ticket).__name__}"
                )

            self._validate_ticket(ticket, path=path, index=index)
            normalized_tickets.append(self._normalize_ticket(ticket))

        return normalized_tickets

    def _read_json(self, path: Path) -> Any:
        """
        Read JSON content from disk.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _validate_ticket(self, ticket: Dict[str, Any], path: Path, index: int) -> None:
        """
        Validate that required fields exist and are non-empty.
        """
        missing_fields = [field for field in REQUIRED_TICKET_FIELDS if not ticket.get(field)]

        if missing_fields:
            raise ValueError(
                f"Ticket #{index} in {path} is missing required field(s): {', '.join(missing_fields)}"
            )

    def _normalize_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize ticket fields to keep downstream processing consistent.
        """
        normalized = dict(ticket)

        normalized["ticket_id"] = str(ticket.get("ticket_id", "")).strip()
        normalized["subject"] = str(ticket.get("subject", "")).strip()
        normalized["message"] = str(ticket.get("message", "")).strip()

        normalized["customer_tier"] = str(ticket.get("customer_tier", "unknown")).strip().lower()
        normalized["product_area"] = str(ticket.get("product_area", "unknown")).strip().lower()
        normalized["environment"] = str(ticket.get("environment", "unknown")).strip().lower()
        normalized["priority"] = str(ticket.get("priority", "low")).strip().lower()

        if "category_expected" in ticket:
            normalized["category_expected"] = str(ticket.get("category_expected", "")).strip().lower()

        if "resolution_expected" in ticket:
            normalized["resolution_expected"] = str(ticket.get("resolution_expected", "")).strip().lower()

        if "correct_article_id" in ticket:
            normalized["correct_article_id"] = str(ticket.get("correct_article_id", "")).strip()

        return normalized


def pretty_print_tickets(tickets: List[Dict[str, Any]]) -> None:
    """
    Print tickets in a readable format for quick terminal inspection.
    """
    for ticket in tickets:
        print(
            f"[{ticket['ticket_id']}] "
            f"subject={ticket['subject']!r}, "
            f"priority={ticket.get('priority', 'low')}, "
            f"product_area={ticket.get('product_area', 'unknown')}"
        )


if __name__ == "__main__":
    loader = TicketLoader()

    raw_tickets = loader.load_raw_tickets()
    eval_tickets = loader.load_eval_tickets()

    print(f"Loaded {len(raw_tickets)} raw tickets")
    print(f"Loaded {len(eval_tickets)} evaluation tickets")
    print("\nSample raw tickets:")
    pretty_print_tickets(raw_tickets[:3])