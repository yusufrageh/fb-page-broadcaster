from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fb_page_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, default="")
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    contacts = relationship("Contact", back_populates="page", cascade="all, delete-orphan")
    broadcasts = relationship("Broadcast", back_populates="page", cascade="all, delete-orphan")
