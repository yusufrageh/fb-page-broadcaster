from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    fb_email = Column(String, default="")
    fb_password = Column(String, default="")  # encrypted
    min_delay = Column(Float, default=5.0)
    max_delay = Column(Float, default=15.0)
    default_batch_size = Column(Integer, default=50)
    max_contacts = Column(Integer, default=100)
