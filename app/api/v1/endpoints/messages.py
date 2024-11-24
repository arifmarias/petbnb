# app/api/v1/endpoints/messages.py
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import json
import logging

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_ws
from app.core.websockets import manager
from app.models.user import User
from app.models.message import Message, ChatRoom
from app.models.booking import Booking
from app.schemas.message import (
    MessageCreate,
    Message as MessageSchema,
    ChatRoomCreate,
    ChatRoom as ChatRoomSchema,
    MessageRead
)
from app.utils.message import MessageValidator

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat-rooms/", response_model=ChatRoomSchema)
async def create_chat_room(
    chat_room: ChatRoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat room for a booking"""
    if chat_room.booking_id:
        booking = db.query(Booking).filter(Booking.id == chat_room.booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        if current_user.id != booking.owner_id and current_user.id != booking.caregiver_id:
            raise HTTPException(status_code=403, detail="Not authorized to create this chat room")
        
        # Check if chat room already exists for this booking
        existing_chat_room = db.query(ChatRoom).filter(ChatRoom.booking_id == chat_room.booking_id).first()
        if existing_chat_room:
            return existing_chat_room
    
    db_chat_room = ChatRoom(**chat_room.dict())
    db.add(db_chat_room)
    db.commit()
    db.refresh(db_chat_room)

    # Create welcome message
    welcome_msg = Message(
        chat_room_id=db_chat_room.id,
        sender_id=current_user.id,
        content=f"Chat room created for booking {chat_room.booking_id}",
        is_system_message=True
    )
    db.add(welcome_msg)
    db.commit()
    
    return db_chat_room

@router.get("/chat-rooms/{chat_room_id}/messages/", response_model=List[MessageSchema])
async def get_messages(
    chat_room_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages from a specific chat room"""
    chat_room = db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    if chat_room.booking:
        if current_user.id != chat_room.booking.owner_id and current_user.id != chat_room.booking.caregiver_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this chat room")
    
    messages = (
        db.query(Message)
        .filter(Message.chat_room_id == chat_room_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return messages

@router.get("/chat-rooms/", response_model=List[ChatRoomSchema])
async def get_user_chat_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat rooms for the current user"""
    chat_rooms = (
        db.query(ChatRoom)
        .join(Booking)
        .filter(
            (Booking.owner_id == current_user.id) | 
            (Booking.caregiver_id == current_user.id)
        )
        .order_by(ChatRoom.updated_at.desc())
        .all()
    )
    return chat_rooms

@router.post("/messages/{message_id}/read", response_model=MessageRead)
async def mark_message_as_read(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a message as read"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.is_read = True
    db.commit()
    db.refresh(message)
    
    return MessageRead(message_id=message.id, read_at=message.updated_at)

@router.websocket("/ws/{chat_room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_room_id: UUID,
    current_user: User = Depends(get_current_user_ws),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time messaging"""
    try:
        # Verify chat room access
        chat_room = db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()
        if not chat_room:
            await websocket.close(code=4004)
            return
            
        if chat_room.booking:
            if current_user.id != chat_room.booking.owner_id and current_user.id != chat_room.booking.caregiver_id:
                await websocket.close(code=4003)
                return
        
        # Connect to WebSocket
        await manager.connect(websocket, str(current_user.id), str(chat_room_id))
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Validate message content
                is_valid, error_message = await MessageValidator.validate_message(
                    db, 
                    chat_room_id, 
                    message_data["content"]
                )
                
                if not is_valid:
                    await websocket.send_json({
                        "type": "error",
                        "message": error_message
                    })
                    continue
                
                # Create and save message
                db_message = Message(
                    chat_room_id=chat_room_id,
                    sender_id=current_user.id,
                    content=message_data["content"],
                    is_system_message=message_data.get("is_system_message", False)
                )
                db.add(db_message)
                db.commit()
                db.refresh(db_message)
                
                # Update chat room's updated_at timestamp
                chat_room.updated_at = db_message.created_at
                db.commit()
                
                # Send acknowledgment to sender
                await websocket.send_json({
                    "type": "message_sent",
                    "message": {
                        "id": str(db_message.id),
                        "sender_id": str(db_message.sender_id),
                        "content": db_message.content,
                        "created_at": str(db_message.created_at),
                        "is_read": db_message.is_read,
                        "is_system_message": db_message.is_system_message
                    }
                })
                
                # Broadcast to other participants
                await manager.broadcast(
                    {
                        "type": "new_message",
                        "message": {
                            "id": str(db_message.id),
                            "sender_id": str(db_message.sender_id),
                            "content": db_message.content,
                            "created_at": str(db_message.created_at),
                            "is_read": db_message.is_read,
                            "is_system_message": db_message.is_system_message
                        }
                    },
                    str(chat_room_id),
                    exclude_user=str(current_user.id)
                )
                
        except WebSocketDisconnect:
            manager.disconnect(str(current_user.id), str(chat_room_id))
            logger.info(f"Client {current_user.id} disconnected from chat room {chat_room_id}")
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid message format"
            })
        except Exception as e:
            logger.error(f"Error in websocket: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": "An error occurred while processing your message"
            })
            manager.disconnect(str(current_user.id), str(chat_room_id))
            await websocket.close(code=1011)
            
    except Exception as e:
        logger.error(f"Error establishing WebSocket connection: {str(e)}")
        await websocket.close(code=1011)