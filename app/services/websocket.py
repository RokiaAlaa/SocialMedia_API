from typing import Dict, List
from fastapi import WebSocket
import json

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """Accept new connection"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        print(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: int, websocket: WebSocket): 
        """Remove connection"""

        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

            print(f"User {user_id} disconnected")

    async def send_personal_message(self, user_id: int, message: dict): 
        """Send message to specific user (all their connections)"""

        if user_id in self.active_connections:
            message_json = json.dumps(message)

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message_json)
                
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")
     
    async def broadcast(self, message: dict): 
        """Broadcast message to all connected users"""

        message_json = json.dumps(message)

        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_text(message_json)
                
                except Exception as e:
                    print(f"Broadcast error: {e}")

    def is_user_online(self, user_id: int) -> bool:
        """Check if user has active connections"""

        return user_id in self.active_connections
    
manager = ConnectionManager()