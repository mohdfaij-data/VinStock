"""
yfinance_provider.py — concrete StockDataProvider backed by the yfinance
library (unofficial Yahoo Finance wrapper).

Known limits of this provider (do not try to work around these by faking
data — surface them as None/"Coming soon" instead):
  - Annual financials: yfinance typically returns ~4 years, not 10.
  - Quarterly financials: typically ~4-5 quarters.
  - No shareholding pattern (promoter/FII/DII/public %) — that's NSE/BSE
    bulk data, not in Yahoo Finance at all.
  - No official peer/competitor list — we use a hand-curated mapping
    (see PEER_MAP below) as a best-effort stand-in.
  - dividendYield field has been inconsistent across yfinance versions
    (sometimes a fraction like 0.012, sometimes already a percent like
    1.2). We defensively detect which scale it's in.
"""

from datetime import datetime
import yfinance as yf

from .base import StockDataProvider, NormalizedStock, FinancialSeries
from . import calculations as calc


# Best-effort hand-curated peer groups (Phase 1). Extend as needed.
PEER_MAP = {
    "RELIANCE.NS": ["ONGC.NS", "BPCL.NS", "IOC.NS"],
    "TCS.NS": ["INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "INFY.NS": ["TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "WIPRO.NS": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "TECHM.NS"],
    "HCLTECH.NS": ["TCS.NS", "INFY.NS", "WIPRO.NS", "TECHM.NS"],
    "HDFCBANK.NS": ["ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS"],
    "ICICIBANK.NS": ["HDFCBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS"],
    "KOTAKBANK.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "SBIN.NS"],
    "AXISBANK.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS"],
    "SBIN.NS": ["HDFCBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS"],
    "HINDUNILVR.NS": ["NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "ITC.NS"],
    "ITC.NS": ["HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
    "MARUTI.NS": ["TATAMOTORS.NS", "M&M.NS", "HYUNDAI.NS"],
    "TATAMOTORS.NS": ["MARUTI.NS", "M&M.NS"],
    "TITAN.NS": ["KALYANKJIL.NS", "ASIANPAINT.NS"],
    "ASIANPAINT.NS": ["BERGEPAINT.NS", "TITAN.NS"],
    "SUNPHARMA.NS": ["DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
    "TATASTEEL.NS": ["JSWSTEEL.NS", "JINDALSTEL.NS", "SAIL.NS"],
    "BHARTIARTL.NS": ["IDEA.NS", "RELIANCE.NS"],
    "LT.NS": ["ADANIPORTS.NS", "SIEMENS.NS"],
}


def _scale_dividend_yield(raw):
    """yfinance has returned dividendYield as both a fraction (0.012) and
    a whole percent (1.2) across versions. Heuristic: real-world dividend
    yields are almost never above ~20%. If raw > 1, assume it's already
    a percent and convert to fraction; if it's absurdly large (>50), it's
    very likely a units bug upstream — treat as unavailable rather than
    show a misleading number."""
    if raw is None:
        return None
    try:
        raw = float(raw)
    except (TypeError, ValueError):
        return None
    if raw > 50:
        return None  # clearly bad data from the API, don't show it
    if raw > 1:
        return raw / 100  # was already a percent, normalize to fraction
    return raw


def _series_from_df(df, row_names, periods=10):
    """
    Pull a row from a yfinance financials DataFrame (rows=line items,
    columns=period-end dates, newest first) and return a FinancialSeries
    oldest->newest, capped at `periods`. row_names is a list of candidate
    labels to try (yfinance's exact label varies by company/version).
    """
    if df is None or df.empty:
        return None
    row = None
    for name in row_names:
        if name in df.index:
            row = df.loc[name]
            break
    if row is None:
        return None

    row = row.dropna()
    row = row.iloc[:periods]  # newest-first, take most recent N
    row = row.iloc[::-1]      # flip to oldest->newest for charting

    # Quarterly periods need month granularity; annual periods just need the year.
    is_quarterly = periods <= 8
    if is_quarterly:
        labels = [d.strftime("%b %Y") if hasattr(d, "strftime") else str(d) for d in row.index]
    else:
        labels = [d.strftime("%Y") if hasattr(d, "strftime") else str(d) for d in row.index]
    values = [round(float(v), 2) if v is not None else None for v in row.values]
    return FinancialSeries(labels=labels, values=values)


class YFinanceProvider(StockDataProvider):
    name = "yfinance"

    def search(self, query: str) -> list:
        # Local lookup only in Phase 1 — yfinance has no symbol-search
        # endpoint we rely on; app.py keeps its own COMPANY_INDEX for this.
        return []

    def get_stock(self, symbol: str) -> NormalizedStock:
        result = NormalizedStock(symbol=symbol, source=self.name)
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}


        if not info or (info.get("regularMarketPrice") is None and info.get("currentPrice") is None):
            raise ValueError(f"No data returned for '{symbol}'")

        # ---- Identity ----
        result.name = info.get("longName") or info.get("shortName") or symbol
        result.sector = info.get("sector")
        result.industry = info.get("industry")
        result.description = info.get("longBusinessSummary")

        # ---- Live price ----
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose")
        result.price = price
        result.prev_close = prev_close
        if price is not None and prev_close:
            result.change = price - prev_close
            result.change_pct = (result.change / prev_close) * 100
        result.high_52w = info.get("fiftyTwoWeekHigh")
        result.low_52w = info.get("fiftyTwoWeekLow")
        result.beta = info.get("beta")

        # ---- Valuation snapshot ----
        result.market_cap = info.get("marketCap")
        result.enterprise_value = info.get("enterpriseValue")
        result.pe_ratio = info.get("trailingPE")
        result.forward_pe = info.get("forwardPE")
        result.pb_ratio = info.get("priceToBook")
        result.peg_ratio = info.get("trailingPegRatio") or info.get("pegRatio")
        result.ev_to_ebitda = info.get("enterpriseToEbitda")
        result.ev_to_revenue = info.get("enterpriseToRevenue")
        result.price_to_sales = info.get("priceToSalesTrailing12Months")
        result.eps = info.get("trailingEps")
        result.book_value = info.get("bookValue")
        result.face_value = info.get("faceValue")  # rarely present
        result.shares_outstanding = info.get("sharesOutstanding")
        result.dividend_yield = _scale_dividend_yield(info.get("dividendYield"))
        result.dividend_payout_ratio = info.get("payoutRatio")

        # ---- Profitability snapshot ----
        result.roe = info.get("returnOnEquity")
        result.roa = info.get("returnOnAssets")
        result.gross_margin = info.get("grossMargins")
        result.operating_margin = info.get("operatingMargins")
        result.net_margin = info.get("profitMargins")

        # ---- Financial health snapshot ----
        result.debt_to_equity = info.get("debtToEquity")
        if result.debt_to_equity is not None:
            result.debt_to_equity = result.debt_to_equity / 100  # yfinance gives this as a %, normalize to a ratio
        result.current_ratio = info.get("currentRatio")
        result.total_cash = info.get("totalCash")
        result.total_debt = info.get("totalDebt")
        result.cash_per_share = calc.cash_per_share(result.total_cash, result.shares_outstanding)

        # ---- Growth snapshot (yfinance gives single latest YoY figures) ----
        result.revenue_growth = info.get("revenueGrowth")
        result.earnings_growth = info.get("earningsGrowth")

        # ---- Price history for chart ----
        try:
            hist = ticker.history(period="6mo")
            result.price_chart_labels = [d.strftime("%d %b") for d in hist.index]
            result.price_chart_values = [round(v, 2) for v in hist["Close"].tolist()]
        except Exception:
            result.warnings.append("Price history unavailable")

        # ---- Annual financial statements ----
        try:
            income = ticker.financials  # columns = years, newest first
            balance = ticker.balance_sheet
            cashflow = ticker.cashflow

            result.revenue_annual = _series_from_df(income, ["Total Revenue", "TotalRevenue"])
            result.operating_revenue_annual = _series_from_df(income, ["Operating Revenue"])
            result.operating_profit_annual = _series_from_df(income, ["Operating Income", "OperatingIncome"])
            result.ebitda_annual = _series_from_df(income, ["EBITDA"])
            result.net_profit_annual = _series_from_df(income, ["Net Income", "NetIncome", "Net Income Common Stockholders"])
            result.eps_annual = _series_from_df(income, ["Basic EPS", "Diluted EPS"])

            result.total_assets_annual = _series_from_df(balance, ["Total Assets", "TotalAssets"])
            result.total_liabilities_annual = _series_from_df(balance, ["Total Liabilities Net Minority Interest", "Total Liab"])
            result.equity_annual = _series_from_df(balance, ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"])
            result.debt_annual = _series_from_df(balance, ["Total Debt"])
            result.cash_annual = _series_from_df(balance, ["Cash And Cash Equivalents", "Cash"])

            result.operating_cf_annual = _series_from_df(cashflow, ["Operating Cash Flow", "Total Cash From Operating Activities"])
            result.investing_cf_annual = _series_from_df(cashflow, ["Investing Cash Flow", "Total Cashflows From Investing Activities"])
            result.financing_cf_annual = _series_from_df(cashflow, ["Financing Cash Flow", "Total Cash From Financing Activities"])
            free_cf = _series_from_df(cashflow, ["Free Cash Flow"])
            result.free_cf_annual = free_cf

            # ---- Derived: ROCE trend, ROE trend, Debt trend across periods ----
            if result.net_profit_annual and result.equity_annual:
                labels = result.net_profit_annual.labels
                roe_vals = []
                eq_by_label = dict(zip(result.equity_annual.labels, result.equity_annual.values))
                for lbl, np_val in zip(labels, result.net_profit_annual.values):
                    eq_val = eq_by_label.get(lbl)
                    roe_vals.append(calc.safe_div(np_val, eq_val))
                result.roe_trend = FinancialSeries(labels=labels, values=roe_vals)

            if result.operating_profit_annual and result.total_assets_annual:
                labels = result.operating_profit_annual.labels
                roce_vals = []
                ta_by_label = dict(zip(result.total_assets_annual.labels, result.total_assets_annual.values))
                for lbl, op_val in zip(labels, result.operating_profit_annual.values):
                    ta_val = ta_by_label.get(lbl)
                    roce_vals.append(calc.safe_div(op_val, ta_val))
                result.roce_trend = FinancialSeries(labels=labels, values=roce_vals)

            if result.debt_annual:
                result.debt_trend = result.debt_annual

            # ---- Derived ROCE (latest period only, for Ratios tab) ----
            if result.operating_profit_annual and result.total_assets_annual and result.total_liabilities_annual:
                try:
                    latest_ebit = result.operating_profit_annual.values[-1]
                    latest_ta = result.total_assets_annual.values[-1]
                    latest_tl = result.total_liabilities_annual.values[-1]
                    result.roce = calc.roce(latest_ebit, latest_ta, latest_tl)
                except (IndexError, TypeError):
                    pass

        except Exception as e:
            result.warnings.append(f"Annual financials partially unavailable: {e}")

        # ---- Quarterly statements (best effort) ----
        try:
            q_income = ticker.quarterly_financials
            result.revenue_quarterly = _series_from_df(q_income, ["Total Revenue", "TotalRevenue"], periods=5)
            result.net_profit_quarterly = _series_from_df(q_income, ["Net Income", "NetIncome", "Net Income Common Stockholders"], periods=5)
            result.eps_quarterly = _series_from_df(q_income, ["Basic EPS", "Diluted EPS"], periods=5)
        except Exception as e:
            result.warnings.append(f"Quarterly financials unavailable: {e}")

        return result

    def get_peers(self, symbol: str) -> list:
        """Best-effort peer list. Returns [] if no mapping exists for this symbol."""
        return PEER_MAP.get(symbol, [])
