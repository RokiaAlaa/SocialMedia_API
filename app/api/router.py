from fastapi import APIRouter
from app.api.endpoints import auth,posts,users,comments,likes,follows,tags,notifications,websocket

api_router = APIRouter()

api_router.include_router(auth.router, prefix='/auth', tags=['Authentication'])

api_router.include_router(users.router, prefix='/users', tags=['Users'])

api_router.include_router(posts.router, prefix='/posts', tags=['Posts'])

api_router.include_router(comments.router, tags=['Comments'])

api_router.include_router(likes.router, tags=['Likes'])

api_router.include_router(follows.router, tags=['Follow'])

api_router.include_router(tags.router, prefix='/tags', tags=['Tags'])

api_router.include_router(notifications.router, prefix='/notifications', tags=['Notifications'])

api_router.include_router(websocket.router, prefix='/WebSocket')