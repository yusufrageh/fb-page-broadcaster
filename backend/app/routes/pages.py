from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.page import Page
from app.services.facebook import login_to_facebook, fetch_managed_pages, close_page

router = APIRouter(prefix="/api/pages", tags=["pages"])


class PageRead(BaseModel):
    id: int
    fb_page_id: str
    name: str
    url: str
    is_active: bool
    created_at: datetime | None = None


@router.post("/fetch", response_model=list[PageRead])
async def fetch_pages(db: AsyncSession = Depends(get_db)):
    """Login to Facebook and fetch managed pages."""
    try:
        page = await login_to_facebook()
        raw_pages = await fetch_managed_pages(page)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await close_page()

    results = []
    for rp in raw_pages:
        existing = await db.execute(
            select(Page).where(Page.fb_page_id == rp["fb_page_id"])
        )
        existing_page = existing.scalar_one_or_none()
        if existing_page:
            existing_page.name = rp["name"]
            existing_page.url = rp["url"]
            results.append(existing_page)
        else:
            new_page = Page(
                fb_page_id=rp["fb_page_id"],
                name=rp["name"],
                url=rp["url"],
            )
            db.add(new_page)
            results.append(new_page)

    await db.commit()
    for r in results:
        await db.refresh(r)

    return [
        PageRead(
            id=p.id,
            fb_page_id=p.fb_page_id,
            name=p.name,
            url=p.url,
            is_active=p.is_active,
            created_at=p.created_at,
        )
        for p in results
    ]


@router.get("", response_model=list[PageRead])
async def get_pages(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Page).order_by(Page.created_at.desc()))
    pages = result.scalars().all()
    return [
        PageRead(
            id=p.id,
            fb_page_id=p.fb_page_id,
            name=p.name,
            url=p.url,
            is_active=p.is_active,
            created_at=p.created_at,
        )
        for p in pages
    ]


@router.put("/{page_id}/activate", response_model=PageRead)
async def activate_page(page_id: int, db: AsyncSession = Depends(get_db)):
    # Deactivate all
    result = await db.execute(select(Page))
    all_pages = result.scalars().all()
    for p in all_pages:
        p.is_active = False

    # Activate selected
    page = await db.get(Page, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    page.is_active = True
    await db.commit()
    await db.refresh(page)

    return PageRead(
        id=page.id,
        fb_page_id=page.fb_page_id,
        name=page.name,
        url=page.url,
        is_active=page.is_active,
        created_at=page.created_at,
    )
