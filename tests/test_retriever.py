from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is importable when tests run from project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from retriever import KnowledgeBaseRetriever, result_to_dict


def test_retriever_returns_quote_export_article() -> None:
    retriever = KnowledgeBaseRetriever()

    ticket = {
        "ticket_id": "TEST-001",
        "subject": "Export to PDF not working",
        "message": "When I click export on a quote, nothing downloads.",
        "product_area": "quote_management",
        "environment": "web",
    }

    result = retriever.retrieve(ticket, predicted_category="quote_export")
    result_dict = result_to_dict(result)

    assert result_dict["ticket_id"] == "TEST-001"
    assert result_dict["article_id"] == "quote_export_issue"
    assert result_dict["article_file"] == "quote_export_issue.md"
    assert result_dict["confidence"] > 0
    assert result_dict["score"] > 0


def test_retriever_returns_login_reset_article() -> None:
    retriever = KnowledgeBaseRetriever()

    ticket = {
        "ticket_id": "TEST-002",
        "subject": "Password reset not working",
        "message": "I reset my password but still cannot log in.",
        "product_area": "authentication",
        "environment": "web",
    }

    result = retriever.retrieve(ticket, predicted_category="login_access")
    result_dict = result_to_dict(result)

    assert result_dict["article_id"] == "login_reset"
    assert result_dict["article_file"] == "login_reset.md"
    assert result_dict["confidence"] > 0


def test_retriever_returns_crm_sync_article() -> None:
    retriever = KnowledgeBaseRetriever()

    ticket = {
        "ticket_id": "TEST-003",
        "subject": "CRM sync delay",
        "message": "Salesforce is not updating new quotes after creation.",
        "product_area": "integrations",
        "environment": "api",
    }

    result = retriever.retrieve(ticket, predicted_category="crm_sync")
    result_dict = result_to_dict(result)

    assert result_dict["article_id"] == "crm_sync_delay"
    assert result_dict["article_file"] == "crm_sync_delay.md"


def test_retriever_returns_permissions_article() -> None:
    retriever = KnowledgeBaseRetriever()

    ticket = {
        "ticket_id": "TEST-004",
        "subject": "User cannot access reports",
        "message": "The user gets access denied when opening reports.",
        "product_area": "permissions",
        "environment": "web",
    }

    result = retriever.retrieve(ticket, predicted_category="permissions")
    result_dict = result_to_dict(result)

    assert result_dict["article_id"] == "user_permissions"
    assert result_dict["article_file"] == "user_permissions.md"


def test_retriever_returns_browser_cache_article() -> None:
    retriever = KnowledgeBaseRetriever()

    ticket = {
        "ticket_id": "TEST-005",
        "subject": "Dashboard not loading properly",
        "message": "The UI widgets are stuck loading and the layout looks broken.",
        "product_area": "ui",
        "environment": "browser_chrome",
    }

    result = retriever.retrieve(ticket, predicted_category="browser_ui")
    result_dict = result_to_dict(result)

    assert result_dict["article_id"] == "browser_cache_issue"
    assert result_dict["article_file"] == "browser_cache_issue.md"


def test_retriever_returns_report_timeout_article() -> None:
    retriever = KnowledgeBaseRetriever()

    ticket = {
        "ticket_id": "TEST-006",
        "subject": "Reports timing out",
        "message": "Large report generation times out before completing.",
        "product_area": "reporting",
        "environment": "web",
    }

    result = retriever.retrieve(ticket, predicted_category="report_timeout")
    result_dict = result_to_dict(result)

    assert result_dict["article_id"] == "report_timeout"
    assert result_dict["article_file"] == "report_timeout.md"


def test_retriever_category_boost_can_select_correct_article() -> None:
    retriever = KnowledgeBaseRetriever()

    ticket = {
        "ticket_id": "TEST-007",
        "subject": "Customer has an issue",
        "message": "The customer needs help with account access.",
        "product_area": "unknown",
        "environment": "web",
    }

    result = retriever.retrieve(ticket, predicted_category="login_access")
    result_dict = result_to_dict(result)

    assert result_dict["article_id"] == "login_reset"
    assert "category:login_access" in result_dict["matched_terms"]