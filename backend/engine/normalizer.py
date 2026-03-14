from fuzzywuzzy import fuzz

# Minimum fuzzy-match score (0–100) to consider two event names the same.
# Set conservatively low to handle sportsbook naming variations (e.g.
# "LA Lakers" vs "Los Angeles Lakers", abbreviations, etc.).
MATCH_THRESHOLD = 70


def american_to_decimal(odds: float) -> float:
    """Convert American odds to decimal odds."""
    if odds >= 100:
        return round(odds / 100 + 1, 4)
    elif odds <= -100:
        return round(100 / abs(odds) + 1, 4)
    return 0.0


def decimal_to_implied(decimal_odds: float) -> float:
    """Convert decimal odds to an implied probability (0-1)."""
    if decimal_odds <= 0:
        return 0.0
    return round(1 / decimal_odds, 6)


def normalize_odds(odds_value) -> float:
    """Ensure odds are in decimal format.

    If the value looks like American odds (abs >= 100), convert it first.
    """
    try:
        odds = float(odds_value)
    except (TypeError, ValueError):
        return 0.0

    if abs(odds) >= 100:
        return american_to_decimal(odds)
    if odds > 1:
        return round(odds, 4)
    return 0.0


def fuzzy_match(name1: str, name2: str) -> bool:
    """Return True when two event / team names are similar enough."""
    score = fuzz.token_sort_ratio(name1.lower().strip(), name2.lower().strip())
    return score >= MATCH_THRESHOLD


def match_events(data_by_book: dict) -> list:
    """Match events across sportsbooks using fuzzy string matching.

    Parameters
    ----------
    data_by_book : dict
        ``{"BookName": [{"event": ..., "outcome": ..., "odds": ...}, ...]}``

    Returns
    -------
    list of dict
        Each dict groups the same event across books with normalised odds.
    """
    books = list(data_by_book.keys())
    if len(books) < 2:
        return []

    matched: list[dict] = []
    used_indices: dict[str, set] = {b: set() for b in books}

    for i, item_a in enumerate(data_by_book[books[0]]):
        event_a = item_a.get("event", "")
        if not event_a:
            continue

        group = {
            "event": event_a,
            "books": {
                books[0]: {
                    "outcome": item_a.get("outcome", ""),
                    "odds": normalize_odds(item_a.get("odds", 0)),
                }
            },
        }

        for other_book in books[1:]:
            for j, item_b in enumerate(data_by_book[other_book]):
                if j in used_indices[other_book]:
                    continue
                event_b = item_b.get("event", "")
                if fuzzy_match(event_a, event_b):
                    group["books"][other_book] = {
                        "outcome": item_b.get("outcome", ""),
                        "odds": normalize_odds(item_b.get("odds", 0)),
                    }
                    used_indices[other_book].add(j)
                    break

        if len(group["books"]) >= 2:
            matched.append(group)

    return matched
