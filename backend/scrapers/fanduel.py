import re
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

FANDUEL_URLS = {
    "nfl": "https://sportsbook.fanduel.com/navigation/nfl",
    "nba": "https://sportsbook.fanduel.com/navigation/nba",
    "mlb": "https://sportsbook.fanduel.com/navigation/mlb",
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

# Matches aria-labels like "Kansas City Chiefs +150 to win"
_ARIA_ODDS_RE = re.compile(
    r"^(?P<team>.+?)\s+(?P<odds>[+\-]\d+)\s+to\s+win", re.IGNORECASE
)


def _parse_aria_events(soup: BeautifulSoup, sport: str) -> list[dict]:
    """
    Parse FanDuel's aria-label attributes on bet buttons — much more stable
    than class-based selectors which change with every React build.
    Groups consecutive home/away button pairs into matchups.
    """
    results = []
    buttons = soup.find_all("button", attrs={"aria-label": True})
    parsed = []
    for btn in buttons:
        m = _ARIA_ODDS_RE.match(btn["aria-label"])
        if m:
            parsed.append({"team": m.group("team").strip(), "odds": m.group("odds")})

    # Pair consecutive entries as home / away
    for i in range(0, len(parsed) - 1, 2):
        home, away = parsed[i], parsed[i + 1]
        results.append({
            "book": "FanDuel",
            "sport": sport,
            "home": home["team"],
            "away": away["team"],
            "home_odds": home["odds"],
            "away_odds": away["odds"],
        })
    return results


def _parse_class_events(soup: BeautifulSoup, sport: str) -> list[dict]:
    """Fallback: broad class-based extraction."""
    results = []
    events = soup.select('[class*="event"], [class*="Event"]')
    for event in events[:20]:
        team_els = event.select(
            '[class*="participant"], [class*="team"], [class*="Team"], [class*="name"]'
        )
        odds_els = event.select(
            '[class*="odds"], [class*="Odds"], [class*="price"], [class*="Price"]'
        )
        teams = [t.get_text(strip=True) for t in team_els if t.get_text(strip=True)]
        odds = [o.get_text(strip=True) for o in odds_els if o.get_text(strip=True)]
        if len(teams) >= 2 and len(odds) >= 2:
            results.append({
                "book": "FanDuel",
                "sport": sport,
                "home": teams[0],
                "away": teams[1],
                "home_odds": odds[0],
                "away_odds": odds[1],
            })
    return results


async def scrape_fanduel(sport: str = "nfl") -> list[dict]:
    results = []
    url = FANDUEL_URLS.get(sport, FANDUEL_URLS["nfl"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await context.new_page()
        try:
            await page.goto(url, timeout=30000, wait_until="networkidle")
            await page.wait_for_timeout(random.randint(3000, 5000))
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            results = _parse_aria_events(soup, sport)
            if not results:
                results = _parse_class_events(soup, sport)

            if results:
                print(f"  [FanDuel] {sport}: {len(results)} events")
        except Exception as e:
            print(f"  [FanDuel] {sport}: scrape error — {e}")
        finally:
            await browser.close()

    return results
