"""merge_heads

Revision ID: a16a190ef818
Revises: 6de45479c241, 9f8a7b6c4d5e
Create Date: 2026-02-04 01:25:46.779893

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a16a190ef818'
down_revision = ('6de45479c241', '9f8a7b6c4d5e')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
