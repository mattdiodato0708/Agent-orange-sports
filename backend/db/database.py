import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "arbs.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS arb_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport TEXT,
                home_team TEXT,
                away_team TEXT,
                book_home TEXT,
                book_away TEXT,
                home_odds TEXT,
                away_odds TEXT,
                profit_pct REAL,
                stake_home REAL,
                stake_away REAL,
                guaranteed_profit REAL,
                found_at TEXT
            )
        """)
        await db.commit()

async def save_arbs(arbs: list[dict]):
    async with aiosqlite.connect(DB_PATH) as db:
        for arb in arbs:
            await db.execute("""
                INSERT INTO arb_opportunities
                (sport, home_team, away_team, book_home, book_away,
                 home_odds, away_odds, profit_pct, stake_home, stake_away,
                 guaranteed_profit, found_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                arb["sport"], arb["home_team"], arb["away_team"],
                arb["book_home"], arb["book_away"],
                arb["home_odds"], arb["away_odds"],
                arb["profit_pct"], arb["stake_home"], arb["stake_away"],
                arb["guaranteed_profit_per_100"], arb["found_at"]
            ))
        await db.commit()

async def get_recent_arbs(min_profit: float = 0.0) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM arb_opportunities
            WHERE profit_pct >= ?
            ORDER BY found_at DESC
            LIMIT 100
        """, (min_profit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
