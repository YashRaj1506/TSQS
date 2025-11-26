from sqlalchemy import Column, String, JSON, Float, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True)
    device_id = Column(String, index=True)
    timeStamp = Column(DateTime, index=True)
    metrics = Column(JSONB)
    tags = Column(JSONB)