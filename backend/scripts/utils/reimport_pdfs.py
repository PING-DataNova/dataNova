#!/usr/bin/env python3
"""Réimporte les PDFs existants dans la base de données."""

from src.storage.database import SessionLocal
from src.storage.models import Document
from src.agent_1a.tools.pdf_extractor import extract_pdf_content_sync
import os
import hashlib
from datetime import datetime

def reimport_pdfs():
    db = SessionLocal()
    
    # Liste des PDFs existants
    pdf_dir = 'data/documents'
    pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf') and os.path.getsize(os.path.join(pdf_dir, f)) > 0]
    
    print(f'📄 PDFs trouvés: {len(pdfs)}')
    
    # IDs connus des documents CBAM
    doc_mapping = {
        'document_1cf130e20e51.pdf': {'celex': '02023R0956', 'title': 'Regulation (EU) 2023/956 - CBAM Main Regulation'},
        'document_080c1221d923.pdf': {'celex': '02023R1773', 'title': 'Implementing Regulation (EU) 2023/1773 - CBAM Transitional Period'},
        'document_6dda84b594e5.pdf': {'celex': '32024R3210', 'title': 'Regulation (EU) 2024/3210 - CBAM Amendment'},
    }
    
    imported = 0
    for pdf_file in pdfs:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        
        # Calculer le hash du fichier
        with open(pdf_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        if pdf_file in doc_mapping:
            info = doc_mapping[pdf_file]
            celex = info['celex']
            title = info['title']
        else:
            celex = pdf_file.replace('document_', '').replace('.pdf', '')
            title = f'Document EUR-Lex {celex}'
        
        # Vérifier si déjà en base par hash
        existing = db.query(Document).filter(Document.hash_sha256 == file_hash).first()
        if existing:
            print(f'  ⏭️  {celex} déjà en base')
            continue
        
        # Extraire le texte
        try:
            result = extract_pdf_content_sync(pdf_path)
            text = result.text if result.status == "success" else ""
            if not text or len(text) < 100:
                print(f'  ⚠️  {pdf_file}: texte trop court')
                continue
                
            doc = Document(
                title=title,
                source_url=f'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}',
                event_type='reglementaire',
                event_subtype='CBAM',
                publication_date=datetime.now(),
                content=text,
                hash_sha256=file_hash,
                status='new'
            )
            db.add(doc)
            imported += 1
            print(f'  ✅ {celex}: {title[:50]}...')
        except Exception as e:
            print(f'  ❌ {pdf_file}: {e}')
    
    db.commit()
    db.close()
    
    print(f'\n📊 Résultat: {imported} documents importés')

if __name__ == '__main__':
    reimport_pdfs()
