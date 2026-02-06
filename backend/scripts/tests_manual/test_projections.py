"""Test de la fonctionnalité save_risk_projections"""

from src.storage.database import get_session
from src.storage.models import Document, PertinenceCheck, HutchinsonSite, Supplier, SupplierRelationship
from src.agent_2.agent import Agent2
from src.orchestration.langgraph_workflow import save_risk_projections
from sqlalchemy import text

session = get_session()

# Récupérer les documents pertinents (OUI ou PARTIELLEMENT)
pertinent_checks = session.query(PertinenceCheck).filter(
    PertinenceCheck.decision.in_(['OUI', 'PARTIELLEMENT'])
).limit(2).all()

print(f'Documents pertinents trouvés: {len(pertinent_checks)}')

if pertinent_checks:
    # Charger les données entreprise
    sites_raw = session.query(HutchinsonSite).filter(HutchinsonSite.active == True).all()
    suppliers_raw = session.query(Supplier).filter(Supplier.active == True).all()
    relationships_raw = session.query(SupplierRelationship).all()
    
    sites = [{
        'id': s.id,
        'site_id': s.code,
        'name': s.name,
        'site_name': s.name,
        'city': s.city,
        'country': s.country,
        'latitude': s.latitude,
        'longitude': s.longitude,
        'site_type': s.sectors[0] if s.sectors else 'Automobile',
        'strategic_importance': s.strategic_importance
    } for s in sites_raw]
    
    suppliers = [{
        'id': s.id,
        'supplier_id': s.code,
        'name': s.name,
        'company_name': s.name,
        'country': s.country,
        'city': s.city,
        'latitude': s.latitude,
        'longitude': s.longitude,
        'criticality': s.financial_health
    } for s in suppliers_raw]
    
    relationships = [{
        'id': r.id,
        'hutchinson_site_id': r.hutchinson_site_id,
        'supplier_id': r.supplier_id,
        'criticality': r.criticality
    } for r in relationships_raw]
    
    print(f'Sites: {len(sites)}, Fournisseurs: {len(suppliers)}')
    
    agent_2 = Agent2()
    
    for check in pertinent_checks:
        doc = session.query(Document).filter(Document.id == check.document_id).first()
        if not doc:
            continue
        
        print(f'\nAnalyse: {doc.title[:50]}...')
        
        document = {
            'id': doc.id,
            'title': doc.title,
            'content': doc.content[:3000] if doc.content else '',
            'event_type': doc.event_type,
            'event_subtype': doc.event_subtype,
            'source_url': doc.source_url,
            'publication_date': str(doc.publication_date) if doc.publication_date else None,
            'geographic_scope': doc.geographic_scope
        }
        
        pertinence_result = {
            'decision': check.decision,
            'confidence': check.confidence,
            'reasoning': check.reasoning,
            'check_id': check.id
        }
        
        risk_analysis, risk_projections = agent_2.analyze(
            document=document,
            pertinence_result=pertinence_result,
            sites=sites,
            suppliers=suppliers,
            supplier_relationships=relationships
        )
        
        print(f'  Projections générées par Agent 2: {len(risk_projections)}')
        
        # Compter les projections concernées
        concerned = [p for p in risk_projections if p.get('is_concerned')]
        print(f'  Entités concernées: {len(concerned)}')
        
        # Sauvegarder les projections
        count = save_risk_projections(doc.id, risk_projections)
        print(f'  → {count} projections sauvegardées en BDD')
        
session.close()

# Vérifier le contenu de la table
print('\n' + '=' * 60)
print('CONTENU DE LA TABLE RISK_PROJECTIONS')
print('=' * 60)

session = get_session()
count = session.execute(text('SELECT COUNT(*) FROM risk_projections')).scalar()
print(f'Total projections: {count}')

if count > 0:
    # Afficher quelques exemples
    rows = session.execute(text('''
        SELECT entity_type, entity_id, risk_score, is_concerned, 
               substr(reasoning, 1, 50) as reasoning_short
        FROM risk_projections 
        ORDER BY risk_score DESC 
        LIMIT 10
    ''')).fetchall()
    
    print('\nTop 10 par risk_score:')
    print('-' * 80)
    for row in rows:
        entity_type, entity_id, risk_score, is_concerned, reasoning = row
        concerned_icon = '✅' if is_concerned else '❌'
        print(f'{concerned_icon} [{entity_type:8}] {entity_id[:15]:15} | Score: {risk_score:5.1f} | {reasoning}...')

session.close()
print('\n✅ Test terminé!')
