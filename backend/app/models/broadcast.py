from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    base_message = Column(String, nullable=False)
    batch_size = Column(Integer, default=50)
    status = Column(String, default="pending")  # pending/running/completed/stopped/failed
    total_contacts = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    page = relationship("Page", back_populates="broadcasts")
    message_logs = relationship("MessageLog", back_populates="broadcast", cascade="all, delete-orphan")
