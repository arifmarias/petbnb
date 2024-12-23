"""update_image_and_pet_relationships

Revision ID: 7da956087083
Revises: fda3ff566b9b
Create Date: 2024-11-28 11:56:10.850720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7da956087083'
down_revision: Union[str, None] = 'fda3ff566b9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('fk_user_images', 'images', type_='foreignkey')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('fk_user_images', 'images', 'users', ['entity_id'], ['id'], initially='DEFERRED', deferrable=True)
    # ### end Alembic commands ###
