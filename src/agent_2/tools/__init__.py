"""
Outils pour Agent 2.
"""

import json
from typing import Optional, List, Dict, Any

from langchain.tools import tool

from src.storage.database import get_session
import re

from src.storage.models import Analysis, CompanyProcess, Document, ImpactAssessment


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
        query = session.query(Analysis, Document).join(Document, Analysis.document_id == Document.id)

        if analysis_id:
            query = query.filter(Analysis.id == analysis_id)
        elif validation_status and validation_status.lower() != "any":
            query = query.filter(Analysis.validation_status == validation_status)

        if limit and limit > 0:
            query = query.order_by(Analysis.created_at.desc()).limit(limit)

        rows = query.all()
        results: List[Dict[str, Any]] = []
        for analysis, document in rows:
            results.append({
                "id": analysis.id,
                "document_id": analysis.document_id,
                "document_title": document.title,
                "regulation_type": analysis.regulation_type or document.regulation_type,
                "is_relevant": analysis.is_relevant,
                "confidence": analysis.confidence,
                "matched_keywords": _normalize_json(analysis.matched_keywords),
                "matched_nc_codes": _normalize_json(analysis.matched_nc_codes),
                "llm_reasoning": analysis.llm_reasoning,
                "validation_status": analysis.validation_status,
                "validation_comment": analysis.validation_comment,
                "validated_by": analysis.validated_by,
                "validated_at": analysis.validated_at.isoformat() if analysis.validated_at else None,
                "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            })
        return results
    finally:
        session.close()


@tool
def fetch_company_processes(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Recupere les donnees entreprise depuis la base de donnees.

    Args:
        limit: Nombre maximum de lignes

    Returns:
        Liste de profils entreprise
    """
    session = get_session()
    try:
        query = session.query(CompanyProcess)
        if limit and limit > 0:
            query = query.order_by(CompanyProcess.created_at.desc()).limit(limit)

        rows = query.all()
        results: List[Dict[str, Any]] = []
        for item in rows:
            results.append({
                "id": item.id,
                "company_name": item.company_name,
                "processes": _normalize_json(item.processes),
                "transport_modes": _normalize_json(item.transport_modes),
                "suppliers": _normalize_json(item.suppliers),
                "products": _normalize_json(item.products),
                "import_export_flows": _normalize_json(item.import_export_flows),
                "notes": item.notes,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            })
        return results
    finally:
        session.close()


@tool
def save_impact_assessment(
    analysis_id: str,
    risk_main: str,
    impact_level: str,
    risk_details: str,
    modality: str,
    deadline: str,
    recommendation: str,
    llm_reasoning: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sauvegarde une analyse d'impact.
    """
    allowed_risk_main = {"fiscal", "operationnel", "conformite", "reputationnel", "juridique"}
    allowed_impact = {"faible", "moyen", "eleve"}
    allowed_modality = {"certificat", "reporting", "taxe", "quota", "interdiction", "autorisation"}
    deadline_pattern = re.compile(r"^(0[1-9]|1[0-2])-[0-9]{4}$")

    errors = []
    if risk_main not in allowed_risk_main:
        errors.append(f"risk_main invalide: {risk_main}")
    if impact_level not in allowed_impact:
        errors.append(f"impact_level invalide: {impact_level}")
    if modality not in allowed_modality:
        errors.append(f"modality invalide: {modality}")
    if deadline and not deadline_pattern.match(deadline):
        errors.append(f"deadline invalide: {deadline} (format MM-YYYY)")

    if errors:
        return {
            "saved": False,
            "errors": errors,
            "allowed": {
                "risk_main": sorted(allowed_risk_main),
                "impact_level": sorted(allowed_impact),
                "modality": sorted(allowed_modality),
                "deadline_format": "MM-YYYY",
            },
        }

    session = get_session()
    try:
        existing = session.query(ImpactAssessment)\
            .filter(ImpactAssessment.analysis_id == analysis_id)\
            .first()
        if existing:
            existing.risk_main = risk_main
            existing.impact_level = impact_level
            existing.risk_details = risk_details
            existing.modality = modality
            existing.deadline = deadline
            existing.recommendation = recommendation
            existing.llm_reasoning = llm_reasoning
            session.commit()
            return {"saved": True, "impact_assessment_id": existing.id, "updated": True}

        impact = ImpactAssessment(
            analysis_id=analysis_id,
            risk_main=risk_main,
            impact_level=impact_level,
            risk_details=risk_details,
            modality=modality,
            deadline=deadline,
            recommendation=recommendation,
            llm_reasoning=llm_reasoning,
        )
        session.add(impact)
        session.commit()
        return {"saved": True, "impact_assessment_id": impact.id, "updated": False}
    except Exception as exc:
        session.rollback()
        return {"saved": False, "errors": [str(exc)]}
    finally:
        session.close()


def get_agent_2_tools():
    return [fetch_analyses, fetch_company_processes, save_impact_assessment]


__all__ = [
    "fetch_analyses",
    "fetch_company_processes",
    "save_impact_assessment",
    "get_agent_2_tools",
]
