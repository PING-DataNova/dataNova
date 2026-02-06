"""
Alembic migration : Ajout du champ celex_id à la table documents
"""
from alembic import op
import sqlalchemy as sa

# Révision Alembic
revision = '20260205_add_celex_id_to_documents'
down_revision = 'a16a190ef818'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('documents', sa.Column('celex_id', sa.String(50), nullable=True))

def downgrade():
    op.drop_column('documents', 'celex_id')