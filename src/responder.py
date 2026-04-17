from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ResponseResult:
    ticket_id: str
    article_id: str
    response_text: str
    response_type: str
    grounded: bool
    escalation_recommended: bool
    steps_used: List[str]


class SupportResponder:
    """
    Generate KB-grounded support responses for classified tickets.

    Responsibilities:
    - read the selected KB article
    - extract structured troubleshooting steps
    - draft a professional support reply
    - recommend escalation when the issue appears unsafe to auto-resolve
    """

    def __init__(self, kb_articles_path: str = "data/kb/articles") -> None:
        self.kb_articles_path = Path(kb_articles_path)

    def respond(
        self,
        ticket: Dict[str, Any],
        article_id: str,
        article_file: str,
        category: str,
        severity: str,
        resolution_path: str,
    ) -> ResponseResult:
        """
        Generate a support response using the selected KB article.
        """
        ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
        subject = str(ticket.get("subject", "")).strip()
        message = str(ticket.get("message", "")).strip()

        article_text = self._read_article(article_file)
        steps = self._extract_section_bullets(article_text, "Resolution Steps")
        escalate_conditions = self._extract_section_bullets(article_text, "Escalate If")

        escalation_recommended = self._should_recommend_escalation(
            message=message,
            severity=severity,
            resolution_path=resolution_path,
        )

        response_type = (
            "escalation_recommended"
            if escalation_recommended
            else "kb_resolution"
        )

        response_text = self._build_response(
            subject=subject,
            message=message,
            category=category,
            severity=severity,
            resolution_path=resolution_path,
            article_id=article_id,
            steps=steps,
            escalate_conditions=escalate_conditions,
            escalation_recommended=escalation_recommended,
        )

        return ResponseResult(
            ticket_id=ticket_id,
            article_id=article_id,
            response_text=response_text,
            response_type=response_type,
            grounded=bool(article_file and steps),
            escalation_recommended=escalation_recommended,
            steps_used=steps[:4],
        )

    def _read_article(self, article_file: str) -> str:
        """
        Read the KB article contents from disk.
        """
        if not article_file:
            return ""

        path = self.kb_articles_path / article_file
        if not path.exists():
            return ""

        return path.read_text(encoding="utf-8")

    def _extract_section_bullets(self, article_text: str, section_name: str) -> List[str]:
        """
        Extract numbered or dashed items from a named markdown section.
        """
        if not article_text:
            return []

        lines = article_text.splitlines()
        collected: List[str] = []
        in_section = False

        for raw_line in lines:
            line = raw_line.strip()

            if line.startswith("## "):
                current_section = line.replace("## ", "", 1).strip().lower()
                in_section = current_section == section_name.lower()
                continue

            if not in_section:
                continue

            if not line:
                continue

            if line.startswith("## "):
                break

            if line[:2].isdigit() and line[2:3] == ".":
                collected.append(line[3:].strip())
            elif line.startswith("- "):
                collected.append(line[2:].strip())

        return collected

    def _should_recommend_escalation(
        self,
        message: str,
        severity: str,
        resolution_path: str,
    ) -> bool:
        """
        Determine whether the response should explicitly recommend escalation.
        """
        text = message.lower()

        escalation_signals = [
            "multiple users",
            "everyone",
            "across browsers",
            "duplicate",
            "duplicates",
            "not updating",
            "timing out",
            "persist",
            "still happening",
            "fails consistently",
        ]

        if resolution_path == "escalate":
            return True

        if resolution_path == "partial_or_escalate" and severity == "high":
            return True

        if any(signal in text for signal in escalation_signals):
            return True

        return False

    def _build_response(
        self,
        subject: str,
        message: str,
        category: str,
        severity: str,
        resolution_path: str,
        article_id: str,
        steps: List[str],
        escalate_conditions: List[str],
        escalation_recommended: bool,
    ) -> str:
        """
        Build the final customer-facing support response.
        """
        greeting = "Hello,"
        acknowledgement = self._build_acknowledgement(subject, category)
        context_line = self._build_context_line(category, severity, article_id)

        if not steps:
            steps_block = (
                "At the moment, I do not have a reliable troubleshooting article for this case, "
                "so this should be reviewed by a support engineer."
            )
        else:
            formatted_steps = "\n".join(
                f"{idx}. {step}" for idx, step in enumerate(steps[:4], start=1)
            )
            steps_block = f"Please try the following:\n{formatted_steps}"

        escalation_block = ""
        if escalation_recommended:
            escalation_block = (
                "\n\nIf the issue continues after these steps, or if this affects multiple users, "
                "it should be escalated for deeper investigation."
            )
        elif resolution_path == "partial_or_escalate":
            escalation_block = (
                "\n\nIf these steps do not resolve the issue, please reply with additional details "
                "so the case can be reviewed further."
            )

        detail_request = self._build_detail_request(category, escalate_conditions)
        closing = "\n\nBest,\nSupport"

        parts = [
            greeting,
            "",
            acknowledgement,
            context_line,
            "",
            steps_block,
            escalation_block,
            detail_request,
            closing,
        ]

        return "\n".join(part for part in parts if part is not None)

    def _build_acknowledgement(self, subject: str, category: str) -> str:
        subject_text = subject.strip() if subject else "the issue you reported"

        category_map = {
            "login_access": "This appears related to login or password access.",
            "quote_export": "This appears related to quote export behavior.",
            "crm_sync": "This appears related to CRM synchronization.",
            "permissions": "This appears related to user access or permissions.",
            "browser_ui": "This appears related to browser or UI rendering behavior.",
            "report_timeout": "This appears related to reporting performance or timeouts.",
        }

        category_hint = category_map.get(category, "This appears related to a support issue requiring review.")
        return f"Thanks for reporting {subject_text.lower()}. {category_hint}"

    def _build_context_line(self, category: str, severity: str, article_id: str) -> str:
        return (
            f"Based on the current ticket details, the issue was mapped to category "
            f"'{category}' with {severity} severity and routed using KB article '{article_id}'."
        )

    def _build_detail_request(self, category: str, escalate_conditions: List[str]) -> str:
        common_requests = {
            "login_access": "If needed, please include the exact login error message and the time of the failed attempt.",
            "quote_export": "If needed, please include the browser name/version and whether the issue occurs in another browser.",
            "crm_sync": "If needed, please include the CRM system name, approximate sync time, and whether records are missing or duplicated.",
            "permissions": "If needed, please include the affected user role and the exact page or report showing the access error.",
            "browser_ui": "If needed, please include browser name/version and a screenshot of the UI issue.",
            "report_timeout": "If needed, please include the report name, dataset size, and approximate time of failure.",
        }

        base = common_requests.get(
            category,
            "If needed, please include any error details, timestamps, and screenshots."
        )

        if escalate_conditions:
            return f"\n{base}"
        return f"\n{base}"


def result_to_dict(result: ResponseResult) -> Dict[str, Any]:
    """
    Convert a ResponseResult into a serializable dictionary.
    """
    return {
        "ticket_id": result.ticket_id,
        "article_id": result.article_id,
        "response_text": result.response_text,
        "response_type": result.response_type,
        "grounded": result.grounded,
        "escalation_recommended": result.escalation_recommended,
        "steps_used": result.steps_used,
    }