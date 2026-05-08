from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings 
from app.api.router import api_router
from app.core.limiter import limiter
from app.core.logging import logger
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os 

app = FastAPI(
    title=settings.APP_NAME,
    description="Blog/Social Media API with Real-time Feature",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = ['http://localhost:8000', 'http://localhost:3000']

if settings.DEBUG:
    allowed_origins.append("*")
else:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=['localhost', 'localhost:8000', 'localhost:3000', 'testserver']   
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

if not settings.CLOUDINARY_CLOUD_NAME:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event('startup')
async def startup_event():
    logger.info('Applicaton starting up...')

@app.on_event('shutdown')
async def shutdown_event():
    logger.info('Applicaton shutting down...')

@app.get('/')
async def root():
    return {"message": "Blog API", "docs": "/docs", "websocket": "/ws/notifications"}

@app.get('/health')
async def health_checks():
    return {"status": "healthy"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Blog/Social Media API",
        version="1.0.0",
        description="""
# Blog/Social Media API

Complete social media backend with real-time features.

## Features

* **User System**: Authentication, profiles, avatars
* **Posts**: Create, edit, delete with images and tags
* **Interactions**: Comments (nested), likes/reactions
* **Social**: Follow system, personalized feed
* **Real-time**: WebSocket notifications
* **Search**: Full-text search, tags
* **File Upload**: Local and cloud (Cloudinary)

## Authentication

Include JWT token in Authorization header:

Authorization: Bearer <token>

## WebSocket

Connect to `/ws/notifications?token=<jwt_token>` for real-time notifications.
""",
    routes=app.routes
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)