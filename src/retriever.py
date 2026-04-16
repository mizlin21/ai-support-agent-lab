from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class RetrievalResult:
    ticket_id: str
    article_id: str
    article_file: str
    confidence: float
    matched_terms: List[str]
    score: int


class KnowledgeBaseRetriever:
    """
    Baseline rule-based knowledge base retriever.

    Responsibilities:
    - load KB index
    - compare ticket text against KB tags and classifier category
    - return the best-matching KB article with a simple confidence score

    This version is intentionally transparent and easy to inspect.
    """

    def __init__(self, kb_index_path: str = "data/kb/kb_index.json") -> None:
        self.kb_index_path = Path(kb_index_path)
        self.kb_index = self._load_kb_index()

    def retrieve(self, ticket: Dict[str, Any], predicted_category: str = "") -> RetrievalResult:
        """
        Retrieve the most relevant knowledge base article for a ticket.
        """
        ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
        text = self._combine_ticket_text(ticket)

        best_article: Dict[str, Any] | None = None
        best_score = -1
        best_matches: List[str] = []

        for article in self.kb_index:
            score, matches = self._score_article(
                text=text,
                article=article,
                predicted_category=predicted_category,
            )

            if score > best_score:
                best_article = article
                best_score = score
                best_matches = matches

        if not best_article:
            return RetrievalResult(
                ticket_id=ticket_id,
                article_id="unknown",
                article_file="",
                confidence=0.0,
                matched_terms=[],
                score=0,
            )

        confidence = self._score_to_confidence(best_score)

        return RetrievalResult(
            ticket_id=ticket_id,
            article_id=str(best_article.get("id", "unknown")),
            article_file=str(best_article.get("file", "")),
            confidence=confidence,
            matched_terms=best_matches,
            score=best_score,
        )

    def retrieve_many(
        self,
        tickets: List[Dict[str, Any]],
        predicted_categories: Dict[str, str] | None = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve KB articles for many tickets.
        """
        predicted_categories = predicted_categories or {}

        results: List[RetrievalResult] = []
        for ticket in tickets:
            ticket_id = str(ticket.get("ticket_id", "UNKNOWN"))
            category = predicted_categories.get(ticket_id, "")
            results.append(self.retrieve(ticket, predicted_category=category))

        return results

    def _load_kb_index(self) -> List[Dict[str, Any]]:
        """
        Load the KB index from disk.
        """
        if not self.kb_index_path.exists():
            raise FileNotFoundError(f"KB index not found: {self.kb_index_path}")

        with self.kb_index_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                f"Expected KB index to be a JSON array, got {type(data).__name__}"
            )

        for index, article in enumerate(data, start=1):
            if not isinstance(article, dict):
                raise ValueError(
                    f"KB entry #{index} must be a JSON object, got {type(article).__name__}"
                )

            required_fields = ["id", "file", "tags"]
            missing = [field for field in required_fields if field not in article]
            if missing:
                raise ValueError(
                    f"KB entry #{index} is missing required field(s): {', '.join(missing)}"
                )

        return data

    def _combine_ticket_text(self, ticket: Dict[str, Any]) -> str:
        subject = str(ticket.get("subject", ""))
        message = str(ticket.get("message", ""))
        product_area = str(ticket.get("product_area", ""))
        environment = str(ticket.get("environment", ""))
        return f"{subject} {message} {product_area} {environment}".lower()

    def _score_article(
        self,
        text: str,
        article: Dict[str, Any],
        predicted_category: str,
    ) -> tuple[int, List[str]]:
        score = 0
        matches: List[str] = []

        article_id = str(article.get("id", "")).lower()
        tags = [str(tag).lower() for tag in article.get("tags", [])]

        # Tag overlap scoring
        for tag in tags:
            if tag in text:
                score += 2
                matches.append(tag)

        # Category-to-article boost
        category_map = {
            "login_access": "login_reset",
            "quote_export": "quote_export_issue",
            "crm_sync": "crm_sync_delay",
            "permissions": "user_permissions",
            "browser_ui": "browser_cache_issue",
            "report_timeout": "report_timeout",
        }

        expected_article_for_category = category_map.get(predicted_category, "")
        if expected_article_for_category and article_id == expected_article_for_category:
            score += 3
            matches.append(f"category:{predicted_category}")

        # Light symptom keyword boosts
        symptom_boosts = {
            "login_reset": ["login", "password", "invalid credentials", "reset"],
            "quote_export_issue": ["export", "pdf", "download"],
            "crm_sync_delay": ["crm", "salesforce", "sync", "integration", "duplicate"],
            "user_permissions": ["access denied", "permission", "role"],
            "browser_cache_issue": ["browser", "cache", "ui", "layout", "dashboard"],
            "report_timeout": ["report", "timeout", "large dataset", "slow"],
        }

        for keyword in symptom_boosts.get(article_id, []):
            if keyword in text:
                score += 1
                if keyword not in matches:
                    matches.append(keyword)

        return score, matches

    def _score_to_confidence(self, score: int) -> float:
        """
        Convert a simple retrieval score into a readable confidence value.
        """
        if score <= 0:
            return 0.0
        if score == 1:
            return 0.55
        if score == 2:
            return 0.65
        if score == 3:
            return 0.72
        if score == 4:
            return 0.8
        if score == 5:
            return 0.87
        return 0.93


def result_to_dict(result: RetrievalResult) -> Dict[str, Any]:
    """
    Convert a RetrievalResult into a serializable dictionary.
    """
    return {
        "ticket_id": result.ticket_id,
        "article_id": result.article_id,
        "article_file": result.article_file,
        "confidence": result.confidence,
        "matched_terms": result.matched_terms,
        "score": result.score,
    }