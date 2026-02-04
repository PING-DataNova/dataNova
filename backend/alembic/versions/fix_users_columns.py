"""fix users table columns

Revision ID: fix_users_columns
Revises: a16a190ef818
Create Date: 2026-02-05

Ajoute les colonnes manquantes first_name et last_name à la table users
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_users_columns'
down_revision = 'a16a190ef818'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Vérifier si les colonnes existent déjà avant de les ajouter
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'first_name' not in columns:
        op.add_column('users', sa.Column('first_name', sa.String(length=100), nullable=True))
        # Mettre une valeur par défaut pour les utilisateurs existants
        op.execute("UPDATE users SET first_name = 'Admin' WHERE first_name IS NULL")
        op.alter_column('users', 'first_name', nullable=False)
    
    if 'last_name' not in columns:
        op.add_column('users', sa.Column('last_name', sa.String(length=100), nullable=True))
        # Mettre une valeur par défaut pour les utilisateurs existants
        op.execute("UPDATE users SET last_name = 'User' WHERE last_name IS NULL")
        op.alter_column('users', 'last_name', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
