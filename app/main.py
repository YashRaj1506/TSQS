from fastapi import FastAPI
from app.routers import events
from app.database import engine
from app.models import Base

app = FastAPI()

app.include_router(events.router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)