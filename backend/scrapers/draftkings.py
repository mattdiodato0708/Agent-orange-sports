import re
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

DK_URLS = {
    "nfl": "https://sportsbook.draftkings.com/leagues/football/nfl",
    "nba": "https://sportsbook.draftkings.com/leagues/basketball/nba",
    "mlb": "https://sportsbook.draftkings.com/leagues/baseball/mlb",
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
]

# DraftKings aria-labels look like: "Kansas City Chiefs, Moneyline, -175"
_DK_ARIA_RE = re.compile(r"^(?P<team>.+?),\s*Moneyline,\s*(?P<odds>[+\-]\d+)", re.IGNORECASE)


def _parse_dk_aria(soup: BeautifulSoup, sport: str) -> list[dict]:
    results = []
    buttons = soup.find_all("button", attrs={"aria-label": True})
    parsed = []
    for btn in buttons:
        m = _DK_ARIA_RE.match(btn["aria-label"])
        if m:
            parsed.append({"team": m.group("team").strip(), "odds": m.group("odds")})

    for i in range(0, len(parsed) - 1, 2):
        home, away = parsed[i], parsed[i + 1]
        results.append({
            "book": "DraftKings",
            "sport": sport,
            "home": home["team"],
            "away": away["team"],
            "home_odds": home["odds"],
            "away_odds": away["odds"],
        })
    return results


def _parse_dk_classes(soup: BeautifulSoup, sport: str) -> list[dict]:
    results = []
    rows = soup.select(
        ".sportsbook-event-accordion__wrapper, "
        ".parlay-card-06__column, "
        "[class*='event-cell'], "
        "[class*='EventCell']"
    )
    for row in rows[:20]:
        team_els = row.select(
            ".event-cell__name-text, .team-name, [class*='name-text'], [class*='teamName']"
        )
        odds_els = row.select(
            ".sportsbook-odds, .sportsbook-price--american, "
            "[class*='odds'], [class*='Odds'], [class*='price']"
        )
        teams = [t.get_text(strip=True) for t in team_els if t.get_text(strip=True)]
        odds = [o.get_text(strip=True) for o in odds_els if o.get_text(strip=True)]
        if len(teams) >= 2 and len(odds) >= 2:
            results.append({
                "book": "DraftKings",
                "sport": sport,
                "home": teams[0],
                "away": teams[1],
                "home_odds": odds[0],
                "away_odds": odds[1],
            })
    return results


async def scrape_draftkings(sport: str = "nfl") -> list[dict]:
    results = []
    url = DK_URLS.get(sport, DK_URLS["nfl"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 768},
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

            results = _parse_dk_aria(soup, sport)
            if not results:
                results = _parse_dk_classes(soup, sport)

            if results:
                print(f"  [DraftKings] {sport}: {len(results)} events")
        except Exception as e:
            print(f"  [DraftKings] {sport}: scrape error — {e}")
        finally:
            await browser.close()

    return results
