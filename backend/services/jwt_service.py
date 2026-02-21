from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from database import AsyncSessionLocal
    from models.models import User
    from sqlalchemy import select

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token noto'g'ri yoki muddati o'tgan")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == int(payload.get("sub"))))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi")
        return user

async def require_teacher(user=Depends(get_current_user)):
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="Faqat o'qituvchilar uchun")
    return user
