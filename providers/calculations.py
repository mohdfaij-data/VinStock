"""
calculations.py — pure functions that derive ratios from raw financial
statement numbers. No provider-specific logic here; just math.

Every function returns None (never 0, never a guess) when an input is
missing or a division isn't meaningful (e.g. divide by zero).
"""


def safe_div(a, b):
    if a is None or b is None:
        return None
    try:
        if b == 0:
            return None
        return a / b
    except (TypeError, ZeroDivisionError):
        return None


def pct_change(new, old):
    """YoY/QoQ growth: (new - old) / abs(old)."""
    if new is None or old is None or old == 0:
        return None
    return (new - old) / abs(old)


def cagr(end_value, start_value, periods):
    """Compound annual growth rate over `periods` years."""
    if end_value is None or start_value is None or periods <= 0:
        return None
    if start_value <= 0 or end_value <= 0:
        return None  # CAGR undefined/misleading across sign changes
    return (end_value / start_value) ** (1 / periods) - 1


def roce(ebit, total_assets, current_liabilities):
    """Return on Capital Employed = EBIT / (Total Assets - Current Liabilities)."""
    if ebit is None or total_assets is None or current_liabilities is None:
        return None
    capital_employed = total_assets - current_liabilities
    return safe_div(ebit, capital_employed)


def quick_ratio(current_assets, inventory, current_liabilities):
    if current_assets is None or current_liabilities is None:
        return None
    inv = inventory or 0
    return safe_div(current_assets - inv, current_liabilities)


def cash_ratio(cash_and_equiv, current_liabilities):
    return safe_div(cash_and_equiv, current_liabilities)


def interest_coverage(ebit, interest_expense):
    if interest_expense is None or interest_expense == 0:
        return None
    return safe_div(ebit, abs(interest_expense))


def asset_turnover(revenue, total_assets):
    return safe_div(revenue, total_assets)


def free_cash_flow(operating_cf, capex):
    """FCF = CFO - Capex. capex is usually reported as a negative outflow;
    normalize by taking its absolute value as the amount spent."""
    if operating_cf is None or capex is None:
        return None
    return operating_cf - abs(capex)


def cash_per_share(total_cash, shares_outstanding):
    return safe_div(total_cash, shares_outstanding)


def dividend_payout_ratio(dividends_paid, net_profit):
    if dividends_paid is None or net_profit is None or net_profit == 0:
        return None
    return abs(dividends_paid) / net_profit


def build_trend_series(labels, values_dict_list, key):
    """
    Helper: given a list of per-period dicts (oldest->newest order assumed
    upstream) and a key, pull out a (labels, values) pair with None for
    missing entries, ready to drop into a FinancialSeries.
    """
    values = [d.get(key) for d in values_dict_list]
    return labels, values
