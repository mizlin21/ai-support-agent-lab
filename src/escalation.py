from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class EscalationResult:
    ticket_id: str
    escalation_required: bool
    escalation_type: str
    summary: str
    suspected_area: str
    customer_impact: str
    reproduction_steps: List[str]
    evidence_requested: List[str]
    reasons: List[str]


class EscalationEngine:
    """
    Determine whether a support ticket should be escalated and, if so,
    generate a structured defect/support handoff record.

    Responsibilities:
    - decide if escalation is required
    - distinguish support follow-up vs engineering defect escalation
    - generate structured escalation details for downstream review
    """

    def evaluate(
        self,
        ticket: Dict[str, Any],
        category: str,
        severity: str,
        resolution_path: str,
        article_id: str,
        responder_escalation_recommended: bool,
    ) -> EscalationResult:
        """
        Evaluate whether the ticket should be escalated.
        """
        ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
        subject = str(ticket.get("subject", "")).strip()
        message = str(ticket.get("message", "")).strip()
        text = f"{subject} {message}".lower()

        reasons = self._collect_escalation_reasons(
            text=text,
            category=category,
            severity=severity,
            resolution_path=resolution_path,
            responder_escalation_recommended=responder_escalation_recommended,
        )

        escalation_required = len(reasons) > 0
        escalation_type = self._determine_escalation_type(
            text=text,
            category=category,
            escalation_required=escalation_required,
        )

        suspected_area = self._map_suspected_area(category)
        customer_impact = self._determine_customer_impact(
            ticket=ticket,
            severity=severity,
            text=text,
        )

        reproduction_steps = self._build_reproduction_steps(ticket, category)
        evidence_requested = self._build_evidence_requests(category, escalation_type)
        summary = self._build_summary(
            subject=subject,
            category=category,
            escalation_type=escalation_type,
            escalation_required=escalation_required,
        )

        return EscalationResult(
            ticket_id=ticket_id,
            escalation_required=escalation_required,
            escalation_type=escalation_type,
            summary=summary,
            suspected_area=suspected_area,
            customer_impact=customer_impact,
            reproduction_steps=reproduction_steps,
            evidence_requested=evidence_requested,
            reasons=reasons,
        )

    def _collect_escalation_reasons(
        self,
        text: str,
        category: str,
        severity: str,
        resolution_path: str,
        responder_escalation_recommended: bool,
    ) -> List[str]:
        reasons: List[str] = []

        if resolution_path == "escalate":
            reasons.append("Routing logic marked this ticket for escalation.")

        if resolution_path == "partial_or_escalate" and severity == "high":
            reasons.append("High-severity issue requires human review.")

        if responder_escalation_recommended:
            reasons.append("Response layer recommended escalation based on ticket signals.")

        broad_impact_signals = [
            "multiple users",
            "everyone",
            "across browsers",
            "entire team",
            "several users",
        ]
        if any(signal in text for signal in broad_impact_signals):
            reasons.append("Issue appears to affect multiple users or environments.")

        defect_signals = [
            "duplicate",
            "duplicates",
            "not updating",
            "timing out",
            "fails consistently",
            "nothing happens",
            "stuck loading",
            "no error message",
        ]
        if any(signal in text for signal in defect_signals):
            reasons.append("Symptoms may indicate a product defect or backend issue.")

        if category == "unknown":
            reasons.append("Ticket could not be classified confidently.")

        return reasons

    def _determine_escalation_type(
        self,
        text: str,
        category: str,
        escalation_required: bool,
    ) -> str:
        if not escalation_required:
            return "none"

        engineering_signals = [
            "across browsers",
            "multiple users",
            "duplicate",
            "duplicates",
            "timing out",
            "stuck loading",
            "no error message",
            "not updating",
        ]

        if category in {"crm_sync", "report_timeout", "quote_export", "browser_ui"}:
            if any(signal in text for signal in engineering_signals):
                return "engineering_defect"

        if category == "unknown":
            return "support_review"

        return "support_follow_up"

    def _map_suspected_area(self, category: str) -> str:
        area_map = {
            "login_access": "authentication_service",
            "quote_export": "document_export_service",
            "crm_sync": "integration_service",
            "permissions": "authorization_layer",
            "browser_ui": "frontend_ui",
            "report_timeout": "reporting_service",
            "unknown": "unclassified_support_issue",
        }
        return area_map.get(category, "unclassified_support_issue")

    def _determine_customer_impact(
        self,
        ticket: Dict[str, Any],
        severity: str,
        text: str,
    ) -> str:
        customer_tier = str(ticket.get("customer_tier", "")).lower()

        if "multiple users" in text or "everyone" in text or "entire team" in text:
            return "high"

        if severity == "high" and customer_tier == "enterprise":
            return "high"

        if severity == "high":
            return "medium"

        return "low"

    def _build_reproduction_steps(self, ticket: Dict[str, Any], category: str) -> List[str]:
        subject = str(ticket.get("subject", "")).strip()
        message = str(ticket.get("message", "")).strip()

        steps = [
            f"Open the support case for: {subject}",
            "Review the user-reported symptoms and current environment details.",
        ]

        category_steps = {
            "login_access": [
                "Attempt login after password reset with a test account.",
                "Confirm whether invalid credential or lockout behavior occurs.",
            ],
            "quote_export": [
                "Open a quote record.",
                "Attempt export to PDF from the affected workflow.",
                "Observe whether download begins or no action occurs.",
            ],
            "crm_sync": [
                "Create or update a quote in the application.",
                "Verify whether the record appears in the connected CRM.",
                "Check for delay, missing records, or duplicates.",
            ],
            "permissions": [
                "Access the affected report or feature as the impacted role.",
                "Confirm whether access denied behavior occurs.",
            ],
            "browser_ui": [
                "Open the affected page in the reported browser.",
                "Verify whether layout, widget, or button rendering is broken.",
            ],
            "report_timeout": [
                "Run the affected report with the reported dataset size.",
                "Verify whether the request times out or fails to load.",
            ],
        }

        steps.extend(category_steps.get(category, ["Attempt to reproduce based on the user-reported workflow."]))

        if message:
            steps.append(f"Reference ticket details: {message}")

        return steps

    def _build_evidence_requests(self, category: str, escalation_type: str) -> List[str]:
        base_requests = ["timestamp of failure", "user/account identifier", "screenshot if available"]

        category_requests = {
            "login_access": ["exact login error message", "browser and device details"],
            "quote_export": ["browser name/version", "quote ID", "whether pop-up blocker was disabled"],
            "crm_sync": ["CRM platform name", "affected record IDs", "integration log excerpt if available"],
            "permissions": ["affected user role", "feature/report name", "admin permission snapshot"],
            "browser_ui": ["browser name/version", "screen recording or screenshot", "recent release/version noted"],
            "report_timeout": ["report name", "dataset size", "approximate run duration before timeout"],
        }

        requests = list(base_requests)
        requests.extend(category_requests.get(category, []))

        if escalation_type == "engineering_defect":
            requests.append("steps already attempted from KB troubleshooting")

        return requests

    def _build_summary(
        self,
        subject: str,
        category: str,
        escalation_type: str,
        escalation_required: bool,
    ) -> str:
        if not escalation_required:
            return f"No escalation required for ticket related to '{subject}'."

        return (
            f"Escalate ticket related to '{subject}' as {escalation_type} "
            f"under category '{category}'."
        )


def result_to_dict(result: EscalationResult) -> Dict[str, Any]:
    """
    Convert an EscalationResult into a serializable dictionary.
    """
    return {
        "ticket_id": result.ticket_id,
        "escalation_required": result.escalation_required,
        "escalation_type": result.escalation_type,
        "summary": result.summary,
        "suspected_area": result.suspected_area,
        "customer_impact": result.customer_impact,
        "reproduction_steps": result.reproduction_steps,
        "evidence_requested": result.evidence_requested,
        "reasons": result.reasons,
    }