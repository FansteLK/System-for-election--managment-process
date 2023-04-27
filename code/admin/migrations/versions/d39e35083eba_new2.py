"""new2

Revision ID: d39e35083eba
Revises: 4aecaed3fc0c
Create Date: 2021-07-23 00:01:00.333129

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'd39e35083eba'
down_revision = '4aecaed3fc0c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('election_participant', sa.Column('pollnumber', sa.Integer(), nullable=True))
    op.drop_column('election_participant', 'id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('election_participant', sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False))
    op.drop_column('election_participant', 'pollnumber')
    # ### end Alembic commands ###