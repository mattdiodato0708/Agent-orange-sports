import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

FANDUEL_URLS = {
    "nfl": "https://sportsbook.fanduel.com/navigation/nfl",
    "nba": "https://sportsbook.fanduel.com/navigation/nba",
    "mlb": "https://sportsbook.fanduel.com/navigation/mlb",
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/118.0.0.0 Safari/537.36",
]

async def scrape_fanduel(sport: str = "nfl") -> list[dict]:
    results = []
    url = FANDUEL_URLS.get(sport, FANDUEL_URLS["nfl"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        page = await context.new_page()
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(random.randint(4000, 7000))
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            events = soup.select('[class*="event"]')
            for event in events[:20]:
                team_els = event.select('[class*="participant"], [class*="team"]')
                odds_els = event.select('[class*="odds"], [class*="price"]')
                teams = [t.get_text(strip=True) for t in team_els if t.get_text(strip=True)]
                odds  = [o.get_text(strip=True) for o in odds_els if o.get_text(strip=True)]
                if len(teams) >= 2 and len(odds) >= 2:
                    results.append({
                        "book": "FanDuel",
                        "sport": sport,
                        "home": teams[0],
                        "away": teams[1],
                        "home_odds": odds[0],
                        "away_odds": odds[1],
                    })
        except Exception as e:
            print(f"[FanDuel] Scrape error: {e}")
        finally:
            await browser.close()

    return results
