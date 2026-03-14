import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.scheduler import start_scheduler
from backend.db.database import init_db, get_recent_arbs

# Comma-separated list of allowed origins; defaults to same-origin only
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",") if os.environ.get("ALLOWED_ORIGINS") else []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the FastAPI app."""
    await init_db()
    task = asyncio.create_task(start_scheduler())
    yield
    task.cancel()


app = FastAPI(title="Agent Orange Sports Arb Finder", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/arbs")
async def get_arbs(min_profit: float = 0.5):
    """Return recent arbitrage opportunities above *min_profit* %."""
    return await get_recent_arbs(min_profit)


@app.get("/api/status")
async def status():
    """Health-check endpoint."""
    return {"status": "running", "version": "1.0"}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
