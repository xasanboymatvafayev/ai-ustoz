from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import pytz

from database import get_db
from models.models import Assignment, Group, GroupMember, User, Submission
from services.jwt_service import get_current_user, require_teacher
from services.ai_checker import ai_check

router = APIRouter(tags=["assignments"])
TZ = pytz.timezone("Asia/Tashkent")

class CreateAssignmentIn(BaseModel):
    group_id: int
    title: str
    description: str
    is_timer: bool = False
    timer_minutes: Optional[int] = None

class ScoreIn(BaseModel):
    submission_id: int
    final_score: float

class SubmitIn(BaseModel):
    assignment_id: int
    content: str

# ===== ASSIGNMENTS =====

@router.post("/assignments/create")
async def create_assignment(data: CreateAssignmentIn, db: AsyncSession = Depends(get_db), teacher=Depends(require_teacher)):
    r = await db.execute(select(Group).where(Group.id == data.group_id, Group.teacher_id == teacher.id))
    if not r.scalar_one_or_none():
        raise HTTPException(404, "Guruh topilmadi")

    now = datetime.now(TZ)
    end_time = now + timedelta(minutes=data.timer_minutes) if data.is_timer and data.timer_minutes else None

    a = Assignment(
        group_id=data.group_id, title=data.title, description=data.description,
        is_timer=data.is_timer, timer_minutes=data.timer_minutes,
        start_time=now if data.is_timer else None, end_time=end_time
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return {
        "id": a.id, "title": a.title, "is_timer": a.is_timer,
        "end_time": end_time.isoformat() if end_time else None
    }

@router.get("/assignments/group/{group_id}")
async def group_assignments(group_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    r = await db.execute(select(Assignment).where(Assignment.group_id == group_id).order_by(Assignment.created_at.desc()))
    assignments = r.scalars().all()
    now = datetime.now(TZ)
    return [{
        "id": a.id, "title": a.title, "description": a.description,
        "is_timer": a.is_timer, "timer_minutes": a.timer_minutes,
        "end_time": a.end_time.isoformat() if a.end_time else None,
        "is_active": (a.end_time > now) if a.end_time else True,
        "remaining_seconds": max(0, int((a.end_time - now).total_seconds())) if a.end_time and a.end_time > now else 0,
        "created_at": a.created_at.isoformat()
    } for a in assignments]

@router.get("/assignments/{assignment_id}")
async def get_assignment(assignment_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    r = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    a = r.scalar_one_or_none()
    if not a: raise HTTPException(404, "Topilmadi")
    now = datetime.now(TZ)
    return {
        "id": a.id, "title": a.title, "description": a.description,
        "is_timer": a.is_timer, "timer_minutes": a.timer_minutes,
        "end_time": a.end_time.isoformat() if a.end_time else None,
        "is_active": (a.end_time > now) if a.end_time else True,
        "remaining_seconds": max(0, int((a.end_time - now).total_seconds())) if a.end_time and a.end_time > now else 0
    }

@router.post("/assignments/score")
async def set_score(data: ScoreIn, db: AsyncSession = Depends(get_db), teacher=Depends(require_teacher)):
    r = await db.execute(select(Submission).where(Submission.id == data.submission_id))
    sub = r.scalar_one_or_none()
    if not sub: raise HTTPException(404, "Topshiriq topilmadi")
    if not (1 <= data.final_score <= 5): raise HTTPException(400, "Ball 1-5 oralig'ida bo'lishi kerak")
    sub.final_score = data.final_score
    await db.commit()
    return {"message": "Ball saqlandi", "final_score": data.final_score}

@router.get("/assignments/teacher/table/{group_id}")
async def teacher_table(group_id: int, db: AsyncSession = Depends(get_db), teacher=Depends(require_teacher)):
    grp = await db.execute(select(Group).where(Group.id == group_id, Group.teacher_id == teacher.id))
    group = grp.scalar_one_or_none()
    if not group: raise HTTPException(404, "Guruh topilmadi")

    members_r = await db.execute(
        select(User).join(GroupMember, User.id == GroupMember.student_id)
        .where(GroupMember.group_id == group_id).order_by(User.full_name)
    )
    members = members_r.scalars().all()

    assign_r = await db.execute(
        select(Assignment).where(Assignment.group_id == group_id).order_by(Assignment.created_at)
    )
    assignments = assign_r.scalars().all()

    if not assignments:
        return {"group_name": group.name, "assignments": [], "rows": []}

    subs_r = await db.execute(
        select(Submission).where(Submission.assignment_id.in_([a.id for a in assignments]))
    )
    sub_map = {(s.student_id, s.assignment_id): s for s in subs_r.scalars().all()}

    rows = []
    for m in members:
        row = {"student_id": m.id, "full_name": m.full_name, "assignments": {}, "total_score": 0, "graded_count": 0}
        for a in assignments:
            sub = sub_map.get((m.id, a.id))
            if sub:
                row["assignments"][str(a.id)] = {
                    "status": "submitted",
                    "submission_id": sub.id,
                    "content_preview": sub.content[:150] + "..." if len(sub.content) > 150 else sub.content,
                    "ai_score": sub.ai_score,
                    "ai_comment": sub.ai_comment,
                    "ai_confidence": sub.ai_confidence,
                    "final_score": sub.final_score,
                    "is_late": sub.is_late,
                    "submitted_at": sub.submitted_at.astimezone(TZ).strftime("%H:%M")
                }
                if sub.final_score is not None:
                    row["total_score"] += sub.final_score
                    row["graded_count"] += 1
            else:
                row["assignments"][str(a.id)] = {"status": "missing"}
        rows.append(row)

    return {
        "group_name": group.name,
        "assignments": [{"id": a.id, "title": a.title, "is_timer": a.is_timer,
                         "date": a.created_at.astimezone(TZ).strftime("%d.%m")} for a in assignments],
        "rows": rows
    }

# ===== SUBMISSIONS =====

@router.post("/submissions/submit")
async def submit(data: SubmitIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if user.role != "student":
        raise HTTPException(403, "Faqat o'quvchilar topshiradi")

    r = await db.execute(select(Assignment).where(Assignment.id == data.assignment_id))
    a = r.scalar_one_or_none()
    if not a: raise HTTPException(404, "Vazifa topilmadi")

    # Guruh a'zosimi?
    m = await db.execute(select(GroupMember).where(
        GroupMember.group_id == a.group_id, GroupMember.student_id == user.id
    ))
    if not m.scalar_one_or_none():
        raise HTTPException(403, "Siz bu guruh a'zosi emassiz")

    # Duplicate?
    ex = await db.execute(select(Submission).where(
        Submission.assignment_id == data.assignment_id, Submission.student_id == user.id
    ))
    if ex.scalar_one_or_none():
        raise HTTPException(400, "Siz allaqachon topshirgansiz")

    now = datetime.now(TZ)
    is_late = a.is_timer and a.end_time and now > a.end_time

    ai = ai_check(data.content, a.description)
    sub = Submission(
        assignment_id=data.assignment_id, student_id=user.id, content=data.content,
        ai_score=ai["ai_score"], ai_comment=ai["ai_comment"], ai_confidence=ai["confidence"],
        is_late=bool(is_late)
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return {
        "submission_id": sub.id, "is_late": bool(is_late),
        "ai_score": ai["ai_score"], "ai_comment": ai["ai_comment"], "confidence": ai["confidence"]
    }

@router.get("/submissions/my/{assignment_id}")
async def my_submission(assignment_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    r = await db.execute(select(Submission).where(
        Submission.assignment_id == assignment_id, Submission.student_id == user.id
    ))
    sub = r.scalar_one_or_none()
    if not sub: return {"status": "not_submitted"}
    return {
        "status": "submitted", "ai_score": sub.ai_score, "ai_comment": sub.ai_comment,
        "final_score": sub.final_score, "is_late": sub.is_late,
        "submitted_at": sub.submitted_at.astimezone(TZ).strftime("%H:%M, %d.%m.%Y")
    }
