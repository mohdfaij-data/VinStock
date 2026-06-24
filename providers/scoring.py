"""
scoring.py — the VinStock Score.

IMPORTANT: This is a heuristic scoring model we designed, not a
professional credit rating or investment recommendation. It is built
entirely from publicly available fundamental ratios and rewards/penalizes
based on commonly-used investing rules of thumb. It will be wrong for
some sectors (e.g. banks don't have "Operating Margin" the same way
industrials do) and should be displayed with that caveat in the UI.

Each of the 4 categories is scored 0-25. Total = 0-100.
Any category where the required inputs are missing returns None for that
category (and is excluded from the total, with the total then rescaled to
the categories that ARE available) — we never invent a sub-score from
missing data.
"""


def _clamp(value, low=0, high=25):
    return max(low, min(high, value))


def score_valuation(pe, pb, peg, ev_ebitda):
    """Lower valuation multiples score higher. 25 pts max, split across
    4 sub-checks worth ~6.25 each. Missing inputs just don't contribute
    (and the available max is rescaled)."""
    parts = []

    if pe is not None and pe > 0:
        # PE < 15 -> full marks, PE > 50 -> 0, linear between
        parts.append(_clamp(6.25 * (1 - (pe - 15) / 35), 0, 6.25))
    if pb is not None and pb > 0:
        parts.append(_clamp(6.25 * (1 - (pb - 1) / 7), 0, 6.25))
    if peg is not None and peg > 0:
        # PEG ~1 is considered fair value
        parts.append(_clamp(6.25 * (1 - abs(peg - 1) / 2), 0, 6.25))
    if ev_ebitda is not None and ev_ebitda > 0:
        parts.append(_clamp(6.25 * (1 - (ev_ebitda - 8) / 25), 0, 6.25))

    if not parts:
        return None
    # Rescale to 25 based on how many sub-checks we actually had
    return round(sum(parts) / len(parts) * 4, 1)


def score_growth(revenue_growth, earnings_growth, eps_growth=None):
    parts = []
    for g in (revenue_growth, earnings_growth, eps_growth):
        if g is not None:
            # 0% growth -> ~half marks, 25%+ -> full marks, negative -> low
            parts.append(_clamp(8.33 * (1 + g / 0.25), 0, 8.33))
    if not parts:
        return None
    return round(sum(parts) / len(parts) * 3, 1)


def score_profitability(roe, roce, net_margin):
    parts = []
    if roe is not None:
        parts.append(_clamp(8.33 * (roe / 0.20), 0, 8.33))   # 20% ROE -> full marks
    if roce is not None:
        parts.append(_clamp(8.33 * (roce / 0.20), 0, 8.33))
    if net_margin is not None:
        parts.append(_clamp(8.33 * (net_margin / 0.20), 0, 8.33))
    if not parts:
        return None
    return round(sum(parts) / len(parts) * 3, 1)


def score_financial_health(debt_to_equity, current_ratio, interest_coverage):
    parts = []
    if debt_to_equity is not None:
        # D/E of 0 -> full marks, D/E of 2+ -> 0
        parts.append(_clamp(8.33 * (1 - debt_to_equity / 2), 0, 8.33))
    if current_ratio is not None:
        # current ratio of 1.5-3 considered healthy
        if current_ratio < 1:
            parts.append(_clamp(8.33 * current_ratio, 0, 8.33))
        else:
            parts.append(_clamp(8.33 * (1 - abs(current_ratio - 2) / 4), 0, 8.33))
    if interest_coverage is not None:
        parts.append(_clamp(8.33 * (interest_coverage / 10), 0, 8.33))
    if not parts:
        return None
    return round(sum(parts) / len(parts) * 3, 1)


def rating_label(total):
    if total is None:
        return "Not enough data"
    if total >= 90:
        return "Strong Buy"
    if total >= 80:
        return "Buy"
    if total >= 70:
        return "Hold"
    if total >= 60:
        return "Weak"
    return "Avoid"


def compute_vinstock_score(metrics: dict):
    """
    metrics: dict with keys pe, pb, peg, ev_ebitda, revenue_growth,
    earnings_growth, eps_growth, roe, roce, net_margin, debt_to_equity,
    current_ratio, interest_coverage — any of which may be None.

    Returns: {
      'valuation': float|None, 'growth': float|None,
      'profitability': float|None, 'financial_health': float|None,
      'total': float|None, 'rating': str, 'categories_used': int
    }
    """
    v = score_valuation(metrics.get("pe"), metrics.get("pb"),
                          metrics.get("peg"), metrics.get("ev_ebitda"))
    g = score_growth(metrics.get("revenue_growth"), metrics.get("earnings_growth"),
                       metrics.get("eps_growth"))
    p = score_profitability(metrics.get("roe"), metrics.get("roce"),
                              metrics.get("net_margin"))
    f = score_financial_health(metrics.get("debt_to_equity"), metrics.get("current_ratio"),
                                 metrics.get("interest_coverage"))

    available = [x for x in (v, g, p, f) if x is not None]
    if not available:
        total = None
    else:
        # Each available category is out of 25; rescale sum to /100
        # proportional to how many categories we actually have data for.
        total = round(sum(available) / len(available) * 4, 1)
        total = min(total, 100)

    return {
        "valuation": v,
        "growth": g,
        "profitability": p,
        "financial_health": f,
        "total": total,
        "rating": rating_label(total),
        "categories_used": len(available),
    }
