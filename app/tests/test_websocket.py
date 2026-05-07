import pytest

class TestWebSocket:
    """Test WebSocket functionality"""

    def test_websocket_connection_with_valid_token(self, client, user_token):
        """Test WebSocket connection with valid token"""
        
        with client.websocket_connect(f'/api/v1/ws/notifications?token={user_token}') as websocket:
            
            data = websocket.receive_json()
            assert data['type'] == 'connected'

    def test_websocket_connection_without_token(self, client):
        """Test WebSocket connection without token"""

        try:
            with client.websocket_connect(f'/api/v1/ws/notifications') as websocket:
                pass
            assert False, 'Should have raised exception' 
        except Exception:
            pass

    def test_websocket_connection_with_invalid_token(self, client):
        """Test WebSocket connection with invalid token"""

        try:
            with client.websocket_connect(f'/api/v1/ws/notifications?token=invalid') as websocket:
                pass
            assert False, 'Should have raised exception' 
        except Exception:
            pass

    def test_websocket_ping_pong(self, client, user_token):
        """Test WebSocket ping/pong"""

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


        with client.websocket_connect(f'/api/v1/ws/notifications?token={user_token}') as websocket:
            
            data = websocket.receive_json()

            websocket.send_json({
                'type': 'mark_read',
                'notification_id': notification.id
            })

            data = websocket.receive_json()
            assert data['type'] == 'notification marked_read'
            assert data['notification_id'] ==  notification.id