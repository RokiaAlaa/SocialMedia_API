# Blog/Social Media API 🚀

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com)
[![Tests](https://img.shields.io/badge/Tests-Passing-success.svg)]( https://github.com/RokiaAlaa/SocialMedia_API)
[![Coverage](https://img.shields.io/badge/Coverage-86%25-brightgreen.svg)]( https://github.com/RokiaAlaa/SocialMedia_API)

A production-ready RESTful API for a blog/social media platform with real-time features, built with FastAPI, PostgreSQL, Redis, and WebSockets.

**GitHub**: https://github.com/RokiaAlaa/SocialMedia_API

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [API Endpoints](#-api-endpoints)
- [WebSocket](#-websocket)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Screenshots](#-screenshots)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Functionality
- 🔐 **Authentication & Authorization**: JWT-based auth with secure password hashing
- 👤 **User Profiles**: Customizable profiles with avatar uploads
- 📝 **Posts**: Create, edit, delete posts with images and tags
- 💬 **Comments**: Nested comment system with replies
- ❤️ **Reactions**: Multiple reaction types (like, love, laugh, wow, sad, angry)
- 👥 **Follow System**: Follow/unfollow users with personalized feed
- 🔔 **Real-time Notifications**: WebSocket-based instant notifications
- 🏷️ **Tags**: Organize and discover content with tags
- 🔍 **Search**: Full-text search across posts
- 📊 **Analytics**: View counts, engagement metrics

### Technical Features
- ⚡ **High Performance**: Redis caching, optimized queries
- 🐳 **Docker**: Fully containerized with Docker Compose
- 🧪 **Testing**: 85%+ test coverage with pytest
- 📚 **API Docs**: Auto-generated interactive documentation (Swagger/ReDoc)
- ☁️ **File Upload**: Support for local storage and Cloudinary
- 🔒 **Security**: CORS, input validation, SQL injection prevention
- 📱 **Scalable**: Async operations, connection pooling

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **Redis** - Caching and pub/sub
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation

### Authentication & Security
- **JWT** - JSON Web Tokens
- **Passlib** - Password hashing (bcrypt)
- **Python-Jose** - JWT encoding/decoding

### Real-time
- **WebSockets** - Real-time notifications
- **Redis Pub/Sub** - Message broadcasting

### File Storage
- **Pillow** - Image processing
- **Cloudinary** - Cloud storage (optional)
- **Local Storage** - Development fallback

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Gunicorn** - WSGI server
- **Uvicorn** - ASGI server

### Testing
- **Pytest** - Testing framework
- **Pytest-asyncio** - Async test support
- **HTTPX** - HTTP client for testing
- **Faker** - Test data generation

---

## 🗄️ Database Schema

<img width="1808" height="830" alt="Schema" src="https://github.com/user-attachments/assets/2d4108ab-238c-4699-8c2b-a8939d02c964" />


---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Quick Start (Docker - Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/blog-api.git
cd blog-api

# Create environment file
cp .env.example .env
# Edit .env with your configurations

# Start with Docker Compose
docker-compose up --build

# API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
````

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
# Create PostgreSQL database named 'blog'
createdb blog

# Run migrations
alembic upgrade head

# Start Redis
redis-server

# Run development server
uvicorn app.main:app --reload

# API available at http://localhost:8000
```

---

## 📡 API Endpoints

### Authentication

```http
POST   /api/v1/auth/register      # Register new user
POST   /api/v1/auth/login         # Login (get JWT token)
GET    /api/v1/auth/me            # Get current user
PUT    /api/v1/auth/me            # Update profile
```

### Users

```http
GET    /api/v1/users/{username}           # Get user profile
PUT    /api/v1/users/{username}           # Update user (own)
POST   /api/v1/users/{username}/avatar    # Upload avatar
DELETE /api/v1/users/{username}           # Delete account (own)
```

### Posts

```http
GET    /api/v1/posts                      # List all posts
GET    /api/v1/posts/{id}                 # Get single post
POST   /api/v1/posts                      # Create post
PUT    /api/v1/posts/{id}                 # Update post (own)
DELETE /api/v1/posts/{id}                 # Delete post (own)
GET    /api/v1/posts/feed                 # Personalized feed
GET    /api/v1/posts/user/{username}      # User's posts
GET    /api/v1/posts?search=query         # Search posts
GET    /api/v1/posts?tag=slug             # Filter by tag
```

### Comments

```http
GET    /api/v1/posts/{id}/comments        # Get post comments
POST   /api/v1/posts/{id}/comments        # Create comment
POST   /api/v1/comments/{id}/reply        # Reply to comment
PUT    /api/v1/comments/{id}              # Update comment (own)
DELETE /api/v1/comments/{id}              # Delete comment (own)
```

### Likes & Reactions

```http
POST   /api/v1/posts/{id}/like            # Like/react to post
DELETE /api/v1/posts/{id}/like            # Unlike post
GET    /api/v1/posts/{id}/likes           # Get post likes
```

### Follow System

```http
POST   /api/v1/users/{username}/follow    # Follow user
DELETE /api/v1/users/{username}/follow    # Unfollow user
GET    /api/v1/users/{username}/followers # Get followers
GET    /api/v1/users/{username}/following # Get following
```

### Tags

```http
GET    /api/v1/tags                       # List all tags
GET    /api/v1/tags/trending              # Get trending tags
GET    /api/v1/tags/{slug}                # Get tag details
GET    /api/v1/tags/{slug}/posts          # Posts with tag
```

### Notifications

```http
GET    /api/v1/notifications              # Get notifications
GET    /api/v1/notifications/unread-count # Unread count
PUT    /api/v1/notifications/{id}/read    # Mark as read
PUT    /api/v1/notifications/read-all     # Mark all as read
DELETE /api/v1/notifications/{id}         # Delete notification
```

### Full API documentation available at `/docs` (Swagger UI)

---

## 🔌 WebSocket

### Real-time Notifications

Connect to WebSocket for instant notifications:

```javascript
const token = "your_jwt_token";
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/notifications?token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "notification") {
    console.log("New notification:", data.data);
    // Handle notification (like, comment, follow)
  }
};

// Send ping to keep connection alive
setInterval(() => {
  ws.send(JSON.stringify({ type: "ping" }));
}, 30000);
```

### Notification Types

- `follow` - Someone followed you
- `like` - Someone liked your post
- `comment` - Someone commented on your post
- `mention` - Someone mentioned you (future feature)

---

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_auth.py -v

# Run specific test
pytest app/tests/test_auth.py::TestAuthentication::test_login_success -v
```

### Test Coverage

Current test coverage: **86%**

```
app/api/endpoints/    86%
app/models/           100%
app/services/         65%
app/core/             94%
```

### Test Structure

- **Unit Tests**: Individual function testing
- **Integration Tests**: Complete user flows
- **WebSocket Tests**: Real-time functionality
- **Performance Tests**: Response time benchmarks

---

## 🌍 Deployment

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# Redis
REDIS_URL=redis://host:6379

# Security
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# App
APP_NAME=Blog API
DEBUG=False
```

### Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up

# View logs
railway logs
```

### Deploy to Render

1. Push code to GitHub
2. Connect repository on Render
3. Add PostgreSQL and Redis services
4. Configure environment variables
5. Deploy!

### Health Check

```bash
curl https://your-app.railway.app/health
# Expected: {"status": "healthy"}
```

---

### Example Response

```json
{
  "id": 1,
  "content": "My first post! #introduction",
  "user": {
    "id": 1,
    "username": "johndoe",
    "avatar_url": "https://..."
  },
  "tags": [
    {"name": "introduction", "slug": "introduction"}
  ],
  "likes_count": 42,
  "comments_count": 7,
  "is_liked": true,
  "created_at": "2026-03-15T10:30:00Z"
}
```

---

## 📂 Project Structure

```
blog-api/
├── app/
│   ├── api/
│   │   ├── deps/                 # Dependencies (auth, database)
│   │   │   ├── auth.py
│   │   │   └── database.py
│   │   └── endpoints/            # API routes
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── posts.py
│   │       ├── comments.py
│   │       ├── likes.py
│   │       ├── follows.py
│   │       ├── tags.py
│   │       ├── notifications.py
│   │       └── websocket.py
│   ├── core/                     # Core functionality
│   │   ├── config.py            # Settings
│   │   ├── security.py          # JWT, password hashing
│   │   └── database.py          # Database connection
│   ├── models/                   # SQLAlchemy models
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   ├── like.py
│   │   ├── follow.py
│   │   ├── tag.py
│   │   └── notification.py
│   ├── schemas/                  # Pydantic schemas
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   ├── like.py
│   │   ├── follow.py
│   │   ├── tag.py
│   │   └── notification.py
│   ├── services/                 # Business logic
│   │   ├── cache.py
│   │   ├── upload.py
│   │   ├── notification.py
│   │   └── websocket.py
│   ├── utils/                    # Utilities
│   │   └── slug.py
│   ├── tests/                    # Test suite
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_posts.py
│   │   ├── test_comments.py
│   │   ├── test_follows.py
│   │   ├── test_websocket.py
│   │   └── test_integration.py
│   └── main.py                   # Application entry point
├── alembic/                      # Database migrations
│   └── versions/
├── uploads/                      # Local file storage
├── .env                          # Environment variables
├── .env.example                  # Example environment
├── .gitignore
├── docker-compose.yml            # Docker services
├── Dockerfile                    # Docker image
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
├── alembic.ini                   # Alembic configuration
└── README.md                     # This file
```

---

## 🔧 Configuration

### Application Settings

Edit `app/core/config.py` to customize:

- Database connection
- Redis connection
- JWT configuration
- File upload settings
- CORS origins

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View current version
alembic current
```

---

## 🐛 Troubleshooting

### Common Issues

**Database connection error:**

```bash
# Check PostgreSQL is running
pg_isready

# Check connection string
echo $DATABASE_URL
```

**Redis connection error:**

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

**Import errors:**

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Migration errors:**

```bash
# Drop all tables and re-migrate (DEVELOPMENT ONLY)
alembic downgrade base
alembic upgrade head
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Keep commits atomic and descriptive

---

## 📝 License

This project is licensed under the MIT License 

---

## 👤 Author

**Rokia Alaa**

- GitHub: https://github.com/RokiaAlaa
- LinkedIn: https://www.linkedin.com/in/rokia-alaa-51847632a/
- Email: rokiaalaa666@gmail.com

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Amazing Python framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Powerful ORM
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Railway](https://railway.app/) - Easy deployment
- Inspired by Twitter/X and Medium

---

## 📊 Project Stats

- **Lines of Code**: ~8,000
- **API Endpoints**: 40+
- **Database Tables**: 8
- **Test Cases**: 100+
- **Test Coverage**: 85%+
- **Development Time**: 2 weeks

---

## 🗺️ Roadmap

### Completed ✅

- [x] User authentication
- [x] Posts CRUD
- [x] Comments system
- [x] Likes/reactions
- [x] Follow system
- [x] Real-time notifications
- [x] Tags
- [x] Search
- [x] File uploads


### Planned 🔜

- [ ] Deployment
- [ ] Direct messaging
- [ ] Bookmarks
- [ ] Rich text editor support
- [ ] Mention notifications
- [ ] Email notifications
- [ ] Two-factor authentication
- [ ] Post scheduling
- [ ] Analytics dashboard
- [ ] Rate limiting
- [ ] Admin panel

---
