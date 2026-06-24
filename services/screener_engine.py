"""
screener_engine.py — filters StockMetricsCache rows (the precomputed
cache, NOT live yfinance calls) against prebuilt or custom screen
definitions.

Design: every screen — prebuilt or custom — is ultimately a list of
conditions: (metric_field, operator, value). This means prebuilt screens
and the custom screen builder share exactly one evaluation function,
so adding a new prebuilt screen is just adding a new condition list, and
the custom builder's UI maps 1:1 onto the same condition shape that's
stored as JSON in SavedScreen.filter_json.

Metrics are read directly off StockMetricsCache columns (no new live
fetches happen here) — this function should be fast (in-memory/SQL,
no network).
"""

OPERATORS = {
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "eq": lambda a, b: a is not None and a == b,
    "near_high": lambda a, b: a is not None and a >= b,  # used with computed pct-from-high
}

# Metrics exposed to BOTH prebuilt screens and the custom screen builder.
# Maps a UI-facing metric key -> StockMetricsCache column name.
FILTERABLE_METRICS = {
    "pe_ratio": "P/E Ratio",
    "pb_ratio": "P/B Ratio",
    "peg_ratio": "PEG Ratio",
    "ev_to_ebitda": "EV/EBITDA",
    "market_cap": "Market Cap",
    "roe": "ROE",
    "roce": "ROCE",
    "roa": "ROA",
    "net_margin": "Net Margin",
    "operating_margin": "Operating Margin",
    "debt_to_equity": "Debt/Equity",
    "current_ratio": "Current Ratio",
    "revenue_growth": "Revenue Growth (YoY)",
    "earnings_growth": "Earnings Growth (YoY)",
    "dividend_yield": "Dividend Yield",
    "dividend_payout_ratio": "Dividend Payout Ratio",
    "free_cash_flow": "Free Cash Flow",
    "vinstock_score": "VinStock Score",
    "change_pct": "Day Change %",
}


def evaluate_conditions(row, conditions):
    """row: a StockMetricsCache instance. conditions: list of
    {metric, operator, value} dicts. Returns True only if ALL conditions
    pass (AND logic) and the row isn't a failed/never-refreshed entry."""
    if row.refresh_failed:
        return False
    for cond in conditions:
        metric = cond["metric"]
        operator = cond["operator"]
        value = cond["value"]
        actual = getattr(row, metric, None)
        op_fn = OPERATORS.get(operator)
        if op_fn is None:
            continue
        if not op_fn(actual, value):
            return False
    return True


def run_screen(StockMetricsCache, conditions):
    """Run a condition list against the full cache table. Returns the
    list of matching StockMetricsCache rows. This hits the DB, not
    yfinance — should be fast even for the full universe."""
    rows = StockMetricsCache.query.filter_by(refresh_failed=False).all()
    return [r for r in rows if evaluate_conditions(r, conditions)]


def near_52w_high(row, threshold_pct=0.90):
    """True if price is within threshold_pct of the 52-week high."""
    if row.price is None or row.high_52w is None or row.high_52w == 0:
        return False
    return (row.price / row.high_52w) >= threshold_pct


# ============================================================
# PREBUILT SCREENS
# Each is a function (row -> bool) OR a plain condition list for the
# simple cases. Functions are used where the logic needs more than a
# single-column comparison (e.g. "near 52w high" needs two columns).
# ============================================================

def screen_value_stocks(row):
    """Low PE, low PB, strong balance sheet."""
    if row.refresh_failed:
        return False
    return (
        row.pe_ratio is not None and 0 < row.pe_ratio < 20 and
        row.pb_ratio is not None and 0 < row.pb_ratio < 3 and
        row.debt_to_equity is not None and row.debt_to_equity < 1
    )


def screen_high_roe_roce(row):
    if row.refresh_failed:
        return False
    return (
        row.roe is not None and row.roe > 0.15 and
        row.roce is not None and row.roce > 0.15
    )


def screen_debt_reduction(row):
    """Best-effort with single-snapshot data: low current Debt/Equity.
    True multi-year 'decreasing debt' needs historical snapshots — Phase 2."""
    if row.refresh_failed:
        return False
    return row.debt_to_equity is not None and row.debt_to_equity < 0.3


def screen_growth_without_dilution(row):
    """Revenue & profit growth > 10%. Share-count stability check needs
    historical shares-outstanding snapshots — Phase 2, so we approximate
    with growth alone for now."""
    if row.refresh_failed:
        return False
    return (
        row.revenue_growth is not None and row.revenue_growth > 0.10 and
        row.earnings_growth is not None and row.earnings_growth > 0.10
    )


def screen_capacity_expansion(row):
    """Approximated with revenue + operating margin strength — true capex
    trend needs balance-sheet asset growth history, Phase 2."""
    if row.refresh_failed:
        return False
    return (
        row.revenue_growth is not None and row.revenue_growth > 0.12 and
        row.operating_margin is not None and row.operating_margin > 0.10
    )


