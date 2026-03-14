from backend.engine.normalizer import match_events, normalize_odds, decimal_to_implied
from itertools import combinations

# Default total bankroll for stake sizing
DEFAULT_BANKROLL = 1000.0


def calculate_arb(odds1: float, odds2: float, bankroll: float = DEFAULT_BANKROLL):
    """Calculate arbitrage profit and optimal stakes for a two-way market.

    Parameters
    ----------
    odds1, odds2 : float
        Decimal odds for the two outcomes.
    bankroll : float
        Total amount to split across both bets.

    Returns
    -------
    dict or None
        ``{"profit_pct", "stake1", "stake2", "payout"}`` when an arb exists.
    """
    if odds1 <= 1 or odds2 <= 1:
        return None

    imp1 = decimal_to_implied(odds1)
    imp2 = decimal_to_implied(odds2)
    total_implied = imp1 + imp2

    if total_implied >= 1:
        return None  # no arb

    profit_pct = round((1 / total_implied - 1) * 100, 4)
    stake1 = round(bankroll * imp1 / total_implied, 2)
    stake2 = round(bankroll * imp2 / total_implied, 2)
    payout = round(stake1 * odds1, 2)

    return {
        "profit_pct": profit_pct,
        "stake1": stake1,
        "stake2": stake2,
        "payout": payout,
    }


def find_all_arbs(data_by_book: dict, min_profit: float = 0.5) -> list:
    """Find every two-way arb across all supplied sportsbook data.

    Parameters
    ----------
    data_by_book : dict
        ``{"BookName": [{"event": ..., "outcome": ..., "odds": ...}, ...]}``
    min_profit : float
        Minimum profit percentage to include.

    Returns
    -------
    list of dict
        Each dict describes an arbitrage opportunity.
    """
    matched_events = match_events(data_by_book)
    arbs: list[dict] = []

    for event_group in matched_events:
        books_in_event = list(event_group["books"].keys())

        for book_a, book_b in combinations(books_in_event, 2):
            entry_a = event_group["books"][book_a]
            entry_b = event_group["books"][book_b]

            odds_a = entry_a["odds"]
            odds_b = entry_b["odds"]

            if odds_a <= 1 or odds_b <= 1:
                continue

            result = calculate_arb(odds_a, odds_b)
            if result and result["profit_pct"] >= min_profit:
                arbs.append(
                    {
                        "event": event_group["event"],
                        "market": "moneyline",
                        "book1": book_a,
                        "outcome1": entry_a["outcome"],
                        "odds1": odds_a,
                        "book2": book_b,
                        "outcome2": entry_b["outcome"],
                        "odds2": odds_b,
                        "profit_pct": result["profit_pct"],
                        "stake1": result["stake1"],
                        "stake2": result["stake2"],
                    }
                )

    return arbs
