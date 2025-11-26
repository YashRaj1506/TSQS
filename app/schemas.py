from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime
from pydantic import RootModel

class EventCreate(BaseModel):
    event_id: str
    device_id: str
    timeStamp: datetime
    metrics: Dict[str, float]
    tags: List[str]

class EventBatch(RootModel[list[EventCreate]]):
    pass

class AlertCreate(BaseModel):
    device_id: str
    metric: str
    op: str
    threshold: float
    callback_url: str | None = None
