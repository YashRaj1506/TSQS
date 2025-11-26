from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Event
from app.schemas import EventCreate, AlertCreate
from typing import List
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy import select, func, text
from fastapi.responses import StreamingResponse
import asyncio
import json

subscribers = []
alerts = []


"""
Below are the helper functions for the alert system [SSE].
"""


def evaluate(value, op, threshold):
    if op == ">":
        return value > threshold
    if op == "<":
        return value < threshold
    if op == ">=":
        return value >= threshold
    if op == "<=":
        return value <= threshold
    if op == "==":
        return value == threshold
    return False


async def trigger_sse(event):
    data = {
        "device_id": event.device_id,
        "metrics": event.metrics,
        "time": str(event.timeStamp),
    }

    for queue, sub_device in subscribers:
        if sub_device == event.device_id:
            await queue.put(data)


async def check_alerts(event):
    for alert in alerts:
        if alert.device_id == event.device_id:
            value = event.metrics.get(alert.metric)
            if value is None:
                continue

            if evaluate(value, alert.op, alert.threshold):
                await trigger_sse(event)


"""
Below is our url routing.
"""

router = APIRouter(prefix="/v1")


@router.post("/alerts")
async def set_alert(alert: AlertCreate):
    alerts.append(alert)
    return {"status": "alert registered"}


@router.get("/alerts/stream")
async def alerts_stream(device_id: str):
    queue = asyncio.Queue()
    subscribers.append((queue, device_id))

    async def event_stream():
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            subscribers.remove((queue, device_id))
            raise

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/events")
async def ingest_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    new_event = Event(
        event_id=event.event_id,
        device_id=event.device_id,
        timeStamp=event.timeStamp,
        metrics=event.metrics,
        tags=event.tags,
    )

    db.add(new_event)
    await db.commit()

    await check_alerts(event)
    return {"status": "ok"}


@router.post("/events/batch")
async def ingest_batch(events: List[EventCreate], db: AsyncSession = Depends(get_db)):

    results = []

    for event in events:
        new_event = Event(
            event_id=event.event_id,
            device_id=event.device_id,
            timeStamp=event.timeStamp,
            metrics=event.metrics,
            tags=event.tags,
        )

        db.add(new_event)

        try:
            await db.commit()
            results.append({"event_id": event.event_id, "status": "stored"})
        except IntegrityError:
            await db.rollback()
            results.append({"event_id": event.event_id, "status": "duplicate"})

    return results


@router.get("/devices/{device_id}/events")
async def get_events(
    device_id: str,
    from_time: datetime = Query(...),
    to_time: datetime = Query(...),
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    results = await db.execute(
        select(Event)
        .where(Event.device_id == device_id)
        .where(Event.timeStamp >= from_time)
        .where(Event.timeStamp <= to_time)
        .order_by(Event.timeStamp.desc())
        .limit(limit)
    )

    return results.scalars().all()


@router.get("/metrics/aggregate")
async def aggregate(
    device_id: str,
    metric: str,
    from_time: datetime,
    to_time: datetime,
    interval: str = "1m",
    db: AsyncSession = Depends(get_db),
):

    INTERVAL_MAP = {
        "1m": "minute",
        "1h": "hour",
        "1d": "day",
    }

    unit = INTERVAL_MAP.get(interval, "minute")

    query = f"""
    SELECT
        date_trunc('{unit}', "timeStamp") AS bucket,
        COUNT(*) AS count,
        SUM((metrics->>'{metric}')::float) AS sum,
        AVG((metrics->>'{metric}')::float) AS avg,
        MIN((metrics->>'{metric}')::float) AS min,
        MAX((metrics->>'{metric}')::float) AS max
    FROM events
    WHERE device_id = :device_id
    AND "timeStamp" BETWEEN :from_time AND :to_time
    GROUP BY bucket
    ORDER BY bucket;
    """

    result = await db.execute(
        text(query),
        {"device_id": device_id, "from_time": from_time, "to_time": to_time},
    )

    return result.mappings().all()


@router.get("/search")
async def search_by_tag(
    tag: str,
    from_time: datetime,
    to_time: datetime,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Event)
        .where(
            Event.tags.contains([tag]),
            Event.timeStamp >= from_time,
            Event.timeStamp <= to_time,
        )
        .limit(limit)
    )

    results = await db.execute(query)

    return results.scalars().all()
