from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import encrypt, decrypt
from app.models.settings import Settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsRead(BaseModel):
    fb_email: str = ""
    fb_password_set: bool = False
    gemini_api_key_set: bool = False
    min_delay: float = 5.0
    max_delay: float = 15.0
    default_batch_size: int = 50
    max_contacts: int = 100


class SettingsUpdate(BaseModel):
    fb_email: str | None = None
    fb_password: str | None = None
    gemini_api_key: str | None = None
    min_delay: float | None = None
    max_delay: float | None = None
    default_batch_size: int | None = None
    max_contacts: int | None = None


@router.get("", response_model=SettingsRead)
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = Settings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return SettingsRead(
        fb_email=settings.fb_email or "",
        fb_password_set=bool(settings.fb_password),
        gemini_api_key_set=bool(settings.gemini_api_key),
        min_delay=settings.min_delay,
        max_delay=settings.max_delay,
        default_batch_size=settings.default_batch_size,
        max_contacts=settings.max_contacts,
    )


@router.put("", response_model=SettingsRead)
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = Settings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    if data.fb_email is not None:
        settings.fb_email = data.fb_email
    if data.fb_password is not None:
        settings.fb_password = encrypt(data.fb_password)
    if data.gemini_api_key is not None:
        settings.gemini_api_key = encrypt(data.gemini_api_key)
    if data.min_delay is not None:
        settings.min_delay = data.min_delay
    if data.max_delay is not None:
        settings.max_delay = data.max_delay
    if data.default_batch_size is not None:
        settings.default_batch_size = data.default_batch_size
    if data.max_contacts is not None:
        settings.max_contacts = data.max_contacts

    await db.commit()
    await db.refresh(settings)

    return SettingsRead(
        fb_email=settings.fb_email or "",
        fb_password_set=bool(settings.fb_password),
        gemini_api_key_set=bool(settings.gemini_api_key),
        min_delay=settings.min_delay,
        max_delay=settings.max_delay,
        default_batch_size=settings.default_batch_size,
        max_contacts=settings.max_contacts,
    )
