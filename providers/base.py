"""
StockDataProvider — abstract interface every data source must implement.

Why this exists:
VinStock currently runs entirely on yfinance. Future sources (NSE/BSE,
Screener.in exports, Financial Modeling Prep, Alpha Vantage, a custom DB)
will each have different field names, units, and quirks. The frontend and
app.py should never talk to yfinance directly — they should talk to a
StockDataProvider, so swapping or combining sources later means writing a
new provider class, not rewriting templates or routes.

Every provider returns the SAME normalized shape (see NormalizedStock below),
regardless of where the data actually came from. Fields that a provider
cannot supply MUST be returned as None — never fabricated. The frontend
is responsible for rendering None as "Coming soon" / "—".
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FinancialSeries:
    """A single line item across multiple periods, e.g. Revenue across 4 years."""
    labels: list = field(default_factory=list)   # e.g. ["FY2022", "FY2023", "FY2024", "FY2025"]
    values: list = field(default_factory=list)   # same length as labels; None for missing periods
    unit: str = "INR"                              # raw currency unit, value is NOT pre-scaled


@dataclass
class NormalizedStock:
    """
    The common shape every provider must fill in.
    Unavailable fields stay None / empty — the template decides how to
    show that ("Coming soon" badge), the provider never invents a number.
    """
    # Identity
    symbol: str = ""
    name: str = ""
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

    # Live price
    price: Optional[float] = None
    prev_close: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    beta: Optional[float] = None

    # Valuation snapshot (current/latest)
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    pb_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None
    price_to_sales: Optional[float] = None
    eps: Optional[float] = None
    book_value: Optional[float] = None
    face_value: Optional[float] = None
    shares_outstanding: Optional[float] = None
    dividend_yield: Optional[float] = None          # stored as a fraction, e.g. 0.012 = 1.2%
    dividend_payout_ratio: Optional[float] = None    # fraction

    # Profitability snapshot
    roe: Optional[float] = None             # fraction
    roa: Optional[float] = None             # fraction
    roce: Optional[float] = None            # fraction, derived
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None

    # Financial health snapshot
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None       # derived
    cash_ratio: Optional[float] = None        # derived
    interest_coverage: Optional[float] = None  # derived
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    cash_per_share: Optional[float] = None    # derived

    # Efficiency snapshot
    asset_turnover: Optional[float] = None    # derived

    # Growth snapshots (YoY, latest available period vs prior)
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    book_value_growth: Optional[float] = None  # derived if 2+ periods present
    fcf_growth: Optional[float] = None         # derived

    # Price history for the price chart
    price_chart_labels: list = field(default_factory=list)
    price_chart_values: list = field(default_factory=list)

    # Multi-period annual financial statement series
    revenue_annual: Optional[FinancialSeries] = None
    operating_revenue_annual: Optional[FinancialSeries] = None
    operating_profit_annual: Optional[FinancialSeries] = None
    ebitda_annual: Optional[FinancialSeries] = None
    net_profit_annual: Optional[FinancialSeries] = None
    eps_annual: Optional[FinancialSeries] = None

    total_assets_annual: Optional[FinancialSeries] = None
    total_liabilities_annual: Optional[FinancialSeries] = None
    equity_annual: Optional[FinancialSeries] = None
    debt_annual: Optional[FinancialSeries] = None
    cash_annual: Optional[FinancialSeries] = None

    operating_cf_annual: Optional[FinancialSeries] = None
    investing_cf_annual: Optional[FinancialSeries] = None
    financing_cf_annual: Optional[FinancialSeries] = None
    free_cf_annual: Optional[FinancialSeries] = None

    # Quarterly (best-effort; yfinance typically gives ~4-5 quarters)
    revenue_quarterly: Optional[FinancialSeries] = None
    net_profit_quarterly: Optional[FinancialSeries] = None
    eps_quarterly: Optional[FinancialSeries] = None

    # Derived multi-period ratio trends (computed from the series above)
    roe_trend: Optional[FinancialSeries] = None
    roce_trend: Optional[FinancialSeries] = None
    debt_trend: Optional[FinancialSeries] = None

    # Shareholding (Phase 3 — always None on yfinance-backed providers)
    promoter_holding: Optional[float] = None
    fii_holding: Optional[float] = None
    dii_holding: Optional[float] = None
    public_holding: Optional[float] = None

    # Bookkeeping: which provider(s) actually supplied this data,
    # useful for "data source" badges and debugging.
    source: str = ""
    warnings: list = field(default_factory=list)


class StockDataProvider(ABC):
    """Every concrete provider (YFinanceProvider, NSEProvider, etc.) implements this."""

    name: str = "base"

    @abstractmethod
    def get_stock(self, symbol: str) -> NormalizedStock:
        """Fetch and normalize all available data for a symbol. Must not raise
        for routine 'data missing' cases — leave fields None instead. May raise
        for genuine failures (symbol not found, network down)."""
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str) -> list:
        """Return a list of {symbol, name} matches for a query string."""
        raise NotImplementedError
