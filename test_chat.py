# test_chat.py
import asyncio
import websockets
import json
import httpx
from uuid import UUID
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatTester:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.token = None
        self.client = httpx.AsyncClient()

    async def login(self, email: str, password: str) -> str:
        """Login and get token"""
        response = await self.client.post(
            f"{self.base_url}/auth/login",
            data={
                "username": email,
                "password": password
            }
        )
        data = response.json()
        self.token = data["access_token"]
        return self.token

    async def create_chat_room(self, booking_id: str) -> dict:
        """Create a new chat room"""
        response = await self.client.post(
            f"{self.base_url}/messages/chat-rooms/",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"booking_id": booking_id}
        )
        return response.json()

    async def get_chat_rooms(self) -> list:
        """Get all chat rooms"""
        response = await self.client.get(
            f"{self.base_url}/messages/chat-rooms/",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.json()

    async def get_messages(self, chat_room_id: str) -> list:
        """Get messages from a chat room"""
        response = await self.client.get(
            f"{self.base_url}/messages/chat-rooms/{chat_room_id}/messages/",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return response.json()

    async def handle_websocket_message(self, message_str: str) -> None:
        """Handle incoming WebSocket messages"""
        message = json.loads(message_str)
        message_type = message.get("type")
        
        if message_type == "connection_established":
            logger.info(f"Connection established: {message.get('message')}")
        elif message_type == "message_sent":
            logger.info(f"Message sent and saved: {message.get('message')}")
        elif message_type == "new_message":
            logger.info(f"New message received: {message.get('message')}")
        elif message_type == "error":
            logger.error(f"Error: {message.get('message')}")
        else:
            logger.info(f"Unknown message type: {message_str}")

    async def test_websocket(self, chat_room_id: str):
        """Test WebSocket connection and messaging"""
        uri = f"ws://localhost:8000/api/v1/messages/ws/{chat_room_id}"
        headers = [
            ('Authorization', f'Bearer {self.token}')
        ]
        
        async with websockets.connect(
            uri,
            additional_headers=headers,
            subprotocols=[]
        ) as websocket:
            logger.info("WebSocket connected")

            # Handle welcome message
            welcome = await websocket.recv()
            await self.handle_websocket_message(welcome)

            # Test different types of messages
            test_messages = [
                {"content": "Hello! Testing the chat system.", "is_system_message": False},
                {"content": "This is a second test message.", "is_system_message": False},
                {"content": "Testing message with special characters: !@#$%", "is_system_message": False},
                {"content": "Final test message.", "is_system_message": False}
            ]

            for i, message in enumerate(test_messages, 1):
                logger.info(f"\nSending message {i}/{len(test_messages)}")
                await websocket.send(json.dumps(message))
                logger.info(f"Message sent: {message['content']}")
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    await self.handle_websocket_message(response)
                except asyncio.TimeoutError:
                    logger.warning("No response received within timeout")
                
                await asyncio.sleep(1)

    async def close(self):
        await self.client.aclose()

async def run_test():
    # Configuration - Replace with your values
    EMAIL = "arifmazumder@daffodilvarsity.edu.bd"
    PASSWORD = "test123456"
    BOOKING_ID = "b23c5cee-a6a4-44ea-948d-a1bb069ad7a8"
    
    tester = ChatTester()
    try:
        logger.info("\n1. Testing Login...")
        await tester.login(EMAIL, PASSWORD)
        logger.info("Login successful")

        logger.info("\n2. Getting existing chat rooms...")
        chat_rooms = await tester.get_chat_rooms()
        logger.info(f"Found {len(chat_rooms)} chat rooms")

        logger.info("\n3. Creating new chat room...")
        chat_room = await tester.create_chat_room(BOOKING_ID)
        chat_room_id = chat_room["id"]
        logger.info(f"Created chat room with ID: {chat_room_id}")

        logger.info("\n4. Getting messages from new chat room...")
        messages = await tester.get_messages(chat_room_id)
        logger.info(f"Found {len(messages)} messages")

        logger.info("\n5. Testing WebSocket connection...")
        await tester.test_websocket(chat_room_id)
        logger.info("WebSocket test completed successfully!")

    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        raise e
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(run_test())