def screen_new_highs(row):
    if row.refresh_failed:
        return False
    return near_52w_high(row, threshold_pct=0.95)


def screen_consistent_compounders(row):
    if row.refresh_failed:
        return False
    return (
        row.revenue_growth is not None and row.revenue_growth > 0.08 and
        row.earnings_growth is not None and row.earnings_growth > 0.08 and
        row.debt_to_equity is not None and row.debt_to_equity < 0.5 and
        row.free_cash_flow is not None and row.free_cash_flow > 0
    )


def screen_high_dividend(row):
    if row.refresh_failed:
        return False
    return (
        row.dividend_yield is not None and row.dividend_yield > 0.02 and
        (row.dividend_payout_ratio is None or row.dividend_payout_ratio < 0.8)
    )


def screen_low_pe_avg(row):
    """'Low on 10yr average PE' needs historical average PE, which we
    don't have (Phase 2). Approximated here as simply low absolute PE
    relative to typical market levels, clearly labeled as an approximation
    in the UI."""
    if row.refresh_failed:
        return False
    return row.pe_ratio is not None and 0 < row.pe_ratio < 15


def screen_turnaround(row):
    """Profit growth positive after a presumably weak base, debt easing.
    True 'recovery from prior losses' needs multi-year history — Phase 2
    approximation: positive earnings growth + below-average debt."""
    if row.refresh_failed:
        return False
    return (
        row.earnings_growth is not None and row.earnings_growth > 0.15 and
        row.debt_to_equity is not None and row.debt_to_equity < 0.8
    )


PREBUILT_SCREENS = {
    "value_stocks": {
        "label": "Value Stocks",
        "description": "Low P/E, low P/B, strong balance sheet.",
        "fn": screen_value_stocks,
        "approximated": False,
    },
    "high_roe_roce": {
        "label": "High ROE + High ROCE",
        "description": "ROE > 15% and ROCE > 15%.",
        "fn": screen_high_roe_roce,
        "approximated": False,
    },
    "debt_reduction": {
        "label": "Debt Reduction",
        "description": "Low current Debt/Equity.",
        "fn": screen_debt_reduction,
        "approximated": True,
        "approximation_note": "Multi-year 'decreasing debt trend' needs historical snapshots (Phase 2). Currently shows low CURRENT debt/equity only.",
    },
    "growth_without_dilution": {
        "label": "Growth Without Dilution",
        "description": "Revenue & profit growth both above 10%.",
        "fn": screen_growth_without_dilution,
        "approximated": True,
        "approximation_note": "Share-count dilution check needs historical shares-outstanding data (Phase 2). Currently checks growth only.",
    },
    "capacity_expansion": {
        "label": "Capacity Expansion",
        "description": "Strong revenue growth with healthy operating margins.",
        "fn": screen_capacity_expansion,
        "approximated": True,
        "approximation_note": "True asset/capex growth tracking needs balance-sheet history (Phase 2). Approximated via revenue growth + margins.",
    },
    "new_highs": {
        "label": "Companies Creating New High",
        "description": "Trading within 5% of their 52-week high.",
        "fn": screen_new_highs,
        "approximated": True,
        "approximation_note": "Relative-strength-vs-market is not yet computed (Phase 2). Currently just proximity to 52W high.",
    },
    "consistent_compounders": {
        "label": "Consistent Compounders",
        "description": "Steady revenue & profit growth, low debt, positive free cash flow.",
        "fn": screen_consistent_compounders,
        "approximated": False,
    },
    "high_dividend": {
        "label": "High Dividend Stocks",
        "description": "Dividend yield > 2% with a sustainable payout ratio.",
        "fn": screen_high_dividend,
        "approximated": False,
    },
    "low_pe_avg": {
        "label": "Low on 10-Year Average P/E",
        "description": "Trading at a low P/E.",
        "fn": screen_low_pe_avg,
        "approximated": True,
        "approximation_note": "True comparison against the stock's own 10-year average P/E needs historical valuation history (Phase 2). Currently shows low ABSOLUTE P/E only.",
    },
    "turnaround": {
        "label": "Turnaround Stocks",
        "description": "Strong recent earnings growth with manageable debt.",
        "fn": screen_turnaround,
        "approximated": True,
        "approximation_note": "True 'recovering from prior losses' needs multi-year profit history (Phase 2). Approximated via current earnings growth + debt level.",
    },
}


def run_prebuilt_screen(StockMetricsCache, screen_key):
    """Returns (matched_rows, screen_meta) or (None, None) if screen_key unknown."""
    meta = PREBUILT_SCREENS.get(screen_key)
    if meta is None:
        return None, None
    rows = StockMetricsCache.query.filter_by(refresh_failed=False).all()
    matched = [r for r in rows if meta["fn"](r)]
    return matched, meta
