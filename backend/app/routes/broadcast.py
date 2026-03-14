from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.page import Page
from app.models.contact import Contact
from app.models.broadcast import Broadcast
from app.services.broadcast import start_broadcast, stop_broadcast, is_running

router = APIRouter(prefix="/api", tags=["broadcast"])


class BroadcastStart(BaseModel):
    base_message: str
    batch_size: int = 50


class BroadcastRead(BaseModel):
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


class ContactRead(BaseModel):
    id: int
    fb_user_id: str
    name: str
    profile_url: str
    last_interaction: datetime | None = None
    last_broadcast_at: datetime | None = None


@router.get("/contacts", response_model=list[ContactRead])
async def get_contacts(db: AsyncSession = Depends(get_db)):
    # Get active page
    result = await db.execute(select(Page).where(Page.is_active == True))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=400, detail="No active page selected")

    result = await db.execute(
        select(Contact).where(Contact.page_id == page.id).order_by(Contact.name)
    )
    contacts = result.scalars().all()
    return [
        ContactRead(
            id=c.id,
            fb_user_id=c.fb_user_id,
            name=c.name,
            profile_url=c.profile_url or "",
            last_interaction=c.last_interaction,
            last_broadcast_at=c.last_broadcast_at,
        )
        for c in contacts
    ]


@router.post("/contacts/fetch", response_model=list[ContactRead])
async def fetch_contacts(db: AsyncSession = Depends(get_db)):
    from app.services.facebook import login_to_facebook, fetch_page_conversations
    from app.models.settings import Settings as SettingsModel

    result = await db.execute(select(Page).where(Page.is_active == True))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=400, detail="No active page selected")

    # Read max_contacts from settings
    settings_result = await db.execute(select(SettingsModel).where(SettingsModel.id == 1))
    settings = settings_result.scalar_one_or_none()
    max_contacts = settings.max_contacts if settings and settings.max_contacts else 100

    try:
        browser_page = await login_to_facebook()
        raw_contacts = await fetch_page_conversations(browser_page, page.fb_page_id, max_contacts=max_contacts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        from app.services.facebook import close_page
        await close_page()

    results = []
    for rc in raw_contacts:
        existing = await db.execute(
            select(Contact).where(
                Contact.fb_user_id == rc["fb_user_id"],
                Contact.page_id == page.id,
            )
        )
        existing_contact = existing.scalar_one_or_none()
        if existing_contact:
            existing_contact.name = rc["name"]
            existing_contact.profile_url = rc.get("profile_url", "")
            results.append(existing_contact)
        else:
            new_contact = Contact(
                fb_user_id=rc["fb_user_id"],
                name=rc["name"],
                page_id=page.id,
                profile_url=rc.get("profile_url", ""),
            )
            db.add(new_contact)
            results.append(new_contact)

    await db.commit()
    for r in results:
        await db.refresh(r)

    return [
        ContactRead(
            id=c.id,
            fb_user_id=c.fb_user_id,
            name=c.name,
            profile_url=c.profile_url or "",
            last_interaction=c.last_interaction,
            last_broadcast_at=c.last_broadcast_at,
        )
        for c in results
    ]


@router.post("/broadcast/start", response_model=BroadcastRead)
async def start_broadcast_endpoint(data: BroadcastStart, db: AsyncSession = Depends(get_db)):
    if is_running():
        raise HTTPException(status_code=400, detail="A broadcast is already running")

    result = await db.execute(select(Page).where(Page.is_active == True))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=400, detail="No active page selected")

    broadcast = Broadcast(
        page_id=page.id,
        base_message=data.base_message,
        batch_size=data.batch_size,
        status="pending",
    )
    db.add(broadcast)
    await db.commit()
    await db.refresh(broadcast)

    await start_broadcast(broadcast.id)

    return BroadcastRead(
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
    )


@router.post("/broadcast/stop")
async def stop_broadcast_endpoint():
    if not is_running():
        raise HTTPException(status_code=400, detail="No broadcast is running")
    await stop_broadcast()
    return {"status": "stopping"}


@router.post("/broadcast/reset-campaign")
async def reset_campaign(db: AsyncSession = Depends(get_db)):
    """Clear sent-to tracking for the active page so all contacts can be messaged again."""
    result = await db.execute(select(Page).where(Page.is_active == True))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=400, detail="No active page selected")

    res = await db.execute(
        update(Contact)
        .where(Contact.page_id == page.id)
        .where(Contact.last_broadcast_at.isnot(None))
        .values(last_broadcast_at=None)
    )
    await db.commit()

    return {"reset_count": res.rowcount, "page_name": page.name}


@router.get("/broadcast/stats")
async def broadcast_stats(db: AsyncSession = Depends(get_db)):
    """Return total contacts sent to for the active page."""
    result = await db.execute(select(Page).where(Page.is_active == True))
    page = result.scalar_one_or_none()
    if not page:
        return {"total_sent_to": 0, "total_contacts": 0}

    sent_to = await db.execute(
        select(func.count()).select_from(Contact).where(
            Contact.page_id == page.id,
            Contact.last_broadcast_at.isnot(None),
        )
    )
    total = await db.execute(
        select(func.count()).select_from(Contact).where(Contact.page_id == page.id)
    )
    return {
        "total_sent_to": sent_to.scalar(),
        "total_contacts": total.scalar(),
    }


@router.get("/broadcast/status")
async def broadcast_status(db: AsyncSession = Depends(get_db)):
    running = is_running()
    result = await db.execute(
        select(Broadcast).order_by(Broadcast.created_at.desc()).limit(1)
    )
    latest = result.scalar_one_or_none()
    if not latest:
        return {"running": False, "broadcast": None}

    return {
        "running": running,
        "broadcast": BroadcastRead(
            id=latest.id,
            page_id=latest.page_id,
            base_message=latest.base_message,
            batch_size=latest.batch_size,
            status=latest.status,
            total_contacts=latest.total_contacts,
            sent_count=latest.sent_count,
            failed_count=latest.failed_count,
            created_at=latest.created_at,
            completed_at=latest.completed_at,
        ),
    }
