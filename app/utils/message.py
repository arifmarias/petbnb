# app/utils/message.py
import re
from typing import Tuple, Optional
from app.models.booking import Booking
from sqlalchemy.orm import Session

class MessageValidator:
    @staticmethod
    def contains_contact_info(content: str) -> Tuple[bool, Optional[str]]:
        """Check if message contains contact information."""
        patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'social_media': r'(?:(?:http|https):\/\/)?(?:www\.)?(?:instagram\.com|facebook\.com|twitter\.com|linkedin\.com)\/[a-zA-Z0-9_\.]+',
            'whatsapp': r'(?i)(?:whatsapp|wa\.me|whatsapp\.com)',
            'telegram': r'(?i)(?:telegram|t\.me)',
        }
        
        for contact_type, pattern in patterns.items():
            if re.search(pattern, content):
                return True, f"Message contains {contact_type}"
        return False, None

    @staticmethod
    async def can_share_contact_info(db: Session, chat_room_id: int) -> bool:
        """Check if users in a chat room can share contact information."""
        chat_room = db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()
        if not chat_room or not chat_room.booking_id:
            return False
            
        booking = db.query(Booking).filter(Booking.id == chat_room.booking_id).first()
        if not booking:
            return False
            
        # Allow contact sharing if booking is confirmed and paid
        return booking.status == "CONFIRMED" and booking.payment_status == "PAID"

    @staticmethod
    async def validate_message(db: Session, chat_room_id: int, content: str) -> Tuple[bool, Optional[str]]:
        """Validate message content based on booking status."""
        has_contact_info, info_type = MessageValidator.contains_contact_info(content)
        
        if not has_contact_info:
            return True, None
            
        can_share = await MessageValidator.can_share_contact_info(db, chat_room_id)
        if not can_share:
            return False, "Contact information can only be shared after booking is confirmed and paid"
            
        return True, None