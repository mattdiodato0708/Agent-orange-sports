from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend.scheduler import start_scheduler
from backend.db.database import init_db, get_recent_arbs
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(start_scheduler())
    yield


app = FastAPI(title="Agent Orange Sports Arb Finder", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/arbs")
async def get_arbs(min_profit: float = 0.5):
    return await get_recent_arbs(min_profit)

@app.get("/api/status")
async def status():
    return {"status": "running", "version": "1.0"}

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
