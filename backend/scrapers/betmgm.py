import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

BETMGM_URLS = {
    "nfl": "https://sports.betmgm.com/en/sports/football-11/betting/usa-9/nfl-35",
    "nba": "https://sports.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004",
    "mlb": "https://sports.betmgm.com/en/sports/baseball-23/betting/usa-9/mlb-75",
}

async def scrape_betmgm(sport: str = "nfl") -> list[dict]:
    results = []
    url = BETMGM_URLS.get(sport, BETMGM_URLS["nfl"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        page = await context.new_page()
        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(random.randint(4000, 6000))
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            events = soup.select("ms-event, .grid-event, .event-grid")
            for event in events[:20]:
                team_els = event.select(".team-name, .participant-name, .option-name")
                odds_els = event.select(".option-value, .odds-value, [class*='price']")
                teams = [t.get_text(strip=True) for t in team_els if t.get_text(strip=True)]
                odds  = [o.get_text(strip=True) for o in odds_els if o.get_text(strip=True)]
                if len(teams) >= 2 and len(odds) >= 2:
                    results.append({
                        "book": "BetMGM",
                        "sport": sport,
                        "home": teams[0],
                        "away": teams[1],
                        "home_odds": odds[0],
                        "away_odds": odds[1],
                    })
        except Exception as e:
            print(f"[BetMGM] Scrape error: {e}")
        finally:
            await browser.close()

    return results
