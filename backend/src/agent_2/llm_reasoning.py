"""
Module de Raisonnement LLM en Cascade pour Agent 2
Utilise Claude Sonnet (Anthropic) pour analyser l'impact en cascade sur la supply chain
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
from pathlib import Path

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    # Charger le .env depuis le répertoire backend
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    print("⚠️  python-dotenv not installed. Run: pip install python-dotenv")
    print("    Variables d'environnement doivent être définies manuellement.")


class LLMReasoning:
    """
    Classe pour le raisonnement LLM en cascade.
    Utilise OpenAI ou Anthropic pour analyser l'impact complet d'un événement sur la supply chain.
    """
    
    def __init__(self, model: str = None):
        """
        Initialise le module de raisonnement LLM.
        
        Args:
            model: Modèle à utiliser (optionnel, défini automatiquement selon le provider)
        """
        self.llm_provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
        
        if self.llm_provider == "openai":
            self.model = model or "gpt-4o"
            self._init_openai_client()
        else:
            self.model = model or "claude-sonnet-4-20250514"
            self._init_anthropic_client()
    
    def _init_openai_client(self):
        """Initialise le client OpenAI"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️  OPENAI_API_KEY not set. LLM reasoning will be simulated.")
                self.client = None
                self.llm_available = False
            else:
                self.client = OpenAI(api_key=api_key)
                self.llm_available = True
        except ImportError:
            print("⚠️  OpenAI library not installed. Run: pip install openai")
            self.client = None
            self.llm_available = False
        except Exception as e:
            print(f"⚠️  OpenAI client initialization failed: {e}")
            self.client = None
            self.llm_available = False
    
    def _init_anthropic_client(self):
        """Initialise le client Anthropic"""
        try:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("⚠️  ANTHROPIC_API_KEY not set. LLM reasoning will be simulated.")
                self.client = None
                self.llm_available = False
            else:
                self.client = anthropic.Anthropic(api_key=api_key)
                self.llm_available = True
        except ImportError:
            print("⚠️  Anthropic library not installed. Run: pip install anthropic")
            self.client = None
            self.llm_available = False
        except Exception as e:
            print(f"⚠️  Anthropic client initialization failed: {e}")
            self.client = None
            self.llm_available = False
    
    def analyze_cascade_impact(
        self,
        event: Dict[str, Any],
        affected_entity: Dict[str, Any],
        entity_type: str,  # "site" ou "supplier"
        relationships: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyse l'impact en cascade d'un événement sur une entité
        
        Args:
            event: Informations sur l'événement
            affected_entity: Site ou fournisseur impacté
            entity_type: "site" ou "supplier"
            relationships: Relations avec d'autres entités
            context: Contexte additionnel (stocks, délais, etc.)
        
        Returns:
            Analyse d'impact en cascade avec recommandations
        """
        prompt = self._build_cascade_prompt(
            event, affected_entity, entity_type, relationships, context
        )
        
        if self.llm_available:
            return self._call_llm(prompt)
        else:
            return self._simulate_reasoning(event, affected_entity, entity_type)
    
    def _build_cascade_prompt(
        self,
        event: Dict[str, Any],
        affected_entity: Dict[str, Any],
        entity_type: str,
        relationships: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Construit le prompt structuré pour Claude Sonnet adapté au type de risque"""
        
        # Formater les informations sur l'événement
        event_info = f"""
ÉVÉNEMENT:
- Type: {event.get('event_type', 'N/A')}
- Sous-type: {event.get('event_subtype', 'N/A')}
- Titre: {event.get('title', 'N/A')}
- Date de publication: {event.get('publication_date', 'N/A')}
- Résumé: {event.get('summary', 'N/A')}
"""
        
        if event.get('geographic_scope', {}).get('coordinates'):
            coords = event['geographic_scope']['coordinates']
            event_info += f"- Localisation: Lat {coords['latitude']}, Lon {coords['longitude']}\n"
        
        if event.get('extra_metadata', {}).get('duration_hours'):
            event_info += f"- Durée estimée: {event['extra_metadata']['duration_hours']} heures\n"
        
        # Formater les informations sur l'entité impactée
        if entity_type == "supplier":
            entity_info = self._format_supplier_info(affected_entity, relationships, context)
        else:
            entity_info = self._format_site_info(affected_entity, relationships, context)
        
        # Adapter le prompt selon le type de risque
        event_type = event.get('event_type', 'climatique')
        
        if event_type == "climatique":
            prompt = self._build_climate_prompt(event_info, entity_info, entity_type)
        elif event_type == "reglementaire":
            prompt = self._build_regulatory_prompt(event_info, entity_info, entity_type)
        elif event_type == "geopolitique":
            prompt = self._build_geopolitical_prompt(event_info, entity_info, entity_type)
        else:
            # Fallback sur climatique
            prompt = self._build_climate_prompt(event_info, entity_info, entity_type)
        
        return prompt
    
    def _format_supplier_info(
        self,
        supplier: Dict[str, Any],
        relationships: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Formate les informations sur un fournisseur avec données Business Interruption"""
        
        info = f"""
FOURNISSEUR IMPACTÉ:
- Nom: {supplier.get('name', 'N/A')}
- Pays: {supplier.get('country', 'N/A')}
- Région: {supplier.get('region', 'N/A')}
- Secteur: {supplier.get('sector', 'N/A')}
- Produits fournis: {', '.join(supplier.get('products_supplied', []))}
- Taille entreprise: {supplier.get('company_size', 'N/A')}
- Santé financière: {supplier.get('financial_health', 'N/A')}
"""
        
        if supplier.get('latitude') and supplier.get('longitude'):
            info += f"- Coordonnées: Lat {supplier['latitude']}, Lon {supplier['longitude']}\n"
        
        # DONNÉES BUSINESS INTERRUPTION - depuis context (calculées par agent.py)
        info += "\n⚠️ IMPACT FINANCIER CALCULÉ (Business Interruption):\n"
        
        # Impact total quotidien (donnée la plus importante)
        total_daily_impact = context.get('total_daily_impact_eur', 0)
        if total_daily_impact:
            info += f"- PERTE QUOTIDIENNE TOTALE: {total_daily_impact:,.0f} EUR/jour\n"
            info += f"- Perte sur 1 semaine: {total_daily_impact * 7:,.0f} EUR\n"
            info += f"- Perte sur 1 mois: {total_daily_impact * 30:,.0f} EUR\n"
        
        # CA perdu par jour
        daily_revenue_loss = context.get('daily_revenue_loss_eur', 0)
        if daily_revenue_loss:
            info += f"- Perte de CA quotidienne: {daily_revenue_loss:,.0f} EUR\n"
        
        # Pénalités clients
        customer_penalties = context.get('customer_penalties_per_day_eur', 0)
        if customer_penalties:
            info += f"- Pénalités clients par jour: {customer_penalties:,.0f} EUR\n"
        
        # Stock de sécurité (sursis)
        stock_coverage = context.get('stock_coverage_days', 0)
        if stock_coverage:
            info += f"- Stock de sécurité couvre: {stock_coverage} jours (sursis avant rupture)\n"
        
        # Délai de remplacement
        switch_time = context.get('switch_time_days', 0) or supplier.get('switch_time_days', 0)
        if switch_time:
            info += f"- Délai pour trouver un remplaçant: {switch_time} jours\n"
            if total_daily_impact:
                info += f"  → Coût total de transition: {total_daily_impact * switch_time:,.0f} EUR\n"
        
        # Fournisseur unique ?
        if context.get('is_sole_supplier'):
            info += f"- ⚠️ FOURNISSEUR UNIQUE - Risque critique, aucune alternative immédiate\n"
        
        # Clients affectés
        affected_customers = context.get('affected_customers', [])
        if affected_customers:
            if isinstance(affected_customers, list):
                # Gérer liste de dicts ou liste de strings
                customer_names = []
                for c in affected_customers:
                    if isinstance(c, dict):
                        customer_names.append(c.get('customer_name', str(c)))
                    else:
                        customer_names.append(str(c))
                info += f"- Clients finaux impactés: {', '.join(customer_names)}\n"
            else:
                info += f"- Clients finaux impactés: {affected_customers}\n"
        
        # Sites Hutchinson affectés en aval
        affected_sites = context.get('affected_sites', [])
        if affected_sites:
            info += f"\nSITES HUTCHINSON IMPACTÉS EN AVAL:\n"
            for site in affected_sites:
                if isinstance(site, dict):
                    info += f"  - {site.get('name', 'N/A')}: {site.get('impact_description', 'Impact à évaluer')}\n"
                else:
                    info += f"  - {site}\n"
        
        # Score de criticité fournisseur
        criticality_score = context.get('criticality_score', 0) or supplier.get('criticality_score', 0)
        if criticality_score:
            info += f"\n- Score de criticité fournisseur: {criticality_score}/100\n"
        
        # Ajouter les relations avec les sites Hutchinson
        if relationships:
            info += "\nDÉTAIL DES RELATIONS AVEC HUTCHINSON:\n"
            for rel in relationships:
                info += f"  - Site: {rel.get('site_name', 'N/A')}\n"
                info += f"    Criticité: {rel.get('criticality', 'N/A')}\n"
                info += f"    Fournisseur unique: {'OUI ⚠️' if rel.get('is_unique_supplier') else 'NON'}\n"
                if rel.get('backup_supplier_id'):
                    info += f"    Backup disponible: OUI\n"
                else:
                    info += f"    Backup disponible: NON ⚠️\n"
                info += f"    Volume annuel: {rel.get('annual_volume_eur', 0):,.0f} EUR\n"
                info += f"    Délai de livraison: {rel.get('lead_time_days', 'N/A')} jours\n"
        
        return info
    
    def _format_site_info(
        self,
        site: Dict[str, Any],
        relationships: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Formate les informations sur un site avec données Business Interruption"""
        
        info = f"""
SITE HUTCHINSON IMPACTÉ:
- Nom: {site.get('name', 'N/A')}
- Pays: {site.get('country', 'N/A')}
- Région: {site.get('region', 'N/A')}
- Secteurs: {', '.join(site.get('sectors', []))}
- Produits principaux: {', '.join(site.get('main_products', []))}
- Matières premières: {', '.join(site.get('raw_materials', []))}
- Nombre d'employés: {site.get('employee_count', 'N/A')}
- Valeur de production annuelle: {site.get('annual_production_value', 0):,.0f} EUR
- Importance stratégique: {site.get('strategic_importance', 'N/A')}
"""
        
        if site.get('latitude') and site.get('longitude'):
            info += f"- Coordonnées: Lat {site['latitude']}, Lon {site['longitude']}\n"
        
        # DONNÉES BUSINESS INTERRUPTION - depuis context (calculées par agent.py)
        info += "\n⚠️ IMPACT FINANCIER CALCULÉ (Business Interruption):\n"
        
        # Impact total quotidien (donnée la plus importante - depuis context)
        total_daily_impact = context.get('total_daily_impact_eur', 0)
        if total_daily_impact:
            info += f"- PERTE QUOTIDIENNE TOTALE: {total_daily_impact:,.0f} EUR/jour\n"
            info += f"- Perte sur 1 semaine: {total_daily_impact * 7:,.0f} EUR\n"
            info += f"- Perte sur 1 mois: {total_daily_impact * 30:,.0f} EUR\n"
        
        # CA quotidien (depuis site ou context)
        daily_revenue = context.get('daily_revenue_loss_eur', 0) or site.get('daily_revenue', 0)
        if daily_revenue:
            info += f"- Perte de CA quotidienne: {daily_revenue:,.0f} EUR\n"
        
        # Production quotidienne
        daily_production = site.get('daily_production_units', 0)
        if daily_production:
            info += f"- Production quotidienne: {daily_production:,} unités\n"
        
        # Coût ligne de production
        prod_line_cost = site.get('production_line_cost_per_hour', 0)
        if prod_line_cost:
            info += f"- Coût arrêt ligne de production: {prod_line_cost:,.0f} EUR/heure ({prod_line_cost * 24:,.0f} EUR/jour)\n"
        
        # Stock de sécurité (depuis context ou site)
        safety_stock = context.get('stock_coverage_days', 0) or site.get('safety_stock_days', 0)
        if safety_stock:
            info += f"- Stock de sécurité couvre: {safety_stock} jours (sursis avant rupture)\n"
        
        # Pénalités clients (depuis context ou site)
        customer_penalty = context.get('customer_penalties_per_day_eur', 0) or site.get('customer_penalty_per_day', 0)
        if customer_penalty:
            info += f"- Pénalités clients par jour de retard: {customer_penalty:,.0f} EUR\n"
        
        # Clients clés (depuis context ou site)
        key_customers = context.get('affected_customers', []) or site.get('key_customers', '')
        if key_customers:
            if isinstance(key_customers, list):
                # Gérer liste de dicts ou liste de strings
                customer_names = []
                for c in key_customers:
                    if isinstance(c, dict):
                        customer_names.append(c.get('customer_name', str(c)))
                    else:
                        customer_names.append(str(c))
                info += f"- Clients clés impactés: {', '.join(customer_names)}\n"
            else:
                info += f"- Clients clés impactés: {key_customers}\n"
        
        # Recovery time estimé
        recovery_time = context.get('recovery_time_days', 0) or site.get('recovery_time_days', 0)
        if recovery_time:
            info += f"- Temps de récupération estimé: {recovery_time} jours\n"
            if total_daily_impact:
                info += f"  → Coût total potentiel: {total_daily_impact * recovery_time:,.0f} EUR\n"
        
        # Ajouter les fournisseurs critiques
        if relationships:
            info += "\nFOURNISSEURS CRITIQUES:\n"
            for rel in relationships:
                if rel.get('criticality') in ['Critique', 'Important']:
                    info += f"  - {rel.get('supplier_name', 'N/A')}\n"
                    info += f"    Criticité: {rel.get('criticality', 'N/A')}\n"
                    info += f"    Produits: {', '.join(rel.get('products_supplied', []))}\n"
                    
                    # Données BI du fournisseur
                    switch_time = rel.get('switch_time_days', 0)
                    if switch_time:
                        info += f"    ⚠️ Délai remplacement si défaillance: {switch_time} jours\n"
                    
                    if rel.get('is_unique_supplier'):
                        info += f"    ⚠️ FOURNISSEUR UNIQUE - Risque majeur si impacté\n"
        
        return info
    
    def _build_climate_prompt(self, event_info: str, entity_info: str, entity_type: str) -> str:
        """Construit un prompt spécifique pour les risques climatiques"""
        
        return f"""Tu es un expert en gestion des risques climatiques pour la supply chain de Hutchinson.

{event_info}

{entity_info}

ANALYSE CLIMATIQUE DEMANDÉE:

IMPORTANT: Tu disposes ci-dessus de données Business Interruption chiffrées (CA quotidien, pénalités, 
stock de sécurité, coût arrêt ligne, clients clés). 
Utilise ces chiffres pour quantifier PRÉCISÉMENT les impacts financiers.

Pour ce risque CLIMATIQUE (inondation, tempête, sécheresse, etc.), analyse l'impact en cascade :

1. **Probabilité et durée d'impact** :
   - Probabilité que l'entité soit réellement impactée (0.0-1.0)
   - Durée estimée de la perturbation (en jours)
   - Délai avant rétablissement complet

2. **Impact logistique** :
   - Routes et transports perturbés ?
   - Délai avant rupture de stock = stock de sécurité en jours
   - Alternatives logistiques disponibles ?

3. **Cascade sur la production (UTILISER LES DONNÉES BI)** :
   - Sites Hutchinson impactés en aval
   - Arrêt total, partiel ou ralentissement ?
   - Calcul : Manque à gagner = CA quotidien × jours d'interruption
   - Calcul : Coût arrêt = Coût ligne/heure × 24h × jours
   - Calcul : Pénalités = Pénalité/jour × (jours interruption - stock sécurité)
   - Impact sur les livraisons clients (retards estimés)

4. **Niveau de risque** : CRITIQUE, FORT, MOYEN, ou FAIBLE

5. **Recommandations urgentes CHIFFRÉES** :
   - Actions immédiates (24-48h) avec coûts
   - Actions court terme (1 semaine) avec budget
   - Mesures préventives avec ROI

RÉPONDS UNIQUEMENT EN JSON :

{{
  "impact_assessment": {{
    "impact_probability": 0.85,
    "estimated_impact_duration_days": 7,
    "cascade_analysis": {{
      "days_until_disruption": 14,
      "affected_downstream_entities": ["Site1", "Site2"],
      "production_impact": "Description détaillée avec chiffres",
      "customer_impact": "Clients impactés et pénalités estimées",
      "daily_financial_impact_eur": 200000,
      "total_financial_impact_eur": 500000,
      "breakdown": {{
        "lost_revenue_eur": 300000,
        "production_line_costs_eur": 120000,
        "customer_penalties_eur": 80000
      }}
    }}
  }},
  "overall_risk_level": "CRITIQUE",
  "risk_reasoning": "Explication avec chiffres",
  "recommendations": [
    {{
      "action": "Action concrète",
      "urgency": "IMMEDIATE|HIGH|MEDIUM|LOW",
      "timeline": "Délai précis",
      "estimated_cost_eur": 25000,
      "expected_benefit": "Réduction du risque de X%",
      "rationale": "ROI : investir X€ pour éviter Y€ de pertes"
    }}
  ]
}}
"""
    
    def _build_regulatory_prompt(self, event_info: str, entity_info: str, entity_type: str) -> str:
        """Construit un prompt spécifique pour les risques réglementaires"""
        
        return f"""Tu es un expert en conformité réglementaire et gestion des risques légaux pour Hutchinson.

{event_info}

{entity_info}

ANALYSE RÉGLEMENTAIRE DEMANDÉE:

IMPORTANT: Tu disposes ci-dessus de données Business Interruption chiffrées (CA quotidien, pénalités, stock, délais).
Utilise ces chiffres pour quantifier PRÉCISÉMENT les impacts financiers dans ton analyse.

Pour ce risque RÉGLEMENTAIRE (nouvelle loi, norme, taxe, sanction, etc.), analyse l'impact en cascade :

1. **Applicabilité et conformité** :
   - Probabilité que l'entité soit concernée par cette réglementation (0.0-1.0)
   - L'entité est-elle actuellement conforme ?
   - Délai pour se mettre en conformité (en jours)

2. **Coûts et investissements (CHIFFRER PRÉCISÉMENT)** :
   - Coût estimé de mise en conformité (€)
   - Investissements nécessaires (certifications, équipements, formations)
   - Impact sur les coûts opérationnels (taxes, pénalités potentielles)
   - Pénalités en cas de non-conformité (€)

3. **Impact sur la compétitivité** :
   - Avantage ou désavantage compétitif ?
   - Impact sur les clients Hutchinson
   - Risque de perte de marché ou d'opportunités (€)

4. **Cascade sur Hutchinson (UTILISER LES DONNÉES BI)** :
   - Sites ou produits Hutchinson impactés
   - Risque de non-conformité en cascade
   - Impact sur la chaîne de valeur
   - Manque à gagner si non-conformité (utiliser CA quotidien × durée estimée)

5. **Niveau de risque** : CRITIQUE, FORT, MOYEN, ou FAIBLE

6. **Recommandations stratégiques CHIFFRÉES** :
   - Actions de conformité avec coûts estimés
   - ROI des investissements de conformité
   - Délais et jalons
   - Alternatives ou adaptations possibles

RÉPONDS UNIQUEMENT EN JSON :

{{
  "impact_assessment": {{
    "impact_probability": 0.90,
    "estimated_impact_duration_days": 180,
    "cascade_analysis": {{
      "days_until_disruption": 90,
      "affected_downstream_entities": ["Site1", "Product Line X"],
      "production_impact": "Description",
      "customer_impact": "Description",
      "financial_impact_estimate_eur": 1000000
    }}
  }},
  "overall_risk_level": "FORT",
  "risk_reasoning": "Explication",
  "recommendations": [
    {{
      "action": "Action",
      "urgency": "IMMEDIATE|HIGH|MEDIUM|LOW",
      "timeline": "Délai",
      "rationale": "Raison"
    }}
  ]
}}
"""
    
    def _build_geopolitical_prompt(self, event_info: str, entity_info: str, entity_type: str) -> str:
        """Construit un prompt spécifique pour les risques géopolitiques"""
        
        return f"""Tu es un expert en risques géopolitiques et sécurité de la supply chain pour Hutchinson.

{event_info}

{entity_info}

ANALYSE GÉOPOLITIQUE DEMANDÉE:

IMPORTANT: Tu disposes ci-dessus de données Business Interruption chiffrées (CA quotidien, pénalités, 
délai de remplacement fournisseur, stock de sécurité, clients clés). 
Utilise ces chiffres pour quantifier PRÉCISÉMENT les impacts financiers.

Pour ce risque GÉOPOLITIQUE (conflit, sanctions, instabilité, etc.), analyse l'impact en cascade :

1. **Probabilité et durée** :
   - Probabilité que l'entité soit impactée (0.0-1.0)
   - Durée estimée de la crise (en jours/mois)
   - Risque d'escalade ou d'évolution

2. **Impact direct (CHIFFRER)** :
   - Sanctions économiques applicables ?
   - Fermeture de frontières ou restrictions commerciales ?
   - Sécurité des employés et des installations
   - Perte de CA estimée par jour (utiliser données BI fournies)

3. **Impact sur les routes commerciales** :
   - Routes logistiques perturbées ou fermées ?
   - Alternatives disponibles (coûts additionnels, délais) ?
   - Dépendance aux pays concernés

4. **Cascade sur Hutchinson (UTILISER LES DONNÉES BI)** :
   - Sites Hutchinson dépendants de cette entité
   - Calcul : Manque à gagner = CA quotidien × jours d'interruption
   - Calcul : Pénalités clients = Pénalité/jour × jours après stock épuisé
   - Produits critiques impactés
   - Délai avant rupture = stock de sécurité (jours)
   - Temps pour remplacer le fournisseur (switch_time_days)
   - Impact total = perte CA + pénalités + coût transition

5. **Niveau de risque** : CRITIQUE, FORT, MOYEN, ou FAIBLE

6. **Recommandations stratégiques CHIFFRÉES** :
   - Actions immédiates avec coûts (sécurité, continuité)
   - Coût de la diversification géographique vs coût du risque
   - Plans de contingence avec budget estimé
   - ROI des mesures préventives

RÉPONDS UNIQUEMENT EN JSON :

{{
  "impact_assessment": {{
    "impact_probability": 0.70,
    "estimated_impact_duration_days": 60,
    "cascade_analysis": {{
      "days_until_disruption": 30,
      "affected_downstream_entities": ["Site1", "Site2"],
      "production_impact": "Description détaillée avec chiffres",
      "customer_impact": "Description avec clients nommés et pénalités",
      "daily_financial_impact_eur": 450000,
      "total_financial_impact_eur": 800000,
      "breakdown": {{
        "lost_revenue_eur": 500000,
        "customer_penalties_eur": 200000,
        "transition_costs_eur": 100000
      }}
    }}
  }},
  "overall_risk_level": "FORT",
  "risk_reasoning": "Explication avec chiffres",
  "recommendations": [
    {{
      "action": "Action concrète",
      "urgency": "IMMEDIATE|HIGH|MEDIUM|LOW",
      "timeline": "Délai précis",
      "estimated_cost_eur": 50000,
      "expected_risk_reduction": "Description",
      "rationale": "Raison avec ROI"
    }}
  ]
}}
"""
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Appelle le LLM (OpenAI ou Anthropic) avec le prompt"""
        try:
            if self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=4096
                )
                content = response.choices[0].message.content.strip()
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text.strip()
            
            # Nettoyer le JSON (enlever les markdown code blocks si présents)
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            # Parser la réponse JSON
            result = json.loads(content.strip())
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"⚠️  Failed to parse Claude response as JSON: {e}")
            print(f"Response: {content[:200]}...")
            return self._get_fallback_response()
        except Exception as e:
            print(f"⚠️  Claude API call failed: {e}")
            return self._get_fallback_response()
    
    def _simulate_reasoning(
        self,
        event: Dict[str, Any],
        affected_entity: Dict[str, Any],
        entity_type: str
    ) -> Dict[str, Any]:
        """Simule un raisonnement LLM (fallback)"""
        
        # Raisonnement simplifié basé sur des règles
        impact_prob = 0.75
        duration_days = 7
        
        if event.get('event_type') == 'climatique':
            impact_prob = 0.85
            duration_days = 5
        elif event.get('event_type') == 'geopolitique':
            impact_prob = 0.60
            duration_days = 30
        
        return {
            "impact_assessment": {
                "impact_probability": impact_prob,
                "estimated_impact_duration_days": duration_days,
                "cascade_analysis": {
                    "days_until_disruption": 14,
                    "affected_downstream_entities": ["Entity1", "Entity2"],
                    "production_impact": "Impact modéré sur la production",
                    "customer_impact": "Retards de livraison possibles",
                    "financial_impact_estimate_eur": 100000
                }
            },
            "overall_risk_level": "MOYEN",
            "risk_reasoning": "Analyse basée sur des règles simplifiées (Claude Sonnet non disponible)",
            "recommendations": [
                {
                    "action": "Contacter l'entité pour évaluer la situation",
                    "urgency": "HIGH",
                    "timeline": "Dans les 48h",
                    "rationale": "Obtenir des informations de première main"
                },
                {
                    "action": "Préparer un plan de contingence",
                    "urgency": "MEDIUM",
                    "timeline": "Dans la semaine",
                    "rationale": "Anticiper les disruptions potentielles"
                }
            ]
        }
    
    def _get_fallback_response(self) -> Dict[str, Any]:
        """Retourne une réponse par défaut en cas d'erreur"""
        return {
            "impact_assessment": {
                "impact_probability": 0.5,
                "estimated_impact_duration_days": 7,
                "cascade_analysis": {
                    "days_until_disruption": 14,
                    "affected_downstream_entities": [],
                    "production_impact": "Impact à évaluer",
                    "customer_impact": "Impact à évaluer",
                    "financial_impact_estimate_eur": 0
                }
            },
            "overall_risk_level": "MOYEN",
            "risk_reasoning": "Analyse par défaut (erreur Claude Sonnet)",
            "recommendations": [
                {
                    "action": "Évaluer manuellement la situation",
                    "urgency": "HIGH",
                    "timeline": "Immédiatement",
                    "rationale": "L'analyse automatique a échoué"
                }
            ]
        }
