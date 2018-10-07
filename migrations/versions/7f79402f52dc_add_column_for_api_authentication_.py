"""add column for api authentication tokens to the users table

Revision ID: 7f79402f52dc
Revises: c0c368f0450d
Create Date: 2018-09-30 23:33:53.207716

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f79402f52dc'
down_revision = 'c0c368f0450d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('api_auth_token', sa.String(length=300), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'api_auth_token')
    # ### end Alembic commands ###
