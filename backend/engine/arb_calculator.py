from backend.engine.normalizer import american_to_decimal, match_events
from datetime import datetime

def calculate_arb(event_a: dict, event_b: dict) -> dict | None:
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
            }
            if best is None or profit_pct > best["profit_pct"]:
                best = result
    return best

def find_all_arbs(all_book_data: dict[str, list[dict]], min_profit: float = 0.5) -> list[dict]:
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
