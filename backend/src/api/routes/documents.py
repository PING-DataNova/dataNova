"""
Route pour servir les PDF collectés
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import os

router = APIRouter(prefix="/documents", tags=["Documents"])

PDF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/documents"))

from src.storage.database import SessionLocal
from src.storage.models import Document

@router.get("/mapping")
def get_celex_to_pdf_mapping():
    """
    Retourne le mapping CELEX ID → nom de fichier PDF
    """
    session = SessionLocal()
    docs = session.query(Document).filter(Document.celex_id.isnot(None)).all()
    mapping = {}
    for doc in docs:
        # On suppose que le nom du fichier PDF est basé sur le hash_sha256
        filename = f"document_{doc.hash_sha256}.pdf"
        mapping[doc.celex_id] = filename
    session.close()
    return mapping

@router.get("/by-celex/{celex_id}")
def get_document_by_celex(celex_id: str):
    """
    Télécharge un PDF par CELEX ID.
    - Si le fichier existe localement → le retourne
    - Sinon → redirige vers EUR-Lex
    """
    session = SessionLocal()
    try:
        doc = session.query(Document).filter(Document.celex_id == celex_id).first()
        
        if doc and doc.extra_metadata:
            # Récupérer le chemin depuis les métadonnées
            file_path_rel = doc.extra_metadata.get("file_path")
            if file_path_rel:
                # Chemin relatif depuis backend/
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
                file_path = os.path.join(base_dir, file_path_rel)
                
                if os.path.isfile(file_path):
                    return FileResponse(
                        file_path, 
                        media_type="application/pdf", 
                        filename=f"{celex_id}.pdf",
                        headers={"Content-Disposition": f"attachment; filename={celex_id}.pdf"}
                    )
        
        # Fichier non trouvé localement → rediriger vers EUR-Lex PDF
        eurlex_pdf_url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:{celex_id}"
        return RedirectResponse(url=eurlex_pdf_url)
    finally:
        session.close()

@router.get("/{filename}")
def get_document_pdf(filename: str):
    file_path = os.path.join(PDF_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)
