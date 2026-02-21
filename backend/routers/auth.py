from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import random, string

from database import get_db
from models.models import User
from services.jwt_service import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# O'qituvchi uchun maxsus kirish paroli
TEACHER_SECRET = "fizika1"

def gen_code(): return ''.join(random.choices(string.digits, k=6))

class RegisterIn(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class VerifyIn(BaseModel):
    email: EmailStr
    code: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TeacherLoginIn(BaseModel):
    secret: str        # "fizika1"
    email: EmailStr
    password: str

class ForgotIn(BaseModel):
    email: EmailStr

class ResetIn(BaseModel):
    email: EmailStr
    code: str
    new_password: str

# ===== STUDENT REGISTER =====
@router.post("/register")
async def register(data: RegisterIn, db: AsyncSession = Depends(get_db)):
    ex = await db.execute(select(User).where(User.email == data.email))
    if ex.scalar_one_or_none():
        raise HTTPException(400, "Bu email allaqachon ro'yxatdan o'tgan")
    code = gen_code()
    user = User(
        full_name=data.full_name, email=data.email,
        password_hash=pwd.hash(data.password), role="student",
        verify_code=code, is_verified=False
    )
    db.add(user)
    await db.commit()
    return {"verify_code": code, "email": data.email}

# ===== VERIFY EMAIL =====
@router.post("/verify-email")
async def verify_email(data: VerifyIn, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(User).where(User.email == data.email))
    user = r.scalar_one_or_none()
    if not user: raise HTTPException(404, "Foydalanuvchi topilmadi")
    if user.is_verified: raise HTTPException(400, "Allaqachon tasdiqlangan")
    if user.verify_code != data.code: raise HTTPException(400, "Kod noto'g'ri")
    user.is_verified = True
    user.verify_code = None
    await db.commit()
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "role": user.role, "full_name": user.full_name, "user_id": user.id}

# ===== STUDENT LOGIN =====
@router.post("/login")
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(User).where(User.email == data.email, User.role == "student"))
    user = r.scalar_one_or_none()
    if not user or not pwd.verify(data.password, user.password_hash):
        raise HTTPException(401, "Email yoki parol noto'g'ri")
    if not user.is_verified:
        raise HTTPException(403, "Email tasdiqlanmagan")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "role": user.role, "full_name": user.full_name, "user_id": user.id}

# ===== TEACHER SECRET LOGIN =====
@router.post("/teacher-login")
async def teacher_login(data: TeacherLoginIn, db: AsyncSession = Depends(get_db)):
    # Avval maxsus parolni tekshirish
    if data.secret != TEACHER_SECRET:
        raise HTTPException(403, "Noto'g'ri kalit")

    r = await db.execute(select(User).where(User.email == data.email, User.role == "teacher"))
    user = r.scalar_one_or_none()
    if not user or not pwd.verify(data.password, user.password_hash):
        raise HTTPException(401, "Email yoki parol noto'g'ri")
    if not user.is_verified:
        raise HTTPException(403, "Email tasdiqlanmagan")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "role": user.role, "full_name": user.full_name, "user_id": user.id}

# ===== TEACHER REGISTER (admin tomonidan yoki birinchi setup) =====
@router.post("/teacher-register")
async def teacher_register(data: TeacherLoginIn, db: AsyncSession = Depends(get_db)):
    """O'qituvchi hisobini yaratish — maxsus kalit talab qilinadi"""
    if data.secret != TEACHER_SECRET:
        raise HTTPException(403, "Noto'g'ri kalit")
    ex = await db.execute(select(User).where(User.email == data.email))
    if ex.scalar_one_or_none():
        raise HTTPException(400, "Bu email allaqachon ro'yxatdan o'tgan")
    user = User(
        full_name="O'qituvchi", email=data.email,
        password_hash=pwd.hash(data.password), role="teacher",
        is_verified=True  # O'qituvchi email tasdiqlashsiz
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": "teacher"})
    return {"access_token": token, "role": "teacher", "full_name": user.full_name, "user_id": user.id}

# ===== FORGOT PASSWORD =====
@router.post("/forgot-password")
async def forgot(data: ForgotIn, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(User).where(User.email == data.email))
    user = r.scalar_one_or_none()
    if not user: raise HTTPException(404, "Email topilmadi")
    code = gen_code()
    user.reset_code = code
    await db.commit()
    return {"reset_code": code, "email": data.email}

@router.post("/reset-password")
async def reset(data: ResetIn, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(User).where(User.email == data.email))
    user = r.scalar_one_or_none()
    if not user: raise HTTPException(404, "Topilmadi")
    if user.reset_code != data.code: raise HTTPException(400, "Kod noto'g'ri")
    user.password_hash = pwd.hash(data.new_password)
    user.reset_code = None
    await db.commit()
    return {"message": "Parol o'zgartirildi"}

@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "role": user.role}
