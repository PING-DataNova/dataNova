"""
Migration Alembic: Ajout des colonnes affected_sites et affected_suppliers à pertinence_checks

Revision ID: 4a8f2b3c9d1e
Revises: 2e485d9c7897
Create Date: 2026-02-01 12:00:00.000000

Description:
    Ajoute deux colonnes JSON à la table PERTINENCE_CHECKS pour stocker les entités affectées:
    - affected_sites: Liste des IDs de sites Hutchinson concernés par l'événement
    - affected_suppliers: Liste des IDs de fournisseurs concernés par l'événement
    
    Ces colonnes permettent à l'Agent 2 de savoir précisément quelles entités analyser
    sans avoir à refaire l'analyse de pertinence.

Auteur: DataNova PING
Date: 2026-02-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '4a8f2b3c9d1e'
down_revision = '2e485d9c7897'  # Dernière migration actuelle
branch_labels = None
depends_on = None


def upgrade():
    """
    Ajoute les colonnes affected_sites et affected_suppliers à pertinence_checks
    """
    # SQLite ne supporte pas ALTER TABLE ADD COLUMN pour JSON directement
    # On utilise donc TEXT qui sera interprété comme JSON par SQLAlchemy
    
    with op.batch_alter_table('pertinence_checks', schema=None) as batch_op:
        # Ajouter affected_sites (JSON array de site IDs)
        batch_op.add_column(
            sa.Column(
                'affected_sites',
                sa.JSON(),
                nullable=True,
                comment='Liste des IDs de sites Hutchinson affectés par cet événement'
            )
        )
        
        # Ajouter affected_suppliers (JSON array de supplier IDs)
        batch_op.add_column(
            sa.Column(
                'affected_suppliers',
                sa.JSON(),
                nullable=True,
                comment='Liste des IDs de fournisseurs affectés par cet événement'
            )
        )
    
    print("✅ Migration upgrade: Colonnes affected_sites et affected_suppliers ajoutées à pertinence_checks")


def downgrade():
    """
    Supprime les colonnes affected_sites et affected_suppliers de pertinence_checks
    """
    with op.batch_alter_table('pertinence_checks', schema=None) as batch_op:
        batch_op.drop_column('affected_suppliers')
        batch_op.drop_column('affected_sites')
    
    print("✅ Migration downgrade: Colonnes affected_sites et affected_suppliers supprimées de pertinence_checks")
