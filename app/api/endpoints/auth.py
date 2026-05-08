from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm 
from app.api.deps.database import get_db
from app.api.deps.auth import oauth2_scheme
from app.api.deps.auth import get_current_active_user
from app.models.user import User
from sqlalchemy import or_
from app.schemas.user import User as UserSchema, UserCreate
from app.schemas.token import Token
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.services.cache import redis_client
from app.core.limiter import limiter

router = APIRouter()

@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
@limiter.limit('5/minute')
async def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""

    existing_email = db.query(User).filter(user_in.email == User.email).first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    
    existing_username = db.query(User).filter(user_in.username == User.username).first()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )
    
    new_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password= hash_password(user_in.password),
            fullname=user_in.fullname
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
@limiter.limit('5/minute')
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    """Login with email/username and password"""
    
    user = db.query(User).filter(or_(form_data.username == User.username, form_data.username == User.email)).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email/username or password",
            headers={'WWW-Authenticate': "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Inactive user'
        )
    
    access_token = create_access_token(data={'user_id': user.id})

    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get("/me", response_model=UserSchema)
@limiter.limit('60/minute')
async def read_current_user(request: Request, current_user: User = Depends(get_current_active_user)):

    """Get current user profile"""
    return current_user

@router.post("/logout")
@limiter.limit('60/minute')
async def logout(request: Request, token: str =  Depends(oauth2_scheme), current_user: User = Depends(get_current_active_user)):

    """Logout (client should delete token)"""
    
    await redis_client.setex(
        f'blacklist:{token}', settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, 'blacklisted'
    )

    return {"message": "Successfully logged out"}