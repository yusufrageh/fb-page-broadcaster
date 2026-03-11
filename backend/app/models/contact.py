from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fb_user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    profile_url = Column(String, default="")
    last_interaction = Column(DateTime, nullable=True)
    last_broadcast_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    page = relationship("Page", back_populates="contacts")
    message_logs = relationship("MessageLog", back_populates="contact", cascade="all, delete-orphan")
