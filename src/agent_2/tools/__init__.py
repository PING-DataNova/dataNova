"""
Outils pour Agent 2.
"""

import json
from typing import Optional, List, Dict, Any

from langchain.tools import tool

from src.storage.database import get_session
from src.storage.models import Analysis


def _normalize_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


@tool
def fetch_analyses(
    validation_status: str = "approved",
    limit: int = 10,
    analysis_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Recupere des analyses depuis la base de donnees.

    Args:
        validation_status: pending, approved, rejected, ou "any"
        limit: Nombre maximum de lignes
        analysis_id: ID d'analyse precis (optionnel)

    Returns:
        Liste d'analyses structurees
    """
    session = get_session()
    try:
        query = session.query(Analysis)

        if analysis_id:
            query = query.filter(Analysis.id == analysis_id)
        elif validation_status and validation_status.lower() != "any":
            query = query.filter(Analysis.validation_status == validation_status)

        if limit and limit > 0:
            query = query.order_by(Analysis.created_at.desc()).limit(limit)

        rows = query.all()
        results: List[Dict[str, Any]] = []
        for item in rows:
            results.append({
                "id": item.id,
                "document_id": item.document_id,
                "is_relevant": item.is_relevant,
                "confidence": item.confidence,
                "matched_keywords": _normalize_json(item.matched_keywords),
                "matched_nc_codes": _normalize_json(item.matched_nc_codes),
                "llm_reasoning": item.llm_reasoning,
                "validation_status": item.validation_status,
                "validation_comment": item.validation_comment,
                "validated_by": item.validated_by,
                "validated_at": item.validated_at.isoformat() if item.validated_at else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            })
        return results
    finally:
        session.close()


def get_agent_2_tools():
    return [fetch_analyses]


__all__ = ["fetch_analyses", "get_agent_2_tools"]
