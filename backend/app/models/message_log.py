from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    broadcast_id = Column(Integer, ForeignKey("broadcasts.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    message_text = Column(String, nullable=False)
    status = Column(String, default="pending")  # sent/failed
    error_message = Column(String, nullable=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    broadcast = relationship("Broadcast", back_populates="message_logs")
    contact = relationship("Contact", back_populates="message_logs")
