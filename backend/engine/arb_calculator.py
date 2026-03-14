from backend.engine.normalizer import american_to_decimal, match_events
from datetime import datetime


def find_arbs_from_events(events: list[dict], min_profit: float = 0.5) -> list[dict]:
    """
    For each game, find the best home odds and best away odds across ALL available
    bookmakers, then check if an arbitrage opportunity exists.

    This is far more powerful than pairwise book comparison — it discovers arbs
    that span any combination of books in a single pass.
    """
    arbs = []
    for event in events:
        books = event.get("books", {})
        if len(books) < 2:
            continue

        best_home: tuple | None = None  # (decimal_odds, book_name, american_str)
        best_away: tuple | None = None

        for book_name, odds in books.items():
            h = american_to_decimal(odds.get("home_odds", ""))
            a = american_to_decimal(odds.get("away_odds", ""))
            if h and (best_home is None or h > best_home[0]):
                best_home = (h, book_name, odds["home_odds"])
            if a and (best_away is None or a > best_away[0]):
                best_away = (a, book_name, odds["away_odds"])

        if not best_home or not best_away:
            continue

        inv_sum = (1 / best_home[0]) + (1 / best_away[0])
        if inv_sum >= 1.0:
            continue

        profit_pct = round((1 - inv_sum) * 100, 3)
        if profit_pct < min_profit:
            continue

        total = 100
        stake_home = round((total / best_home[0]) / inv_sum, 2)
        stake_away = round((total / best_away[0]) / inv_sum, 2)

        arbs.append({
            "sport": event["sport"],
            "home_team": event["home"],
            "away_team": event["away"],
            "book_home": best_home[1],
            "book_away": best_away[1],
            "home_odds": best_home[2],
            "away_odds": best_away[2],
            "profit_pct": profit_pct,
            "stake_home": stake_home,
            "stake_away": stake_away,
            "guaranteed_profit_per_100": round(total * (1 - inv_sum), 2),
            "found_at": datetime.utcnow().isoformat(),
            "books_checked": len(books),
        })

    return sorted(arbs, key=lambda x: x["profit_pct"], reverse=True)


def calculate_arb(event_a: dict, event_b: dict) -> dict | None:
    """Pairwise arb check between two single-book event records (scraper-only fallback)."""
    combos = [
        (event_a, event_b),
        (event_b, event_a),
    ]
    best = None
    for home_book, away_book in combos:
        dec_home = american_to_decimal(home_book.get("home_odds", ""))
        dec_away = american_to_decimal(away_book.get("away_odds", ""))
        if not dec_home or not dec_away:
            continue
        inv_sum = (1 / dec_home) + (1 / dec_away)
        if inv_sum < 1.0:
            profit_pct = round((1 - inv_sum) * 100, 3)
            total_stake = 100
            stake_home = round((total_stake / dec_home) / inv_sum, 2)
            stake_away = round((total_stake / dec_away) / inv_sum, 2)
            guaranteed_profit = round(total_stake * (1 - inv_sum), 2)
            result = {
                "sport": home_book.get("sport", "unknown"),
                "home_team": home_book.get("home", ""),
                "away_team": away_book.get("away", ""),
                "book_home": home_book.get("book", ""),
                "book_away": away_book.get("book", ""),
                "home_odds": home_book.get("home_odds", ""),
                "away_odds": away_book.get("away_odds", ""),
                "profit_pct": profit_pct,
                "stake_home": stake_home,
                "stake_away": stake_away,
                "guaranteed_profit_per_100": guaranteed_profit,
                "found_at": datetime.utcnow().isoformat(),
                "books_checked": 2,
            }
            if best is None or profit_pct > best["profit_pct"]:
                best = result
    return best


def find_all_arbs(all_book_data: dict[str, list[dict]], min_profit: float = 0.5) -> list[dict]:
    """Pairwise arb finder for flat scraped data (no-API fallback path)."""
    arbs = []
    books = list(all_book_data.keys())
    for i in range(len(books)):
        for j in range(i + 1, len(books)):
            book_a = books[i]
            book_b = books[j]
            matched = match_events(all_book_data[book_a], all_book_data[book_b])
            for event_a, event_b in matched:
                arb = calculate_arb(event_a, event_b)
                if arb and arb["profit_pct"] >= min_profit:
                    arbs.append(arb)
    return sorted(arbs, key=lambda x: x["profit_pct"], reverse=True)
