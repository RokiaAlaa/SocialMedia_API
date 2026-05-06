from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps.database import get_db
from app.core.security import verify_access_token
from app.models.user import User
from app.services.websocket import manager
import json

router = APIRouter()

@router.websocket('/ws/notifications')
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time notifications"""
    
    token_data = await verify_access_token(token)


    if not token_data or not token_data.user_id:
        await websocket.close(code=1008)
        return
    
    user_id = token_data.user_id
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        await websocket.close(code=1008)
        return

    await manager.connect(user_id, websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to notifications"
        })

        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                
                if message.get("type") == 'ping':
                    await websocket.send_json({'type': 'pong'})
                
                elif message.get('type') == 'mark_read':
                    notification_id = message.get('notification_id')

                    if notification_id:
                        from app.models.notification import Notification
                        notification = db.query(Notification).filter(
                            Notification.id == notification_id,
                            Notification.user_id == user_id
                        ).first()

                        if notification:
                            notification.is_read = True
                            db.commit()

                            await websocket.send_json({
                                'type': 'notification_marked_read',
                                'notification_id': notification_id
                            })

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)

    except Exception as e:
        print(f"Websocket error: {e}")
        manager.disconnect(user_id, websocket)