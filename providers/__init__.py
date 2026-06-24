"""
providers package — the data layer abstraction.

To add a future source (NSE, BSE, Screener.in, Financial Modeling Prep,
Alpha Vantage, a custom DB): create a new file implementing
StockDataProvider (see base.py), then register it in get_provider() below.
app.py and the templates never import yfinance directly — they only ever
call get_provider().get_stock(symbol).
"""

from .yfinance_provider import YFinanceProvider

_PROVIDERS = {
    "yfinance": YFinanceProvider(),
    # "nse": NSEProvider(),                  # Phase 2
    # "screener": ScreenerImportProvider(),  # Phase 2
    # "fmp": FMPProvider(),                  # future
}

DEFAULT_PROVIDER = "yfinance"


def get_provider(name: str = None):
    return _PROVIDERS.get(name or DEFAULT_PROVIDER, _PROVIDERS[DEFAULT_PROVIDER])
