"""
Base de contacts pour les notifications PING
"""

from typing import List, Dict, Any

# ============================================================================
# CONTACTS DE TEST
# ============================================================================

CONTACTS = {
    # Destinataires principaux (reçoivent toutes les alertes CRITIQUE)
    "primary": [
        {
            "name": "Marc Houndji",
            "email": "marc.houndji@groupe-esigelec.org",
            "role": "Directeur Achats",
            "notify_levels": ["CRITIQUE", "ELEVE", "MOYEN", "FAIBLE"]
        },
        {
            "name": "Nora Dossou-Gbete",
            "email": "nora.dossou-gbete@groupe-esigelec.org",
            "role": "Directeur Supply Chain",
            "notify_levels": ["CRITIQUE", "ELEVE", "MOYEN", "FAIBLE"]
        }
    ],
    
    # Contacts par site (pour extension future)
    "sites": {
        "toulouse": {
            "directeur": "marc.houndji@groupe-esigelec.org",
            "supply_chain": "nora.dossou-gbete@groupe-esigelec.org"
        },
        "munich": {
            "directeur": "marc.houndji@groupe-esigelec.org",
            "supply_chain": "nora.dossou-gbete@groupe-esigelec.org"
        },
        "paris": {
            "directeur": "marc.houndji@groupe-esigelec.org",
            "supply_chain": "nora.dossou-gbete@groupe-esigelec.org"
        }
    },
    
    # Contacts par type d'événement
    "event_types": {
        "reglementaire": {
            "additional": ["marc.houndji@groupe-esigelec.org"]
        },
        "climatique": {
            "additional": ["nora.dossou-gbete@groupe-esigelec.org"]
        },
        "geopolitique": {
            "additional": ["marc.houndji@groupe-esigelec.org", "nora.dossou-gbete@groupe-esigelec.org"]
        }
    }
}


def get_all_contacts() -> List[Dict[str, Any]]:
    """Retourne tous les contacts primaires"""
    return CONTACTS["primary"]


def get_contacts_for_level(risk_level: str) -> List[Dict[str, Any]]:
    """
    Retourne les contacts à notifier selon le niveau de risque
    
    Args:
        risk_level: CRITIQUE, ELEVE, MOYEN, FAIBLE
    """
    contacts = []
    for contact in CONTACTS["primary"]:
        if risk_level in contact.get("notify_levels", []):
            contacts.append(contact)
    return contacts


def get_contacts_for_event_type(event_type: str) -> List[str]:
    """
    Retourne les emails additionnels pour un type d'événement
    
    Args:
        event_type: reglementaire, climatique, geopolitique
    """
    event_config = CONTACTS["event_types"].get(event_type, {})
    return event_config.get("additional", [])


def get_contacts_for_site(site_id: str) -> Dict[str, str]:
    """
    Retourne les contacts pour un site spécifique
    
    Args:
        site_id: ID du site (toulouse, munich, etc.)
    """
    return CONTACTS["sites"].get(site_id, {})
