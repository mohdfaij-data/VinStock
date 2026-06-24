"""
models.py — SQLAlchemy models for VinStock.

Designed to start on SQLite and move to PostgreSQL/MySQL with no code
changes: we avoid SQLite-only types, use server-agnostic column types,
and keep all queries through the ORM (no raw SQLite-specific SQL).
To migrate later: change SQLALCHEMY_DATABASE_URI in app.py and run
`flask db upgrade` (Flask-Migrate is wired in app.py).
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


# ============================================================
# AUTH
# ============================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    watchlists = db.relationship("Watchlist", backref="owner", lazy=True, cascade="all, delete-orphan")
    preferences = db.relationship("UserPreference", backref="owner", uselist=False, cascade="all, delete-orphan")
    alerts = db.relationship("Alert", backref="owner", lazy=True, cascade="all, delete-orphan")
    saved_screens = db.relationship("SavedScreen", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class UserPreference(db.Model):
    __tablename__ = "user_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    currency_display = db.Column(db.String(10), default="INR")
    default_watchlist_id = db.Column(db.Integer, db.ForeignKey("watchlists.id"), nullable=True)
    email_alerts_enabled = db.Column(db.Boolean, default=True)
    theme = db.Column(db.String(20), default="light")


# ============================================================
# WATCHLISTS
# ============================================================

class Watchlist(db.Model):
    __tablename__ = "watchlists"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, default="My Watchlist")
    created_at = db.Column(db.DateTime, default=utcnow)

    items = db.relationship("WatchlistStock", backref="watchlist", lazy=True, cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_user_watchlist_name"),)


class WatchlistStock(db.Model):
    """One stock entry inside a watchlist, with personal notes/tags."""
    __tablename__ = "watchlist_stocks"

    id = db.Column(db.Integer, primary_key=True)
    watchlist_id = db.Column(db.Integer, db.ForeignKey("watchlists.id"), nullable=False, index=True)
    symbol = db.Column(db.String(30), nullable=False, index=True)   # e.g. "TCS.NS"
    notes = db.Column(db.Text, nullable=True)
    tag = db.Column(db.String(30), nullable=True)  # "Long Term" / "Swing" / "Dividend" / custom
    added_price = db.Column(db.Float, nullable=True)  # price at time of adding, for gain/loss tracking
    added_at = db.Column(db.DateTime, default=utcnow)

    __table_args__ = (db.UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_symbol"),)


# ============================================================
# ALERTS (architecture now, triggering engine is a later phase)
# ============================================================

class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    symbol = db.Column(db.String(30), nullable=False)
    condition = db.Column(db.String(20), nullable=False)   # "price_above" | "price_below" | "pe_below" | ...
    threshold = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    triggered_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)


# ============================================================
# SAVED CUSTOM SCREENS
# ============================================================

class SavedScreen(db.Model):
    """A user's custom screen — the filter definition is stored as JSON
    text so the schema doesn't need to change every time we add a new
    filterable metric."""
    __tablename__ = "saved_screens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    filter_json = db.Column(db.Text, nullable=False)  # JSON-encoded list of {metric, operator, value}
    created_at = db.Column(db.DateTime, default=utcnow)


# ============================================================
# STOCK UNIVERSE + METRICS CACHE (screener data pipeline)
# ============================================================

class StockUniverse(db.Model):
    """The maintained list of stocks the screener is allowed to scan.
    Kept separate from screening logic so the universe can grow from
    ~150 stocks to 500+ to the full NSE list without touching any
    filter code."""
    __tablename__ = "stock_universe"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    index_membership = db.Column(db.String(60), nullable=True)  # "Nifty 50" / "Nifty Next 50" / etc.
    sector = db.Column(db.String(80), nullable=True)
    is_active = db.Column(db.Boolean, default=True)  # allows disabling a symbol without deleting history


class StockMetricsCache(db.Model):
    """
    The precomputed, cached fundamentals for one stock — this is what the
    screener actually filters against. Populated by the data collector
    service on a schedule (every 6-12h), NOT on every page load.

    One row per symbol; updated in place on each refresh (we don't keep
    historical snapshots here — that would be a separate time-series
    table, a future phase).
    """
    __tablename__ = "stock_metrics_cache"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=True)
    sector = db.Column(db.String(80), nullable=True)
    industry = db.Column(db.String(120), nullable=True)

    # Price snapshot
    price = db.Column(db.Float, nullable=True)
    change_pct = db.Column(db.Float, nullable=True)
    high_52w = db.Column(db.Float, nullable=True)
    low_52w = db.Column(db.Float, nullable=True)

    # Valuation
    market_cap = db.Column(db.Float, nullable=True)
    pe_ratio = db.Column(db.Float, nullable=True)
    pb_ratio = db.Column(db.Float, nullable=True)
    peg_ratio = db.Column(db.Float, nullable=True)
    ev_to_ebitda = db.Column(db.Float, nullable=True)

    # Profitability
    roe = db.Column(db.Float, nullable=True)
    roce = db.Column(db.Float, nullable=True)
    roa = db.Column(db.Float, nullable=True)
    net_margin = db.Column(db.Float, nullable=True)
    operating_margin = db.Column(db.Float, nullable=True)

    # Financial health
    debt_to_equity = db.Column(db.Float, nullable=True)
    current_ratio = db.Column(db.Float, nullable=True)

    # Growth
    revenue_growth = db.Column(db.Float, nullable=True)
    earnings_growth = db.Column(db.Float, nullable=True)

    # Income
    dividend_yield = db.Column(db.Float, nullable=True)
    dividend_payout_ratio = db.Column(db.Float, nullable=True)

    # Cash flow
    free_cash_flow = db.Column(db.Float, nullable=True)

    # Shareholding (Phase 3 — stays NULL until a real data source exists)
    promoter_holding = db.Column(db.Float, nullable=True)
    fii_holding = db.Column(db.Float, nullable=True)
    dii_holding = db.Column(db.Float, nullable=True)

    # VinStock Score snapshot (so screens can filter/sort by score without recomputing)
    vinstock_score = db.Column(db.Float, nullable=True)
    vinstock_rating = db.Column(db.String(20), nullable=True)

    # Bookkeeping
    data_source = db.Column(db.String(30), default="yfinance")
    last_refreshed = db.Column(db.DateTime, default=utcnow)
    refresh_failed = db.Column(db.Boolean, default=False)
    refresh_error = db.Column(db.Text, nullable=True)


class ScreenRunCache(db.Model):
    """
    Cached RESULT of running a named screen (e.g. 'value_stocks'), so
    repeated hits within the cache window (~1hr) don't re-filter the
    whole universe. matched_symbols is a JSON-encoded list.
    """
    __tablename__ = "screen_run_cache"

    id = db.Column(db.Integer, primary_key=True)
    screen_key = db.Column(db.String(60), unique=True, nullable=False, index=True)
    matched_symbols_json = db.Column(db.Text, nullable=False)
    computed_at = db.Column(db.DateTime, default=utcnow)
