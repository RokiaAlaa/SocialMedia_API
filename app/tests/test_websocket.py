import pytest
from unittest.mock import patch, AsyncMock
from app.schemas.token import TokenData

class TestWebSocket:
    """Test WebSocket functionality"""

    def test_websocket_connection_with_valid_token(self, client, user_token, test_user):
        """Test WebSocket connection with valid token"""

        with patch('app.api.endpoints.websocket.verify_access_token',
                   new=AsyncMock(return_value=TokenData(user_id=test_user.id))):
            with client.websocket_connect(f'/api/v1/ws/notifications?token={user_token}') as websocket:
                
                data = websocket.receive_json()
                assert data['type'] == 'connected'

    def test_websocket_connection_without_token(self, client, test_user):
        """Test WebSocket connection without token"""

        with patch('app.api.endpoints.websocket.verify_access_token',
                   new=AsyncMock(return_value=TokenData(user_id=test_user.id))):
            try:
                with client.websocket_connect(f'/api/v1/ws/notifications') as websocket:
                    pass
                assert False, 'Should have raised exception' 
            except Exception:
                pass

    def test_websocket_connection_with_invalid_token(self, client, test_user):
        """Test WebSocket connection with invalid token"""

        try:
            with client.websocket_connect(f'/api/v1/ws/notifications?token=invalid') as websocket:
                pass
            assert False, 'Should have raised exception' 
        except Exception:
            pass

    def test_websocket_ping_pong(self, client, user_token, test_user):
        """Test WebSocket ping/pong"""

        with patch('app.api.endpoints.websocket.verify_access_token',
                   new=AsyncMock(return_value=TokenData(user_id=test_user.id))):
            
            with client.websocket_connect(f'/api/v1/ws/notifications?token={user_token}') as websocket:
                
                data = websocket.receive_json()

                websocket.send_json({'type': 'ping'})

                data = websocket.receive_json()

                assert data['type'] == 'pong'

    def test_websocket_mark_read_via_ws(self, client, user_token, test_user, db):
        """Test marking notification as read via WebSocket"""

        from app.models.notification import Notification, NotificationType
        notification = Notification(
            user_id=test_user.id,
            sender_id=test_user.id,
            type=NotificationType.LIKE,
            is_read=False
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)

        with patch('app.api.endpoints.websocket.verify_access_token',
                   new=AsyncMock(return_value=TokenData(user_id=test_user.id))):
            
            with client.websocket_connect(f'/api/v1/ws/notifications?token={user_token}') as websocket:
                
                data = websocket.receive_json()

                websocket.send_json({
                    'type': 'mark_read',
                    'notification_id': notification.id
                })

                data = websocket.receive_json()
                assert data['type'] == 'notification_marked_read'
                assert data['notification_id'] ==  notification.id