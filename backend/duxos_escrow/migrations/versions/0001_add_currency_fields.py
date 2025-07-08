"""Add currency fields to escrow tables

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add currency field to escrows table
    op.add_column('escrows', sa.Column('currency', sa.String(10), nullable=False, server_default='FLOP'))
    
    # Add currency field to escrow_transactions table
    op.add_column('escrow_transactions', sa.Column('currency', sa.String(10), nullable=False, server_default='FLOP'))


def downgrade() -> None:
    # Remove currency fields
    op.drop_column('escrow_transactions', 'currency')
    op.drop_column('escrows', 'currency')
