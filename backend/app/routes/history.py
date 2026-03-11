from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.broadcast import Broadcast
from app.models.message_log import MessageLog

router = APIRouter(prefix="/api/history", tags=["history"])


class MessageLogRead(BaseModel):
    id: int
    contact_name: str
    message_text: str
    status: str
    error_message: str | None = None
    sent_at: datetime | None = None


class BroadcastSummary(BaseModel):
    id: int
    page_id: int
    base_message: str
    batch_size: int
    status: str
    total_contacts: int
    sent_count: int
    failed_count: int
    created_at: datetime | None = None
    completed_at: datetime | None = None


class BroadcastDetail(BroadcastSummary):
    message_logs: list[MessageLogRead] = []


@router.get("", response_model=list[BroadcastSummary])
async def get_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Broadcast).order_by(Broadcast.created_at.desc())
    )
    broadcasts = result.scalars().all()
    return [
        BroadcastSummary(
            id=b.id,
            page_id=b.page_id,
            base_message=b.base_message,
            batch_size=b.batch_size,
            status=b.status,
            total_contacts=b.total_contacts,
            sent_count=b.sent_count,
            failed_count=b.failed_count,
            created_at=b.created_at,
            completed_at=b.completed_at,
        )
        for b in broadcasts
    ]


@router.get("/{broadcast_id}", response_model=BroadcastDetail)
async def get_broadcast_detail(broadcast_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Broadcast)
        .options(selectinload(Broadcast.message_logs).selectinload(MessageLog.contact))
        .where(Broadcast.id == broadcast_id)
    )
    broadcast = result.scalar_one_or_none()
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")

    logs = [
        MessageLogRead(
            id=log.id,
            contact_name=log.contact.name if log.contact else "Unknown",
            message_text=log.message_text,
            status=log.status,
            error_message=log.error_message,
            sent_at=log.sent_at,
        )
        for log in broadcast.message_logs
    ]

    return BroadcastDetail(
        id=broadcast.id,
        page_id=broadcast.page_id,
        base_message=broadcast.base_message,
        batch_size=broadcast.batch_size,
        status=broadcast.status,
        total_contacts=broadcast.total_contacts,
        sent_count=broadcast.sent_count,
        failed_count=broadcast.failed_count,
        created_at=broadcast.created_at,
        completed_at=broadcast.completed_at,
        message_logs=logs,
    )
