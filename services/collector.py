"""
collector.py — the data collection service.

This is the "Data Collector" stage of the pipeline:
  Data Source -> Data Collector -> Database -> Metrics Engine ->
  VinStock Score Engine -> Cache Layer -> Frontend

Responsibility: pull each symbol in the universe through the active
StockDataProvider, compute the derived metrics + VinStock Score, and
write the result into StockMetricsCache. This is meant to be invoked by
a scheduler (cron / APScheduler / a manual admin route) every 6-12 hours
— NOT on every screener page load. See run_refresh_all() and
run_refresh_one().

Failures on individual symbols are caught and recorded (refresh_failed,
refresh_error) so one bad symbol never blocks the rest of the universe
from refreshing.
"""

from datetime import datetime, timezone
import time

from providers import get_provider
from providers import calculations as calc
from providers.scoring import compute_vinstock_score
from services.stock_universe import get_universe


def utcnow():
    return datetime.now(timezone.utc)


def _compute_row_fields(symbol, provider):
    """Fetch one symbol via the provider and build the dict of fields
    matching StockMetricsCache's columns. Raises on hard failures
    (caller is responsible for catching and recording refresh_failed)."""
    s = provider.get_stock(symbol)

    eps_growth = None
    if s.eps_annual and len(s.eps_annual.values) >= 2:
        eps_growth = calc.pct_change(s.eps_annual.values[-1], s.eps_annual.values[-2])

    fcf_latest = None
    if s.free_cf_annual and s.free_cf_annual.values:
        fcf_latest = s.free_cf_annual.values[-1]

    score = compute_vinstock_score({
        "pe": s.pe_ratio, "pb": s.pb_ratio, "peg": s.peg_ratio, "ev_ebitda": s.ev_to_ebitda,
        "revenue_growth": s.revenue_growth, "earnings_growth": s.earnings_growth, "eps_growth": eps_growth,
        "roe": s.roe, "roce": s.roce, "net_margin": s.net_margin,
        "debt_to_equity": s.debt_to_equity, "current_ratio": s.current_ratio,
        "interest_coverage": None,
    })

    change_pct = s.change_pct

    return {
        "name": s.name,
        "sector": s.sector,
        "industry": s.industry,
        "price": s.price,
        "change_pct": change_pct,
        "high_52w": s.high_52w,
        "low_52w": s.low_52w,
        "market_cap": s.market_cap,
        "pe_ratio": s.pe_ratio,
        "pb_ratio": s.pb_ratio,
        "peg_ratio": s.peg_ratio,
        "ev_to_ebitda": s.ev_to_ebitda,
        "roe": s.roe,
        "roce": s.roce,
        "roa": s.roa,
        "net_margin": s.net_margin,
        "operating_margin": s.operating_margin,
        "debt_to_equity": s.debt_to_equity,
        "current_ratio": s.current_ratio,
        "revenue_growth": s.revenue_growth,
        "earnings_growth": s.earnings_growth,
        "dividend_yield": s.dividend_yield,
        "dividend_payout_ratio": s.dividend_payout_ratio,
        "free_cash_flow": fcf_latest,
        # Shareholding fields intentionally omitted (stay NULL) — no data source yet (Phase 3)
        "vinstock_score": score["total"],
        "vinstock_rating": score["rating"],
        "data_source": provider.name,
        "last_refreshed": utcnow(),
        "refresh_failed": False,
        "refresh_error": None,
    }


def run_refresh_one(symbol, db, StockMetricsCache, provider=None, sleep_after=0.0):
    """
    Refresh a single symbol's cache row. Creates the row if it doesn't
    exist yet. Commits the session. Returns (success: bool, error: str|None).
    `sleep_after` lets callers throttle between requests when refreshing
    many symbols in a row, to be polite to the upstream data source.
    """
    provider = provider or get_provider()
    row = StockMetricsCache.query.filter_by(symbol=symbol).first()
    if row is None:
        row = StockMetricsCache(symbol=symbol)
        db.session.add(row)

    try:
        fields = _compute_row_fields(symbol, provider)
        for k, v in fields.items():
            setattr(row, k, v)
        db.session.commit()
        success, error = True, None
    except Exception as e:
        row.refresh_failed = True
        row.refresh_error = str(e)
        row.last_refreshed = utcnow()
        db.session.commit()
        success, error = False, str(e)

    if sleep_after:
        time.sleep(sleep_after)

    return success, error


def run_refresh_all(db, StockMetricsCache, provider=None, throttle_seconds=0.3, limit=None, on_progress=None):
    """
    Refresh every symbol in the universe. Intended to be triggered by a
    scheduler or an admin/manual 'Refresh data' action — NOT by a user's
    page load. Each yfinance call is a network round-trip, so this can
    take minutes for the full ~184-stock universe; throttle_seconds adds
    a small delay between calls to avoid hammering Yahoo's servers.

    on_progress(done, total, symbol, success) is called after each symbol,
    useful for showing progress in an admin UI.

    Returns a summary dict: {total, succeeded, failed, failed_symbols}.
    """
    provider = provider or get_provider()
    universe = get_universe()
    if limit:
        universe = universe[:limit]

    succeeded, failed, failed_symbols = 0, 0, []

    for i, (symbol, name, index_membership, sector) in enumerate(universe):
        ok, err = run_refresh_one(symbol, db, StockMetricsCache, provider=provider, sleep_after=throttle_seconds)
        if ok:
            succeeded += 1
        else:
            failed += 1
            failed_symbols.append((symbol, err))
        if on_progress:
            on_progress(i + 1, len(universe), symbol, ok)

    return {
        "total": len(universe),
        "succeeded": succeeded,
        "failed": failed,
        "failed_symbols": failed_symbols,
        "completed_at": utcnow(),
    }


def seed_universe_table(db, StockUniverse):
    """Idempotently populate StockUniverse from the curated list. Safe to
    call repeatedly — updates existing rows rather than duplicating."""
    for symbol, name, index_membership, sector in get_universe():
        row = StockUniverse.query.filter_by(symbol=symbol).first()
        if row is None:
            row = StockUniverse(symbol=symbol)
            db.session.add(row)
        row.name = name
        row.index_membership = index_membership
        row.sector = sector
        row.is_active = True
    db.session.commit()
