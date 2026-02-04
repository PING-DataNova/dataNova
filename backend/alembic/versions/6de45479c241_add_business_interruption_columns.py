"""add_business_interruption_columns

Revision ID: 6de45479c241
Revises: 4a8f2b3c9d1e
Create Date: 2026-02-03 19:02:44.162149

Migration pour ajouter les colonnes Business Interruption aux tables:
- hutchinson_sites (production, stocks, clients)
- suppliers (volumes, contingence)
- supplier_relationships (consommation, stocks, contrats)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6de45479c241'
down_revision = '4a8f2b3c9d1e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # HUTCHINSON_SITES - Colonnes Business Interruption
    # DÉJÀ APPLIQUÉ (colonnes existent dans la BDD)
    # =========================================================================
    
    # Production - Données journalières
    # op.add_column('hutchinson_sites', sa.Column('daily_revenue', sa.Float(), nullable=True))
    # op.add_column('hutchinson_sites', sa.Column('daily_production_units', sa.Integer(), nullable=True))
    # op.add_column('hutchinson_sites', sa.Column('production_capacity_utilization', sa.Float(), nullable=True))
    
    # Stocks - Couverture en jours
    # op.add_column('hutchinson_sites', sa.Column('raw_material_stock_days', sa.JSON(), nullable=True))
    # op.add_column('hutchinson_sites', sa.Column('finished_goods_stock_days', sa.Integer(), nullable=True))
    # op.add_column('hutchinson_sites', sa.Column('safety_stock_days', sa.Integer(), nullable=True))
    
    # Clients - Impact downstream
    # op.add_column('hutchinson_sites', sa.Column('key_customers', sa.JSON(), nullable=True))
    # op.add_column('hutchinson_sites', sa.Column('customer_contracts_penalties', sa.Float(), nullable=True))
    
    # Flexibilité - Capacité de repli
    # op.add_column('hutchinson_sites', sa.Column('backup_production_sites', sa.JSON(), nullable=True))
    # op.add_column('hutchinson_sites', sa.Column('ramp_up_time_days', sa.Integer(), nullable=True))
    # op.add_column('hutchinson_sites', sa.Column('can_work_overtime', sa.Boolean(), nullable=True))
    # op.add_column('hutchinson_sites', sa.Column('max_overtime_capacity_percent', sa.Float(), nullable=True))
    
    # =========================================================================
    # SUPPLIERS - Colonnes Business Interruption
    # DÉJÀ APPLIQUÉ (colonnes existent dans la BDD)
    # =========================================================================
    
    # Volumes réels
    # op.add_column('suppliers', sa.Column('annual_purchase_volume', sa.Float(), nullable=True))
    # op.add_column('suppliers', sa.Column('daily_delivery_value', sa.Float(), nullable=True))
    
    # Stocks chez Hutchinson
    # op.add_column('suppliers', sa.Column('average_stock_at_hutchinson_days', sa.Integer(), nullable=True))
    
    # Contingence - Fournisseur backup
    # op.add_column('suppliers', sa.Column('alternative_supplier_id', sa.String(), nullable=True))
    # op.add_column('suppliers', sa.Column('switch_time_days', sa.Integer(), nullable=True))
    # op.add_column('suppliers', sa.Column('qualification_time_days', sa.Integer(), nullable=True))
    
    # Capacité de réponse
    # op.add_column('suppliers', sa.Column('can_increase_capacity', sa.Boolean(), nullable=True))
    # op.add_column('suppliers', sa.Column('max_capacity_increase_percent', sa.Float(), nullable=True))
    # op.add_column('suppliers', sa.Column('lead_time_express_days', sa.Integer(), nullable=True))
    
    # Score de criticité
    # op.add_column('suppliers', sa.Column('criticality_score', sa.Integer(), nullable=True))
    
    # =========================================================================
    # SUPPLIER_RELATIONSHIPS - Colonnes Business Interruption
    # À APPLIQUER
    # =========================================================================
    
    # Consommation réelle
    op.add_column('supplier_relationships', sa.Column('daily_consumption_value', sa.Float(), nullable=True))
    op.add_column('supplier_relationships', sa.Column('daily_consumption_units', sa.Integer(), nullable=True))
    
    # Stock spécifique à cette relation
    op.add_column('supplier_relationships', sa.Column('stock_coverage_days', sa.Integer(), nullable=True))
    op.add_column('supplier_relationships', sa.Column('min_stock_days', sa.Integer(), nullable=True))
    op.add_column('supplier_relationships', sa.Column('max_stock_days', sa.Integer(), nullable=True))
    
    # Impact contractuel
    op.add_column('supplier_relationships', sa.Column('contract_penalties_per_day', sa.Float(), nullable=True))
    op.add_column('supplier_relationships', sa.Column('contract_bonus_per_day', sa.Float(), nullable=True))
    
    # Commandes
    op.add_column('supplier_relationships', sa.Column('minimum_order_quantity', sa.Float(), nullable=True))
    op.add_column('supplier_relationships', sa.Column('minimum_order_value', sa.Float(), nullable=True))
    op.add_column('supplier_relationships', sa.Column('lead_time_normal_days', sa.Integer(), nullable=True))
    op.add_column('supplier_relationships', sa.Column('lead_time_urgent_days', sa.Integer(), nullable=True))
    op.add_column('supplier_relationships', sa.Column('urgent_delivery_surcharge_percent', sa.Float(), nullable=True))
    
    # Production impactée
    op.add_column('supplier_relationships', sa.Column('production_lines_dependent', sa.JSON(), nullable=True))
    op.add_column('supplier_relationships', sa.Column('percent_site_production_dependent', sa.Float(), nullable=True))


def downgrade() -> None:
    # =========================================================================
    # SUPPLIER_RELATIONSHIPS - Suppression colonnes BI
    # =========================================================================
    op.drop_column('supplier_relationships', 'percent_site_production_dependent')
    op.drop_column('supplier_relationships', 'production_lines_dependent')
    op.drop_column('supplier_relationships', 'urgent_delivery_surcharge_percent')
    op.drop_column('supplier_relationships', 'lead_time_urgent_days')
    op.drop_column('supplier_relationships', 'lead_time_normal_days')
    op.drop_column('supplier_relationships', 'minimum_order_value')
    op.drop_column('supplier_relationships', 'minimum_order_quantity')
    op.drop_column('supplier_relationships', 'contract_bonus_per_day')
    op.drop_column('supplier_relationships', 'contract_penalties_per_day')
    op.drop_column('supplier_relationships', 'max_stock_days')
    op.drop_column('supplier_relationships', 'min_stock_days')
    op.drop_column('supplier_relationships', 'stock_coverage_days')
    op.drop_column('supplier_relationships', 'daily_consumption_units')
    op.drop_column('supplier_relationships', 'daily_consumption_value')
    
    # =========================================================================
    # SUPPLIERS - Suppression colonnes BI
    # =========================================================================
    op.drop_column('suppliers', 'criticality_score')
    op.drop_column('suppliers', 'lead_time_express_days')
    op.drop_column('suppliers', 'max_capacity_increase_percent')
    op.drop_column('suppliers', 'can_increase_capacity')
    op.drop_column('suppliers', 'qualification_time_days')
    op.drop_column('suppliers', 'switch_time_days')
    op.drop_column('suppliers', 'alternative_supplier_id')
    op.drop_column('suppliers', 'average_stock_at_hutchinson_days')
    op.drop_column('suppliers', 'daily_delivery_value')
    op.drop_column('suppliers', 'annual_purchase_volume')
    
    # =========================================================================
    # HUTCHINSON_SITES - Suppression colonnes BI
    # =========================================================================
    op.drop_column('hutchinson_sites', 'max_overtime_capacity_percent')
    op.drop_column('hutchinson_sites', 'can_work_overtime')
    op.drop_column('hutchinson_sites', 'ramp_up_time_days')
    op.drop_column('hutchinson_sites', 'backup_production_sites')
    op.drop_column('hutchinson_sites', 'customer_contracts_penalties')
    op.drop_column('hutchinson_sites', 'key_customers')
    op.drop_column('hutchinson_sites', 'safety_stock_days')
    op.drop_column('hutchinson_sites', 'finished_goods_stock_days')
    op.drop_column('hutchinson_sites', 'raw_material_stock_days')
    op.drop_column('hutchinson_sites', 'production_capacity_utilization')
    op.drop_column('hutchinson_sites', 'daily_production_units')
    op.drop_column('hutchinson_sites', 'daily_revenue')
