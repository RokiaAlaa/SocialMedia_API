import os
os.environ['TESTING'] = 'true'

from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.api.deps.database import get_db, Base
from app.core.security import hash_password
from app.models.user import User
from app.models.post import Post
from app.models.tag import Tag

@pytest.fixture(autouse=True)
def disable_rate_limit():
    from app.core.limiter import limiter
    limiter._enabled=False
    yield
    limiter._enabled=True
    
@pytest.fixture(autouse=True)
def mock_redis():
    with patch('app.core.security.redis_client') as mock_security, patch(
              'app.services.cache.redis_client') as mock_cache, patch(
              'app.services.websocket.redis_client') as mock_ws:
        
        mock_security.get = AsyncMock(return_value=None)
        mock_security.set = AsyncMock(return_value=True)
        mock_security.setex = AsyncMock(return_value=True)
        mock_security.delete = AsyncMock(return_value=True)

        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)
        mock_cache.setex = AsyncMock(return_value=True)
        mock_cache.delete = AsyncMock(return_value=True)
        mock_cache.keys = AsyncMock(return_value=[])

        mock_pipe = AsyncMock()
        mock_pipe.incr = AsyncMock()
        mock_pipe.expire = AsyncMock()
        mock_pipe.execute = AsyncMock(return_value=[1, True])
        mock_ws.pipeline = MagicMock(return_value=mock_pipe)
        mock_ws.decr = AsyncMock(return_value=True)
        yield 

SQLALCHEMY_DATABASE_URL='sqlite:///:memory:'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope='function')
def db():
    """Database session for each test"""
    Base.metadata.create_all(bind=engine)
    db=TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope='function')
def client(db):
    """Test client"""
    def override_get_db_with_session():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db_with_session
    yield TestClient(app)
    app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def test_user(db):
    """Create test user"""
    user = User(
        email='test@example.com',
        username='testuser',
        fullname='Test User',
        hashed_password=hash_password('testpass123'),
        bio='Test bio',
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_user2(db):
    """Create second test user"""
    user = User(
        email='test2@example.com',
        username='testuser2',
        fullname='Test User 2',
        hashed_password=hash_password('testpass123'),
        bio='Test bio',
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_post(db, test_user):
    """Create test post"""
    post = Post(
        user_id=test_user.id,
        content='Test post content',
        is_published=True
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@pytest.fixture
def test_tag(db):
    """Create test tag"""
    tag = Tag(
        name='TestTag',
        slug='testslug'
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@pytest.fixture
def user_token(client, test_user):
    """Get JWT token for test user"""
    response = client.post(
        '/api/v1/auth/login',
        data={
            'username': test_user.email,
            'password': 'testpass123'
        }
    )

    return response.json()['access_token']

@pytest.fixture
def user2_token(client, test_user2):
    """Get JWT token for second user"""
    response = client.post(
        '/api/v1/auth/login',
        data={
            'username': test_user2.email,
            'password': 'testpass123'
        }
    )

    return response.json()['access_token']

@pytest.fixture
def user_headers(user_token):
    """Headers with user token"""
    return {'Authorization': f'Bearer {user_token}'}

@pytest.fixture
def user2_headers(user2_token):
    """Headers with user2 token"""
    return {'Authorization': f'Bearer {user2_token}'}

def get_auth_headers(token: str) -> dict:
    """Get authorization headers"""
    return {'Authorization': f'Bearer {token}'}