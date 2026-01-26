"""Script pour charger les données JSON simulées dans la base de données."""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import SessionLocal
from src.storage.models import Document, Analysis
import hashlib


def load_json_data():
    """Charger les données JSON dans la base de données."""
    
    # Données JSON
    json_data = {
        "documents": [
            {
                "title": "Regulation (EU) 2024/123 - CBAM Extension to Polymers and Plastics",
                "celex_number": "32024R0123",
                "document_type": "REGULATION",
                "publication_date": "2024-01-15T00:00:00",
                "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R0123",
                "summary": "This regulation extends the Carbon Border Adjustment Mechanism (CBAM) to cover polymers and plastic materials imported from third countries. It requires importers to declare embedded carbon emissions and purchase CBAM certificates. Applies to CN codes 3901-3926. Mandatory from June 2026.",
                "status": "ACTIVE_LAW"
            },
            {
                "title": "Proposal COM(2024) 567 - Amendment to EUDR for Natural Rubber",
                "celex_number": "52024PC0567",
                "document_type": "PROPOSAL",
                "publication_date": "2024-11-20T00:00:00",
                "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52024PC0567",
                "summary": "Commission proposal to extend the EU Deforestation Regulation (EUDR) to include natural rubber imports. Would require due diligence statements for rubber sourced from Thailand, Indonesia, and Vietnam. Impact assessment shows compliance costs of 200M EUR annually for EU industry. Public consultation open until March 2026.",
                "status": "PROPOSAL"
            },
            {
                "title": "Regulation (EU) 2024/789 - Additional Customs Duties on Steel from India",
                "celex_number": "32024R0789",
                "document_type": "REGULATION",
                "publication_date": "2024-09-10T00:00:00",
                "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R0789",
                "summary": "Implementing regulation imposing additional duties of 25% on certain steel products (CN codes 7208-7229) imported from India in response to alleged dumping practices. Affects hot-rolled and cold-rolled steel. Duties effective immediately from publication date. Annual review scheduled for September 2025.",
                "status": "ACTIVE_LAW"
            },
            {
                "title": "Council Decision 2024/456 - Extension of Sanctions on Belarus",
                "celex_number": "32024D0456",
                "document_type": "DECISION",
                "publication_date": "2024-06-30T00:00:00",
                "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024D0456",
                "summary": "Council decision extending economic sanctions on Belarus until December 2025. Includes restrictions on imports of potash fertilizers (CN code 3102) and petroleum products. Companies with existing supply contracts from Belarusian entities must phase out by December 31, 2024. Exemptions available for humanitarian purposes only.",
                "status": "ACTIVE_LAW"
            },
            {
                "title": "Regulation (EU) 2024/234 - Updated CBAM Emission Reporting Requirements",
                "celex_number": "32024R0234",
                "document_type": "REGULATION",
                "publication_date": "2024-03-01T00:00:00",
                "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R0234",
                "summary": "Delegated regulation specifying detailed methodology for calculating embedded emissions in CBAM-covered goods (aluminium, steel, cement, fertilizers, electricity). Requires installation-level data from third-country producers. Default values apply if actual data unavailable. Quarterly reporting mandatory starting Q2 2024.",
                "status": "ACTIVE_LAW"
            },
            {
                "title": "Proposal COM(2024) 890 - Corporate Sustainability Reporting Directive (CSRD) Extension",
                "celex_number": "52024PC0890",
                "document_type": "PROPOSAL",
                "publication_date": "2024-12-05T00:00:00",
                "url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52024PC0890",
                "summary": "Proposal to extend CSRD scope to cover companies with 250+ employees (currently 500+) by 2027. Would require Scope 3 emissions reporting for entire supply chain, including third-country suppliers. Impact assessment estimates compliance costs of 50-80k EUR per company annually. Parliament vote expected Q3 2025.",
                "status": "PROPOSAL"
            }
        ]
    }
    
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("🚀 CHARGEMENT DES DONNÉES JSON SIMULÉES")
        print("=" * 80)
        
        documents_created = []
        analyses_created = []
        
        for doc_data in json_data["documents"]:
            # Créer le hash du contenu
            content_hash = hashlib.sha256(doc_data["summary"].encode()).hexdigest()
            
            # Extraire les codes NC du summary
            nc_codes = []
            if "CN codes" in doc_data["summary"] or "CN code" in doc_data["summary"]:
                # Extraction simple des codes NC mentionnés
                if "3901-3926" in doc_data["summary"]:
                    nc_codes = ["3901", "3902", "3903", "3904", "3905", "3906", "3907", "3926"]
                elif "7208-7229" in doc_data["summary"]:
                    nc_codes = ["7208", "7209", "7210", "7228", "7229"]
                elif "3102" in doc_data["summary"]:
                    nc_codes = ["3102"]
            
            # Créer le document
            doc = Document(
                title=doc_data["title"],
                source_url=doc_data["url"],
                regulation_type=doc_data["document_type"],
                publication_date=datetime.fromisoformat(doc_data["publication_date"]),
                hash_sha256=content_hash,
                content=doc_data["summary"],
                nc_codes=nc_codes,
                document_metadata={
                    "celex_number": doc_data["celex_number"],
                    "status": doc_data["status"]
                },
                status="new",
                workflow_status="analyzed"
            )
            
            db.add(doc)
            db.flush()
            documents_created.append(doc)
            
            # Créer une analyse pour chaque document
            # Les 3 premiers sont en attente de validation (PENDING)
            # Les autres sont déjà approuvés ou rejetés
            is_pending = len(analyses_created) < 3
            
            # Déterminer la pertinence et le statut
            if doc_data["status"] == "ACTIVE_LAW":
                is_relevant = True
                confidence = 0.9
                validation_status = "approved" if not is_pending else "pending"
            elif doc_data["status"] == "PROPOSAL":
                is_relevant = True
                confidence = 0.75
                validation_status = "pending" if is_pending else "approved"
            else:
                is_relevant = False
                confidence = 0.5
                validation_status = "rejected"
            
            # Extraire des mots-clés du titre
            keywords = []
            title_lower = doc_data["title"].lower()
            if "cbam" in title_lower:
                keywords.append("CBAM")
            if "steel" in title_lower or "acier" in title_lower:
                keywords.append("steel")
            if "rubber" in title_lower:
                keywords.append("rubber")
            if "sanctions" in title_lower:
                keywords.append("sanctions")
            if "emissions" in title_lower or "emission" in title_lower:
                keywords.append("emissions")
            if "csrd" in title_lower:
                keywords.append("CSRD")
            
            analysis = Analysis(
                document_id=doc.id,
                is_relevant=is_relevant,
                confidence=confidence,
                matched_keywords=keywords,
                matched_nc_codes=nc_codes,
                llm_reasoning=f"Analysis of '{doc.title}': {doc_data['summary'][:200]}...",
                validation_status=validation_status
            )
            
            db.add(analysis)
            analyses_created.append(analysis)
        
        db.commit()
        
        print(f"\n✅ Données chargées avec succès!")
        print(f"\n📊 Résumé:")
        print(f"  - {len(documents_created)} documents créés")
        print(f"  - {len(analyses_created)} analyses créées")
        
        # Compter par statut
        pending = sum(1 for a in analyses_created if a.validation_status == "pending")
        approved = sum(1 for a in analyses_created if a.validation_status == "approved")
        rejected = sum(1 for a in analyses_created if a.validation_status == "rejected")
        
        print(f"\n🔍 Analyses par statut:")
        print(f"  ⏳ En attente (pending): {pending}")
        print(f"  ✅ Approuvées (approved): {approved}")
        print(f"  ❌ Rejetées (rejected): {rejected}")
        
        print(f"\n📄 Documents créés:")
        for i, doc in enumerate(documents_created, 1):
            status_icon = "⏳" if analyses_created[i-1].validation_status == "pending" else "✅" if analyses_created[i-1].validation_status == "approved" else "❌"
            print(f"  {status_icon} {doc.title[:70]}...")
            print(f"      Codes NC: {', '.join(doc.nc_codes) if doc.nc_codes else 'N/A'}")
            print(f"      Statut validation: {analyses_created[i-1].validation_status}")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_json_data()
