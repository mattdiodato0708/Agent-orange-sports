from fuzzywuzzy import fuzz

# Minimum fuzzy-match score (0–100) to consider two event names the same game
MATCH_THRESHOLD = 80

def american_to_decimal(american: str) -> float | None:
    try:
        val = int(str(american).replace("+", "").replace("\u2212", "-").replace("\u2013", "-").strip())
        if val > 0:
            return round((val / 100) + 1, 4)
        else:
            return round((100 / abs(val)) + 1, 4)
    except (ValueError, TypeError):
        return None

def normalize_team_name(name: str) -> str:
    name = name.lower().strip()
    replacements = {
        "new england": "patriots", "kansas city": "chiefs",
        "green bay": "packers", "san francisco": "49ers",
        "los angeles": "la", "new york": "ny",
        "golden state": "warriors", "oklahoma city": "thunder",
    }
    for k, v in replacements.items():
        name = name.replace(k, v)
    return name.strip()

def match_events(book_a_events: list[dict], book_b_events: list[dict], threshold: int = MATCH_THRESHOLD) -> list[tuple]:
    matched = []
    for a in book_a_events:
        a_home = normalize_team_name(a.get("home", ""))
        a_away = normalize_team_name(a.get("away", ""))
        for b in book_b_events:
            b_home = normalize_team_name(b.get("home", ""))
            b_away = normalize_team_name(b.get("away", ""))
            score = max(
                (fuzz.ratio(a_home, b_home) + fuzz.ratio(a_away, b_away)) / 2,
                (fuzz.ratio(a_home, b_away) + fuzz.ratio(a_away, b_home)) / 2,
            )
            if score >= threshold:
                matched.append((a, b))
                break
    return matched
