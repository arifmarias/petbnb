# app/core/websockets.py

from fastapi import WebSocket
from typing import Dict, Set, Optional
import json
from uuid import UUID

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, chat_room_id: str):
        """Connect a user to a specific chat room."""
        await websocket.accept()
        if chat_room_id not in self.active_connections:
            self.active_connections[chat_room_id] = {}
        self.active_connections[chat_room_id][user_id] = websocket
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to chat room successfully"
        })
        
    def disconnect(self, user_id: str, chat_room_id: str):
        """Disconnect a user from a specific chat room."""
        if chat_room_id in self.active_connections:
            if user_id in self.active_connections[chat_room_id]:
                del self.active_connections[chat_room_id][user_id]
                
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        await websocket.send_json(message)
        
    async def broadcast(self, message: dict, chat_room_id: str, exclude_user: Optional[str] = None):
        """Broadcast a message to all users in a chat room except the excluded user."""
        if chat_room_id in self.active_connections:
            for user_id, connection in self.active_connections[chat_room_id].items():
                if user_id != exclude_user:
                    await connection.send_json(message)

manager = ConnectionManager()