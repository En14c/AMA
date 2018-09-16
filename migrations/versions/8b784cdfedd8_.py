"""empty message

Revision ID: 8b784cdfedd8
Revises: a8176fce55e5
Create Date: 2018-09-14 00:51:46.057766

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b784cdfedd8'
down_revision = 'a8176fce55e5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('about_me', sa.String(length=300), nullable=True))
    op.add_column('users', sa.Column('avatar_hash', sa.String(length=32), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'avatar_hash')
    op.drop_column('users', 'about_me')
    # ### end Alembic commands ###
