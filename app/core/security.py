from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings
from app.schemas.token import TokenData
from app.services.cache import redis_client

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

async def verify_access_token(token: str, credentials_exception):

    if await redis_client.get(f'blacklist:{token}'):
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithm=ALGORITHM)

        id: int = payload.get('user_id')

        if id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=id)

    except JWTError:
        raise credentials_exception
    
    return token_data