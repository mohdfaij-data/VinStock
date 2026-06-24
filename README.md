# VinStock — Phase 1

A stock research platform for Indian (NSE) equities: real-time fundamentals,
a screener with prebuilt + custom screens, watchlists, and user accounts.

## Running locally

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`. The SQLite database (`instance/vinstock.db`)
is created automatically on first run, along with the 184-stock universe.

## Before the screener shows results

Screens filter against a **cache table**, not live data, so the cache must
be populated first:

1. Go to `/admin/refresh`
2. Click "Run Refresh Now" (try with a small `limit` like 10 first — refreshing
   all ~184 stocks takes several minutes since each one is a live network call)
3. Once done, `/screens` will show real matches

This mirrors a production setup where a scheduled job (cron / APScheduler)
refreshes the cache every 6–12 hours, and users only ever read from cache.

## What's real vs. approximated

Everything in this app uses real yfinance data — nothing is fabricated.
However, several **screens are approximations** because true versions need
multi-year historical snapshots we don't store yet (that's Phase 2 — see
below). Each approximated screen is labeled in the UI with an "Approximated"
badge and an explanation of exactly what's missing. For example:

- "Low on 10-Year Average P/E" currently checks *low absolute P/E*, not P/E
  vs. the stock's own historical average (we'd need to store P/E over time).
- "Debt Reduction" checks *current* low Debt/Equity, not a multi-year
  decreasing trend.
- "Growth Without Dilution" checks growth rates but not share-count stability.

Fields with no available data source at all (Promoter/FII/DII holding,
Quick Ratio, Interest Coverage) show a "Coming soon" badge rather than a
guessed number.

## Architecture

```
providers/        Data layer abstraction (currently only yfinance_provider.py).
                   Adding NSE/BSE/FMP/Alpha Vantage later = new provider class,
                   no changes needed to routes or templates.
models/           SQLAlchemy models: Users, Watchlists, WatchlistStocks, Alerts,
                   SavedScreen, StockUniverse, StockMetricsCache.
services/
  auth_service.py        registration/login logic
  watchlist_service.py   watchlist CRUD logic
  stock_universe.py      the curated list of ~184 NSE stocks (data, not logic)
  collector.py           pulls each universe stock through the provider,
                          computes derived metrics + score, writes to cache
  screener_engine.py     evaluates prebuilt + custom screens against the cache
templates/        Jinja2 templates (server-rendered, no separate frontend build)
static/style.css   single stylesheet, extended (not rewritten) across phases
```

## Known limitations (please read before assuming something is broken)

- **yfinance is unofficial.** Yahoo can change response formats or rate-limit
  without notice. If many refreshes fail at once, that's the most likely cause.
- **Annual financials**: yfinance typically returns ~4 years, not 10.
- **Quarterly financials**: typically ~4-5 quarters.
- **Stock universe (184 symbols)**: hand-curated for Phase 1, not the full
  NSE listing. Index membership labels ("Nifty 50" etc.) are best-effort and
  should be reconciled against nseindia.com's official files before treating
  them as authoritative — NSE's index composition changes periodically.
- **Peer comparison**: hand-curated peer groups for ~20 major stocks only.
- **No password reset / email verification** yet — registration is
  email+password only, no email sending is wired up.
- **SECRET_KEY is a hardcoded dev value** in `app.py` — change this before
  any real deployment (use an environment variable).

## Migrating from SQLite to PostgreSQL later

Change one line in `app.py`:
```python
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://user:pass@host/dbname"
```
All models use standard SQLAlchemy types with no SQLite-specific features,
so no model changes are needed. Install `psycopg2-binary` and add it to
requirements.txt.

## Deploying to Render

1. Push this folder to a GitHub repo
2. New Web Service on Render → connect repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app` (already in `Procfile`)
5. **Important**: SQLite on Render's free tier is not persistent across
   deploys/restarts (ephemeral filesystem). For anything beyond a demo,
   add a managed PostgreSQL instance and point `SQLALCHEMY_DATABASE_URI`
   at it via an environment variable.
