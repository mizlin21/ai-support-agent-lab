from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable when tests run from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from classifier import TicketClassifier, result_to_dict


def test_classifier_detects_quote_export_issue() -> None:
    classifier = TicketClassifier()

    ticket = {
        "ticket_id": "TEST-001",
        "subject": "Export to PDF not working",
        "message": "When I click export on a quote, nothing happens.",
        "product_area": "quote_management",
        "environment": "web",
        "priority": "medium",
    }

    result = classifier.classify(ticket)
    result_dict = result_to_dict(result)

    assert result_dict["ticket_id"] == "TEST-001"
    assert result_dict["category"] == "quote_export"
    assert result_dict["severity"] == "medium"
    assert result_dict["resolution_path"] == "kb_resolvable"
    assert result_dict["confidence"] > 0
    assert "export" in result_dict["matched_rules"] or "pdf" in result_dict["matched_rules"]


def test_classifier_detects_login_access_issue() -> None:
    classifier = TicketClassifier()

    ticket = {
        "ticket_id": "TEST-002",
        "subject": "Cannot log into account after password reset",
        "message": "I reset my password and still get invalid credentials.",
        "product_area": "authentication",
        "environment": "web",
        "priority": "high",
    }

    result = classifier.classify(ticket)
    result_dict = result_to_dict(result)

    assert result_dict["category"] == "login_access"
    assert result_dict["severity"] == "high"
    assert result_dict["resolution_path"] == "kb_resolvable"
    assert "password" in result_dict["matched_rules"] or "login" in result_dict["matched_rules"]


def test_classifier_escalates_multi_user_quote_export_issue() -> None:
    classifier = TicketClassifier()

    ticket = {
        "ticket_id": "TEST-003",
        "subject": "Multiple users cannot export quotes",
        "message": "Several users are reporting export failures across browsers.",
        "product_area": "quote_management",
        "environment": "web",
        "priority": "high",
    }

    result = classifier.classify(ticket)
    result_dict = result_to_dict(result)

    assert result_dict["category"] == "quote_export"
    assert result_dict["severity"] == "high"
    assert result_dict["resolution_path"] == "escalate"


def test_classifier_routes_crm_sync_high_severity_to_partial_or_escalate() -> None:
    classifier = TicketClassifier()

    ticket = {
        "ticket_id": "TEST-004",
        "subject": "CRM sync delay",
        "message": "Our Salesforce integration is not updating new quotes.",
        "product_area": "integrations",
        "environment": "api",
        "priority": "high",
    }

    result = classifier.classify(ticket)
    result_dict = result_to_dict(result)

    assert result_dict["category"] == "crm_sync"
    assert result_dict["severity"] == "high"
    assert result_dict["resolution_path"] == "partial_or_escalate"


def test_classifier_returns_unknown_when_no_rules_match() -> None:
    classifier = TicketClassifier()

    ticket = {
        "ticket_id": "TEST-005",
        "subject": "Unexpected behavior",
        "message": "Something strange happened and I am not sure what caused it.",
        "product_area": "unknown",
        "environment": "web",
        "priority": "low",
    }

    result = classifier.classify(ticket)
    result_dict = result_to_dict(result)

    assert result_dict["category"] == "unknown"
    assert result_dict["confidence"] == 0.0
    assert result_dict["matched_rules"] == []
    assert result_dict["resolution_path"] == "escalate"