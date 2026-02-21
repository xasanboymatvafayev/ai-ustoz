from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from database import get_db
from models.models import Group, GroupMember, User
from services.jwt_service import get_current_user, require_teacher

router = APIRouter(prefix="/groups", tags=["groups"])

def new_key():
    return str(uuid.uuid4())[:8].upper()

async def unique_key(db):
    while True:
        key = new_key()
        ex = await db.execute(select(Group).where(Group.invite_key == key))
        if not ex.scalar_one_or_none():
            return key

class CreateGroupIn(BaseModel):
    name: str

class JoinGroupIn(BaseModel):
    invite_key: str

@router.post("/create")
async def create_group(data: CreateGroupIn, db: AsyncSession = Depends(get_db), teacher=Depends(require_teacher)):
    key = await unique_key(db)
    group = Group(name=data.name, teacher_id=teacher.id, invite_key=key)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return {"id": group.id, "name": group.name, "invite_key": group.invite_key}

@router.get("/my")
async def my_groups(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if user.role == "teacher":
        r = await db.execute(select(Group).where(Group.teacher_id == user.id).order_by(Group.created_at.desc()))
        groups = r.scalars().all()
        return [{"id": g.id, "name": g.name, "invite_key": g.invite_key, "created_at": g.created_at.isoformat()} for g in groups]
    else:
        r = await db.execute(
            select(Group).join(GroupMember, Group.id == GroupMember.group_id)
            .where(GroupMember.student_id == user.id)
        )
        groups = r.scalars().all()
        return [{"id": g.id, "name": g.name} for g in groups]

@router.post("/join")
async def join_group(data: JoinGroupIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if user.role != "student":
        raise HTTPException(403, "Faqat o'quvchilar guruhga qo'shila oladi")
    r = await db.execute(select(Group).where(Group.invite_key == data.invite_key.upper().strip()))
    group = r.scalar_one_or_none()
    if not group:
        raise HTTPException(404, "Invite key noto'g'ri. O'qituvchingizdan so'rang.")
    ex = await db.execute(select(GroupMember).where(
        GroupMember.group_id == group.id, GroupMember.student_id == user.id
    ))
    if ex.scalar_one_or_none():
        raise HTTPException(400, "Siz allaqachon bu guruh a'zosisiz")
    db.add(GroupMember(group_id=group.id, student_id=user.id))
    await db.commit()
    return {"message": f"'{group.name}' guruhiga qo'shildingiz!", "group_id": group.id, "group_name": group.name}

@router.post("/{group_id}/regenerate-key")
async def regen_key(group_id: int, db: AsyncSession = Depends(get_db), teacher=Depends(require_teacher)):
    r = await db.execute(select(Group).where(Group.id == group_id, Group.teacher_id == teacher.id))
    group = r.scalar_one_or_none()
    if not group: raise HTTPException(404, "Guruh topilmadi")
    group.invite_key = await unique_key(db)
    await db.commit()
    return {"new_invite_key": group.invite_key, "message": "Key yangilandi"}

@router.get("/{group_id}/members")
async def get_members(group_id: int, db: AsyncSession = Depends(get_db), teacher=Depends(require_teacher)):
    r = await db.execute(
        select(User).join(GroupMember, User.id == GroupMember.student_id)
        .where(GroupMember.group_id == group_id)
    )
    members = r.scalars().all()
    return [{"id": m.id, "full_name": m.full_name, "email": m.email} for m in members]
