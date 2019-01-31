"""rename parameter to parameter_definition

Revision ID: 8c19c53d5701
Revises:
Create Date: 2019-01-24 16:47:21.493240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c19c53d5701'
down_revision = None
branch_labels = None
depends_on = None

naming_convention = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
}

def upgrade():
    try:
        with op.batch_alter_table("next_id") as batch_op:
            batch_op.alter_column('parameter_id', new_column_name='parameter_definition_id')
    except (sa.exc.NoSuchTableError, sa.exc.OperationalError):
        pass
    with op.batch_alter_table("parameter_value", naming_convention=naming_convention) as batch_op:
        batch_op.alter_column('parameter_id', new_column_name='parameter_definition_id')
        batch_op.drop_constraint('fk_parameter_value_parameter_id_parameter')
    op.rename_table('parameter', 'parameter_definition')
    with op.batch_alter_table("parameter_value", naming_convention=naming_convention) as batch_op:
        batch_op.create_foreign_key(
            "fk_parameter_value_parameter_definition_id_parameter_definition",
            "parameter_definition", ["parameter_definition_id"], ["id"])

def downgrade():
    try:
        with op.batch_alter_table("next_id") as batch_op:
            batch_op.alter_column('parameter_definition_id', new_column_name='parameter_id')
    except (sa.exc.NoSuchTableError, sa.exc.OperationalError):
        pass
    with op.batch_alter_table("parameter_value") as batch_op:
        batch_op.alter_column('parameter_definition_id', new_column_name='parameter_id')
        batch_op.drop_constraint('fk_parameter_value_parameter_definition_id_parameter_definition')
    op.rename_table('parameter_definition', 'parameter')
    with op.batch_alter_table("parameter_value", naming_convention=naming_convention) as batch_op:
        batch_op.create_foreign_key(
            "fk_parameter_value_parameter_id_parameter",
            "parameter", ["parameter_id"], ["id"])
