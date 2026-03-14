import re
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

BETMGM_URLS = {
    "nfl": "https://sports.betmgm.com/en/sports/football-11/betting/usa-9/nfl-35",
    "nba": "https://sports.betmgm.com/en/sports/basketball-7/betting/usa-9/nba-6004",
    "mlb": "https://sports.betmgm.com/en/sports/baseball-23/betting/usa-9/mlb-75",
}

# BetMGM aria-labels: "Kansas City Chiefs -175" or "New England Patriots +155"
_MGM_ARIA_RE = re.compile(r"^(?P<team>.+?)\s+(?P<odds>[+\-]\d+)$")


def _parse_mgm_aria(soup: BeautifulSoup, sport: str) -> list[dict]:
    results = []
    buttons = soup.find_all("button", attrs={"aria-label": True})
    parsed = []
    for btn in buttons:
        m = _MGM_ARIA_RE.match(btn["aria-label"].strip())
        if m:
            parsed.append({"team": m.group("team").strip(), "odds": m.group("odds")})

    for i in range(0, len(parsed) - 1, 2):
        home, away = parsed[i], parsed[i + 1]
        results.append({
            "book": "BetMGM",
            "sport": sport,
            "home": home["team"],
            "away": away["team"],
            "home_odds": home["odds"],
            "away_odds": away["odds"],
        })
    return results


def _parse_mgm_classes(soup: BeautifulSoup, sport: str) -> list[dict]:
    results = []
    events = soup.select(
        "ms-event, ms-event-pick, .grid-event, .event-grid, [class*='event-pick']"
    )
    for event in events[:20]:
        team_els = event.select(
            ".team-name, .participant-name, .option-name, "
            "[class*='teamName'], [class*='participant']"
        )
        odds_els = event.select(
            ".option-value, .odds-value, [class*='price'], [class*='odds']"
        )
        teams = [t.get_text(strip=True) for t in team_els if t.get_text(strip=True)]
        odds = [o.get_text(strip=True) for o in odds_els if o.get_text(strip=True)]
        if len(teams) >= 2 and len(odds) >= 2:
            results.append({
                "book": "BetMGM",
                "sport": sport,
                "home": teams[0],
                "away": teams[1],
                "home_odds": odds[0],
                "away_odds": odds[1],
            })
    return results


async def scrape_betmgm(sport: str = "nfl") -> list[dict]:
    results = []
    url = BETMGM_URLS.get(sport, BETMGM_URLS["nfl"])

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
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

            results = _parse_mgm_aria(soup, sport)
            if not results:
                results = _parse_mgm_classes(soup, sport)

            if results:
                print(f"  [BetMGM] {sport}: {len(results)} events")
        except Exception as e:
            print(f"  [BetMGM] {sport}: scrape error — {e}")
        finally:
            await browser.close()

    return results
