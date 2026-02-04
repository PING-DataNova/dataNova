"""add_detailed_report_sections

Revision ID: 9f8a7b6c4d5e
Revises: 2e485d9c7897
Create Date: 2026-02-04 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f8a7b6c4d5e'
down_revision = '2e485d9c7897'
branch_labels = None
depends_on = None


def upgrade():
    # Ajouter les nouvelles colonnes pour les 7 sections du rapport détaillé
    op.add_column('risk_analyses', sa.Column('context_and_stakes', sa.Text(), nullable=True))
    op.add_column('risk_analyses', sa.Column('affected_entities_details', sa.Text(), nullable=True))
    op.add_column('risk_analyses', sa.Column('financial_analysis', sa.Text(), nullable=True))
    op.add_column('risk_analyses', sa.Column('timeline', sa.Text(), nullable=True))
    op.add_column('risk_analyses', sa.Column('prioritization_matrix', sa.Text(), nullable=True))
    op.add_column('risk_analyses', sa.Column('do_nothing_scenario', sa.Text(), nullable=True))
    
    # Ajouter une colonne pour stocker le modèle utilisé pour les recommandations
    op.add_column('risk_analyses', sa.Column('recommendations_model', sa.String(50), nullable=True))


def downgrade():
    # Supprimer les colonnes en cas de rollback
    op.drop_column('risk_analyses', 'do_nothing_scenario')
    op.drop_column('risk_analyses', 'prioritization_matrix')
    op.drop_column('risk_analyses', 'timeline')
    op.drop_column('risk_analyses', 'financial_analysis')
    op.drop_column('risk_analyses', 'affected_entities_details')
    op.drop_column('risk_analyses', 'context_and_stakes')
    op.drop_column('risk_analyses', 'recommendations_model')
