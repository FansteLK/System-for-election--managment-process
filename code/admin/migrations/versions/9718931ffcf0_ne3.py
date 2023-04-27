"""ne3

Revision ID: 9718931ffcf0
Revises: d39e35083eba
Create Date: 2021-07-23 00:13:59.907684

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9718931ffcf0'
down_revision = 'd39e35083eba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('election_participant', sa.Column('guid', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('election_participant', 'guid')
    # ### end Alembic commands ###
