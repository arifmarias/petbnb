"""Add Owner Images fields

Revision ID: 780c08a97498
Revises: 55f3b7eb85db
Create Date: 2024-11-28 10:06:36.417545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '780c08a97498'
down_revision: Union[str, None] = '55f3b7eb85db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('fk_caregiver_images', 'images', 'caregiver_profiles', ['entity_id'], ['id'], use_alter=True)
    op.create_foreign_key('fk_user_images', 'images', 'users', ['entity_id'], ['id'], use_alter=True)
    op.create_foreign_key('fk_pet_images', 'images', 'pets', ['entity_id'], ['id'], use_alter=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('fk_pet_images', 'images', type_='foreignkey')
    op.drop_constraint('fk_user_images', 'images', type_='foreignkey')
    op.drop_constraint('fk_caregiver_images', 'images', type_='foreignkey')
    # ### end Alembic commands ###
