"""add_messaging_system

Revision ID: 5d857837466a
Revises: 
Create Date: 2024-11-23 16:01:47.634159

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '5d857837466a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chat_rooms table
    op.create_table(
        'chat_rooms',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('booking_id', UUID(as_uuid=True), sa.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_rooms_id', 'chat_rooms', ['id'])
    op.create_index('ix_chat_rooms_booking_id', 'chat_rooms', ['booking_id'])

    # Create chat_room_participants table
    op.create_table(
        'chat_room_participants',
        sa.Column('chat_room_id', UUID(as_uuid=True), sa.ForeignKey('chat_rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('chat_room_id', 'user_id')
    )
    op.create_index('ix_chat_room_participants_chat_room_id', 'chat_room_participants', ['chat_room_id'])
    op.create_index('ix_chat_room_participants_user_id', 'chat_room_participants', ['user_id'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('chat_room_id', UUID(as_uuid=True), sa.ForeignKey('chat_rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('is_system_message', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_id', 'messages', ['id'])
    op.create_index('ix_messages_chat_room_id', 'messages', ['chat_room_id'])
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])

    # Create message_read_status table
    op.create_table(
        'message_read_status',
        sa.Column('message_id', UUID(as_uuid=True), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('read_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.PrimaryKeyConstraint('message_id', 'user_id')
    )
    op.create_index('ix_message_read_status_message_id', 'message_read_status', ['message_id'])
    op.create_index('ix_message_read_status_user_id', 'message_read_status', ['user_id'])

    # Create updated_at triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Add triggers
    op.execute("""
        CREATE TRIGGER update_chat_rooms_updated_at
            BEFORE UPDATE ON chat_rooms
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_messages_updated_at
            BEFORE UPDATE ON messages
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Add the payment foreign key that was in your original migration
    op.create_foreign_key(None, 'payments', 'payments', ['payment_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key from payments first
    op.drop_constraint(None, 'payments', type_='foreignkey')
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_messages_updated_at ON messages;")
    op.execute("DROP TRIGGER IF EXISTS update_chat_rooms_updated_at ON chat_rooms;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop tables in the correct order
    op.drop_table('message_read_status')
    op.drop_table('messages')
    op.drop_table('chat_room_participants')
    op.drop_table('chat_rooms')