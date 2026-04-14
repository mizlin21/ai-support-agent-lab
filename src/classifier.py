from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ClassificationResult:
    ticket_id: str
    category: str
    severity: str
    resolution_path: str
    confidence: float
    matched_rules: List[str]


class TicketClassifier:
    """
    Baseline rule-based classifier for simulated SaaS support tickets.

    Responsibilities:
    - predict ticket category
    - estimate severity
    - recommend handling path:
        - kb_resolvable
        - partial_or_escalate
        - escalate

    This version is intentionally deterministic and easy to inspect.
    Later versions can extend this with model-assisted logic.
    """

    def __init__(self) -> None:
        self.category_rules: Dict[str, List[str]] = {
            "login_access": [
                "login",
                "log in",
                "sign in",
                "password",
                "reset",
                "invalid credentials",
                "cannot access account",
            ],
            "quote_export": [
                "export",
                "pdf",
                "download",
                "quote",
                "save as pdf",
                "file downloads",
            ],
            "crm_sync": [
                "crm",
                "salesforce",
                "sync",
                "integration",
                "duplicate entries",
                "not updating",
                "missing updates",
                "api",
            ],
            "permissions": [
                "access denied",
                "permission",
                "permissions",
                "role",
                "user cannot access",
                "not authorized",
            ],
            "browser_ui": [
                "ui",
                "layout",
                "buttons overlap",
                "dashboard",
                "widgets",
                "cache",
                "rendering",
                "broken on chrome",
                "browser",
            ],
            "report_timeout": [
                "report",
                "reports",
                "timeout",
                "timing out",
                "large dataset",
                "slow loading",
                "generate a large report",
            ],
        }

        self.high_severity_terms = [
            "multiple users",
            "everyone",
            "enterprise",
            "high priority",
            "urgent",
            "blocked",
            "cannot work",
            "production",
            "several users",
        ]

        self.escalation_terms = [
            "multiple users",
            "everyone",
            "across browsers",
            "duplicate entries",
            "duplicates records",
            "fails consistently",
            "system outage",
            "down",
            "no workaround",
        ]

    def classify(self, ticket: Dict[str, str]) -> ClassificationResult:
        """
        Classify a support ticket into category, severity, and handling path.
        """
        ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
        text = self._combine_ticket_text(ticket)

        category, matched_rules, confidence = self._predict_category(text)
        severity = self._predict_severity(ticket, text)
        resolution_path = self._predict_resolution_path(category, severity, text)

        return ClassificationResult(
            ticket_id=ticket_id,
            category=category,
            severity=severity,
            resolution_path=resolution_path,
            confidence=confidence,
            matched_rules=matched_rules,
        )

    def classify_many(self, tickets: List[Dict[str, str]]) -> List[ClassificationResult]:
        """
        Classify a list of tickets.
        """
        return [self.classify(ticket) for ticket in tickets]

    def _combine_ticket_text(self, ticket: Dict[str, str]) -> str:
        subject = str(ticket.get("subject", ""))
        message = str(ticket.get("message", ""))
        product_area = str(ticket.get("product_area", ""))
        environment = str(ticket.get("environment", ""))
        return f"{subject} {message} {product_area} {environment}".lower()

    def _predict_category(self, text: str) -> tuple[str, List[str], float]:
        best_category = "unknown"
        best_matches: List[str] = []
        best_score = 0

        for category, keywords in self.category_rules.items():
            matches = [keyword for keyword in keywords if keyword in text]
            score = len(matches)

            if score > best_score:
                best_category = category
                best_matches = matches
                best_score = score

        if best_category == "unknown":
            return "unknown", [], 0.0

        # Simple confidence scaling for readability in outputs.
        confidence = min(0.5 + (best_score * 0.1), 0.95)
        return best_category, best_matches, round(confidence, 2)

    def _predict_severity(self, ticket: Dict[str, str], text: str) -> str:
        explicit_priority = str(ticket.get("priority", "")).lower()
        customer_tier = str(ticket.get("customer_tier", "")).lower()

        if explicit_priority in {"high", "critical"}:
            return "high"

        if any(term in text for term in self.high_severity_terms):
            return "high"

        if customer_tier == "enterprise" and ("not working" in text or "cannot" in text):
            return "high"

        if explicit_priority == "medium":
            return "medium"

        return "low"

    def _predict_resolution_path(self, category: str, severity: str, text: str) -> str:
        if category == "unknown":
            return "escalate"

        if any(term in text for term in self.escalation_terms):
            return "escalate"

        if category in {"crm_sync", "report_timeout"} and severity == "high":
            return "partial_or_escalate"

        if category in {"quote_export", "login_access", "permissions", "browser_ui"}:
            if severity == "high" and "multiple users" in text:
                return "escalate"
            return "kb_resolvable"

        if category in {"crm_sync", "report_timeout"}:
            return "partial_or_escalate"

        return "partial_or_escalate"


def result_to_dict(result: ClassificationResult) -> Dict[str, object]:
    """
    Convert a ClassificationResult dataclass into a serializable dictionary.
    """
    return {
        "ticket_id": result.ticket_id,
        "category": result.category,
        "severity": result.severity,
        "resolution_path": result.resolution_path,
        "confidence": result.confidence,
        "matched_rules": result.matched_rules,
    }