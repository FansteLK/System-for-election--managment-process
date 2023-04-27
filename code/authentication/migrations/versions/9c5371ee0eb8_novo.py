"""Novo

Revision ID: 9c5371ee0eb8
Revises: a2774f3d6635
Create Date: 2021-07-25 19:49:22.441499

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9c5371ee0eb8'
down_revision = 'a2774f3d6635'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('userrole')
    op.add_column('users', sa.Column('idRole', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'users', 'roles', ['idRole'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'idRole')
    op.create_table('userrole',
    sa.Column('id', mysql.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('idUser', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('idRole', mysql.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['idRole'], ['roles.id'], name='userrole_ibfk_1'),
    sa.ForeignKeyConstraint(['idUser'], ['users.id'], name='userrole_ibfk_2'),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8mb3',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###
