from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from app.models.user import User
from .database import get_db
from app.core.security import verify_access_token
from sqlalchemy.orm import Session
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='api/v1/auth/login')
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl='api/v1/auth/login', auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:

    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                          detail= "Could not Validate credentials",
                                          headers={'WWW-Authenticate': "Bearer"})
    
    token_data = await verify_access_token(token, credentials_exception)

    user = db.query(User).filter(User.id == token_data.user_id).first()

    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:

    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Inactive user')
    
    return current_user

async def get_optional_current_user(token: str = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> Optional[User]:
 
    """Get current user if token provided, else None"""
    
    if not token:
        return None
    
    try:
        credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        token_data = await verify_access_token(token, credentials_exception)
    except HTTPException:
        return None

    if token_data is None or token_data.user_id is None:
        return None

    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    return user