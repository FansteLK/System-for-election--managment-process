"""Migracija

Revision ID: 1298f114f710
Revises: 
Create Date: 2021-07-20 15:33:56.740549

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1298f114f710'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('election',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('election_begining', sa.DateTime(), nullable=False),
    sa.Column('election_ending', sa.DateTime(), nullable=False),
    sa.Column('type', sa.String(length=1), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('participants',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=False),
    sa.Column('type', sa.String(length=1), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('vote',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('jmbg', sa.String(length=13), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('election_participant',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('IdParticipant', sa.Integer(), nullable=False),
    sa.Column('IdElection', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['IdElection'], ['election.id'], ),
    sa.ForeignKeyConstraint(['IdParticipant'], ['participants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('election_participant')
    op.drop_table('vote')
    op.drop_table('participants')
    op.drop_table('election')
    # ### end Alembic commands ###