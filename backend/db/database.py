import os
import aiosqlite
import json
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "arb_data.db")


async def init_db():
    """Initialize the SQLite database and create tables if needed."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS arbs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT NOT NULL,
                event TEXT NOT NULL,
                market TEXT NOT NULL,
                book1 TEXT NOT NULL,
                outcome1 TEXT NOT NULL,
                odds1 REAL NOT NULL,
                book2 TEXT NOT NULL,
                outcome2 TEXT NOT NULL,
                odds2 REAL NOT NULL,
                profit_pct REAL NOT NULL,
                stake1 REAL,
                stake2 REAL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def save_arbs(arbs: list):
    """Save a list of arbitrage opportunities to the database."""
    async with aiosqlite.connect(DB_PATH) as db:
        for arb in arbs:
            await db.execute(
                """INSERT INTO arbs
                   (sport, event, market, book1, outcome1, odds1,
                    book2, outcome2, odds2, profit_pct, stake1, stake2, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    arb.get("sport", ""),
                    arb.get("event", ""),
                    arb.get("market", "moneyline"),
                    arb.get("book1", ""),
                    arb.get("outcome1", ""),
                    arb.get("odds1", 0),
                    arb.get("book2", ""),
                    arb.get("outcome2", ""),
                    arb.get("odds2", 0),
                    arb.get("profit_pct", 0),
                    arb.get("stake1", 0),
                    arb.get("stake2", 0),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        await db.commit()


async def get_recent_arbs(min_profit: float = 0.5, limit: int = 100):
    """Retrieve recent arbitrage opportunities above a minimum profit threshold."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM arbs
               WHERE profit_pct >= ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (min_profit, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
