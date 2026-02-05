"""add_risk_projections_and_360_scores

Revision ID: 2e485d9c7897
Revises: af4473498229
Create Date: 2026-02-01 08:53:04.699530

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e485d9c7897'
down_revision = 'af4473498229'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migration pour ajouter:
    1. Table RISK_TYPES (3 types de risques paramétrables)
    2. Table RISK_PROJECTIONS (projection sur chaque entité)
    3. Nouvelles colonnes dans RISK_ANALYSES (360° Risk Score, Business Interruption)
    """
    
    # ========================================
    # 1. Créer la table RISK_TYPES
    # ========================================
    op.create_table('risk_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Insérer les 3 types de risques par défaut
    op.execute("""
        INSERT INTO risk_types (name, description, keywords, sources, active) VALUES
        (
            'Réglementaire',
            'Risques liés aux réglementations, lois et directives',
            '["CBAM", "EUR-Lex", "réglementation", "loi", "directive", "norme", "conformité"]',
            '[{"type": "web", "url": "https://eur-lex.europa.eu"}, {"type": "web", "url": "https://www.legifrance.gouv.fr"}]',
            true
        ),
        (
            'Climatique',
            'Risques liés aux événements climatiques et catastrophes naturelles',
            '["inondation", "tempête", "sécheresse", "canicule", "ouragan", "cyclone", "tremblement de terre", "tsunami"]',
            '[{"type": "api", "url": "https://api.weatherapi.com"}, {"type": "web", "url": "https://www.meteo-france.fr"}]',
            true
        ),
        (
            'Géopolitique',
            'Risques liés aux conflits, tensions géopolitiques et sanctions',
            '["conflit", "guerre", "sanction", "embargo", "tension", "crise", "instabilité", "coup d''état"]',
            '[{"type": "web", "url": "https://www.diplomatie.gouv.fr"}, {"type": "web", "url": "https://www.un.org"}]',
            true
        )
    """)
    
    # ========================================
    # 2. Créer la table RISK_PROJECTIONS
    # ========================================
    op.create_table('risk_projections',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        
        # Scores
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('impact_score', sa.Float(), nullable=True),
        sa.Column('business_interruption_score', sa.Float(), nullable=True),
        
        # Détails
        sa.Column('is_concerned', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('estimated_disruption_days', sa.Integer(), nullable=True),
        sa.Column('revenue_impact_percentage', sa.Float(), nullable=True),
        
        # Sous-scores pour 360° Risk Score
        sa.Column('severity_score', sa.Float(), nullable=True),
        sa.Column('probability_score', sa.Float(), nullable=True),
        sa.Column('exposure_score', sa.Float(), nullable=True),
        sa.Column('urgency_score', sa.Float(), nullable=True),
        
        # Métadonnées
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Contraintes (guillemets simples pour PostgreSQL)
        sa.CheckConstraint("entity_type IN ('site', 'supplier')", name='check_entity_type'),
        sa.CheckConstraint('risk_score >= 0 AND risk_score <= 100', name='check_risk_score_range'),
        sa.ForeignKeyConstraint(['event_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Index pour performance
    op.create_index('idx_risk_projections_event', 'risk_projections', ['event_id'])
    op.create_index('idx_risk_projections_entity', 'risk_projections', ['entity_id'])
    op.create_index('idx_risk_projections_concerned', 'risk_projections', ['is_concerned'])
    op.create_index('idx_risk_projections_entity_type', 'risk_projections', ['entity_type'])
    
    # ========================================
    # 3. Ajouter les nouvelles colonnes dans RISK_ANALYSES
    # ========================================
    
    # Sous-scores pour 360° Risk Score
    op.add_column('risk_analyses', sa.Column('severity_score', sa.Float(), nullable=True))
    op.add_column('risk_analyses', sa.Column('probability_score', sa.Float(), nullable=True))
    op.add_column('risk_analyses', sa.Column('exposure_score', sa.Float(), nullable=True))
    op.add_column('risk_analyses', sa.Column('urgency_score', sa.Float(), nullable=True))
    
    # Score composite 360°
    op.add_column('risk_analyses', sa.Column('risk_score_360', sa.Float(), nullable=True))
    
    # Business Interruption Score
    op.add_column('risk_analyses', sa.Column('business_interruption_score', sa.Float(), nullable=True))
    op.add_column('risk_analyses', sa.Column('estimated_disruption_days', sa.Integer(), nullable=True))
    op.add_column('risk_analyses', sa.Column('revenue_impact_percentage', sa.Float(), nullable=True))
    
    # Lien optionnel vers RISK_TYPES (pas de FK avec SQLite en ALTER TABLE)
    op.add_column('risk_analyses', sa.Column('risk_type_id', sa.Integer(), nullable=True))
    
    # Index pour performance
    op.create_index('idx_risk_analyses_risk_type', 'risk_analyses', ['risk_type_id'])


def downgrade() -> None:
    """
    Rollback de la migration
    """
    
    # Supprimer les index
    op.drop_index('idx_risk_analyses_risk_type', table_name='risk_analyses')
    op.drop_index('idx_risk_projections_entity_type', table_name='risk_projections')
    op.drop_index('idx_risk_projections_concerned', table_name='risk_projections')
    op.drop_index('idx_risk_projections_entity', table_name='risk_projections')
    op.drop_index('idx_risk_projections_event', table_name='risk_projections')
    
    # Supprimer les colonnes de RISK_ANALYSES
    op.drop_column('risk_analyses', 'risk_type_id')
    op.drop_column('risk_analyses', 'revenue_impact_percentage')
    op.drop_column('risk_analyses', 'estimated_disruption_days')
    op.drop_column('risk_analyses', 'business_interruption_score')
    op.drop_column('risk_analyses', 'risk_score_360')
    op.drop_column('risk_analyses', 'urgency_score')
    op.drop_column('risk_analyses', 'exposure_score')
    op.drop_column('risk_analyses', 'probability_score')
    op.drop_column('risk_analyses', 'severity_score')
    
    # Supprimer les tables
    op.drop_table('risk_projections')
    op.drop_table('risk_types')
