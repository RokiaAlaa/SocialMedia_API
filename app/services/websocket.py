from typing import Dict, List
from fastapi import WebSocket
import json
from app.services.cache import redis_client

class ConnectionManager:
    """Manage WebSocket connections"""

    MAX_CONNECTIONS_PER_USER = 5

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """Accept new connection, returns False if limit exceeded"""

        await websocket.accept()

        pipe = redis_client.pipeline()
        pipe.incr(f'ws:connection:{user_id}')
        pipe.expire(f'ws:connection:{user_id}', 86400)
        results = await pipe.execute()
        conn_count = results[0]

        if conn_count > self.MAX_CONNECTIONS_PER_USER:
            await redis_client.decr(f'ws:connection:{user_id}')
            await websocket.close(code=1008)
            return False

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

        print(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
        return True

    async def disconnect(self, user_id: int, websocket: WebSocket): 
        """Remove connection"""

        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

            print(f"User {user_id} disconnected")

    async def send_personal_message(self, user_id: int, message: dict): 
        """Send message to specific user (all their connections)"""

        if user_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        dead_connections = []

        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                dead_connections.append(connection)

        for conn in dead_connections:
            await self.disconnect(user_id, conn)
     
    async def broadcast(self, message: dict): 
        """Broadcast message to all connected users"""

        message_json = json.dumps(message)
        dead_connections = []

        for user_id, user_connections in self.active_connections.items():
            for connection in user_connections:
                try:
                    await connection.send_text(message_json)
                
                except Exception as e:
                    print(f"Broadcast error: {e}")
                    dead_connections.append((user_id, connection))
                
        for user_id, conn in dead_connections:
            await self.disconnect(user_id, conn)

    def is_user_online(self, user_id: int) -> bool:
        """Check if user has active connections"""

        return user_id in self.active_connections
    
manager = ConnectionManager()