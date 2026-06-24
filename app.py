import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import csv
import io

from models import db, User, UserPreference, Watchlist, WatchlistStock, Alert, SavedScreen, StockUniverse, StockMetricsCache, ScreenRunCache
from providers import get_provider
from providers import calculations as calc
from providers import formatters as fmt
from providers.scoring import compute_vinstock_score
from services import auth_service, watchlist_service
from services.stock_universe import get_universe
from services.collector import run_refresh_all, run_refresh_one, seed_universe_table
from services.screener_engine import PREBUILT_SCREENS, run_prebuilt_screen, run_screen, FILTERABLE_METRICS


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vinstock.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
        seed_universe_table(db, StockUniverse)

    register_routes(app)
    return app


# ---------------------------------------------------------------
QUICK_ANALYZE = [
    {"symbol": "RELIANCE.NS", "name": "Reliance"},
    {"symbol": "TCS.NS", "name": "TCS"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank"},
    {"symbol": "INFY.NS", "name": "Infosys"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank"},
    {"symbol": "HINDUNILVR.NS", "name": "HUL"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki"},
    {"symbol": "TITAN.NS", "name": "Titan Company"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints"},
]

NAME_LOOKUP = {s: n for s, n, _, _ in get_universe()}
COMPANY_INDEX = [{"symbol": s, "name": n} for s, n, _, _ in get_universe()]


def normalize_symbol(symbol):
    symbol = symbol.upper().strip()
    if "." not in symbol:
        symbol = f"{symbol}.NS"
    return symbol


def _series_or_none(series):
    if series is None:
        return None
    return {"labels": series.labels, "values": series.values}


def register_routes(app):

    # ============================================================
    # HOME / SEARCH
    # ============================================================
    @app.route("/")
    def home():
        return render_template("index.html", quick_analyze=QUICK_ANALYZE)
    @app.route("/about")
    def about():
      return render_template("about.html")
    @app.route("/search")
    def search():
        q = request.args.get("q", "").strip().lower()
        if not q:
            return jsonify([])
        results = [c for c in COMPANY_INDEX if q in c["name"].lower() or q in c["symbol"].lower()]
        return jsonify(results[:8])

    # ============================================================
    # AUTH
    # ============================================================
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        if request.method == "POST":
            email = request.form.get("email", "")
            name = request.form.get("name", "")
            password = request.form.get("password", "")
            user, error = auth_service.register_user(db, User, UserPreference, Watchlist, email, name, password)
            if error:
                flash(error, "error")
                return render_template("register.html", email=email, name=name)
            login_user(user)
            flash("Welcome to VinStock!", "success")
            return redirect(url_for("home"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        if request.method == "POST":
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            user, error = auth_service.authenticate_user(User, email, password)
            if error:
                flash(error, "error")
                return render_template("login.html", email=email)
            login_user(user)
            next_url = request.args.get("next") or url_for("home")
            return redirect(next_url)
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You've been logged out.", "success")
        return redirect(url_for("home"))

    # ============================================================
    # WATCHLIST
    # ============================================================
    @app.route("/watchlist")
    @login_required
    def watchlist_page():
        watchlists = Watchlist.query.filter_by(user_id=current_user.id).all()
        selected_id = request.args.get("id", type=int)
        selected = None
        if selected_id:
            selected = Watchlist.query.filter_by(id=selected_id, user_id=current_user.id).first()
        if selected is None and watchlists:
            selected = watchlists[0]

        items_view = []
        if selected:
            provider = get_provider()
            for item in selected.items:
                cache_row = StockMetricsCache.query.filter_by(symbol=item.symbol).first()
                current_price = cache_row.price if cache_row else None
                gain_loss_pct = None
                if current_price is not None and item.added_price:
                    gain_loss_pct = calc.pct_change(current_price, item.added_price)
                items_view.append({
                    "symbol": item.symbol,
                    "name": NAME_LOOKUP.get(item.symbol, item.symbol),
                    "notes": item.notes,
                    "tag": item.tag,
                    "added_price": fmt.fmt_price(item.added_price),
                    "current_price": fmt.fmt_price(current_price),
                    "gain_loss_pct": fmt.fmt_pct(gain_loss_pct) if gain_loss_pct is not None else None,
                    "gain_loss_positive": (gain_loss_pct or 0) >= 0,
                    "day_change_pct": fmt.fmt_pct((cache_row.change_pct / 100) if cache_row and cache_row.change_pct is not None else None),
                })

        return render_template("watchlist.html", watchlists=watchlists, selected=selected, items=items_view)

    @app.route("/watchlist/create", methods=["POST"])
    @login_required
    def watchlist_create():
        name = request.form.get("name", "")
        wl, error = watchlist_service.create_watchlist(db, Watchlist, current_user.id, name)
        if error:
            flash(error, "error")
        else:
            flash(f"Created watchlist '{wl.name}'.", "success")
        return redirect(url_for("watchlist_page", id=wl.id if wl else None))

    @app.route("/watchlist/<int:watchlist_id>/add", methods=["POST"])
    @login_required
    def watchlist_add_stock(watchlist_id):
        wl = Watchlist.query.filter_by(id=watchlist_id, user_id=current_user.id).first()
        if wl is None:
            flash("Watchlist not found.", "error")
            return redirect(url_for("watchlist_page"))

        symbol = normalize_symbol(request.form.get("symbol", ""))
        tag = request.form.get("tag") or None
        notes = request.form.get("notes") or None

        added_price = None
        try:
            provider = get_provider()
            s = provider.get_stock(symbol)
            added_price = s.price
        except Exception:
            pass  # if live price fails, still allow adding without a baseline price

        item, error = watchlist_service.add_stock_to_watchlist(db, WatchlistStock, wl.id, symbol, notes, tag, added_price)
        if error:
            flash(error, "error")
        else:
            flash(f"Added {symbol} to {wl.name}.", "success")
        return redirect(url_for("watchlist_page", id=wl.id))

    @app.route("/watchlist/<int:watchlist_id>/remove/<symbol>", methods=["POST"])
    @login_required
    def watchlist_remove_stock(watchlist_id, symbol):
        wl = Watchlist.query.filter_by(id=watchlist_id, user_id=current_user.id).first()
        if wl is None:
            flash("Watchlist not found.", "error")
            return redirect(url_for("watchlist_page"))
        watchlist_service.remove_stock_from_watchlist(db, WatchlistStock, wl.id, symbol)
        flash(f"Removed {symbol}.", "success")
        return redirect(url_for("watchlist_page", id=wl.id))

    @app.route("/watchlist/<int:watchlist_id>/delete", methods=["POST"])
    @login_required
    def watchlist_delete(watchlist_id):
        watchlist_service.delete_watchlist(db, Watchlist, current_user.id, watchlist_id)
        flash("Watchlist deleted.", "success")
        return redirect(url_for("watchlist_page"))

    # ============================================================
    # SCREENER
    # ============================================================
    @app.route("/screens")
    def screens_index():
        screens = [{"key": k, **v} for k, v in PREBUILT_SCREENS.items()]
        last_refresh = db.session.query(db.func.max(StockMetricsCache.last_refreshed)).scalar()
        cached_count = StockMetricsCache.query.filter_by(refresh_failed=False).count()
        total_universe = len(get_universe())
        return render_template(
            "screens.html", screens=screens, last_refresh=last_refresh,
            cached_count=cached_count, total_universe=total_universe,
        )

    @app.route("/screens/run/<screen_key>")
    def run_screen_route(screen_key):
        matched, meta = run_prebuilt_screen(StockMetricsCache, screen_key)
        if meta is None:
            return render_template("screen_results.html", error="Unknown screen.", results=[], meta=None)

        sort_by = request.args.get("sort", "vinstock_score")
        descending = request.args.get("dir", "desc") == "desc"
        matched.sort(key=lambda r: (getattr(r, sort_by, None) is None, getattr(r, sort_by, None)), reverse=descending)

        results = [_row_to_view(r) for r in matched]
        return render_template("screen_results.html", error=None, results=results, meta=meta, screen_key=screen_key, sort_by=sort_by)

    @app.route("/screens/custom", methods=["GET", "POST"])
    def custom_screener():
        results = []
        conditions = []
        if request.method == "POST":
            metrics = request.form.getlist("metric")
            operators = request.form.getlist("operator")
            values = request.form.getlist("value")
            for m, op, v in zip(metrics, operators, values):
                if not m or not op or v == "":
                    continue
                try:
                    val = float(v)
                except ValueError:
                    continue
                conditions.append({"metric": m, "operator": op, "value": val})

            if conditions:
                matched = run_screen(StockMetricsCache, conditions)
                results = [_row_to_view(r) for r in matched]

        return render_template(
            "custom_screener.html", metrics=FILTERABLE_METRICS, results=results,
            conditions=conditions, result_count=len(results),
        )

    @app.route("/screens/save", methods=["POST"])
    @login_required
    def save_screen():
        name = request.form.get("name", "Custom Screen")
        filter_json = request.form.get("filter_json", "[]")
        screen = SavedScreen(user_id=current_user.id, name=name, filter_json=filter_json)
        db.session.add(screen)
        db.session.commit()
        flash(f"Saved screen '{name}'.", "success")
        return redirect(url_for("custom_screener"))

    @app.route("/screens/export/<screen_key>.csv")
    def export_screen_csv(screen_key):
        matched, meta = run_prebuilt_screen(StockMetricsCache, screen_key)
        if meta is None:
            return "Unknown screen", 404
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Symbol", "Name", "Sector", "CMP", "Market Cap", "PE", "PB", "ROE", "ROCE",
                          "Debt/Equity", "Revenue Growth", "Profit Growth", "Dividend Yield", "VinStock Score"])
        for r in matched:
            writer.writerow([
                r.symbol, r.name, r.sector, r.price, r.market_cap, r.pe_ratio, r.pb_ratio,
                r.roe, r.roce, r.debt_to_equity, r.revenue_growth, r.earnings_growth,
                r.dividend_yield, r.vinstock_score,
            ])
        return Response(
            output.getvalue(), mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={screen_key}.csv"},
        )

    # ============================================================
    # ADMIN: trigger a data refresh (manual button, stand-in for a scheduler)
    # ============================================================
    @app.route("/admin/refresh", methods=["GET", "POST"])
    def admin_refresh():
        if request.method == "POST":
            limit = request.form.get("limit", type=int)
            summary = run_refresh_all(db, StockMetricsCache, limit=limit, throttle_seconds=0.2)
            flash(f"Refreshed {summary['succeeded']}/{summary['total']} stocks ({summary['failed']} failed).", "success")
            return redirect(url_for("admin_refresh"))
        cached_count = StockMetricsCache.query.count()
        failed_count = StockMetricsCache.query.filter_by(refresh_failed=True).count()
        return render_template("admin_refresh.html", cached_count=cached_count, failed_count=failed_count,
                                total_universe=len(get_universe()))

    @app.route("/admin/refresh-one/<symbol>", methods=["POST"])
    def admin_refresh_one(symbol):
        ok, err = run_refresh_one(symbol, db, StockMetricsCache)
        return jsonify({"success": ok, "error": err})

    # ============================================================
    # STOCK DETAIL PAGE (Phase 1 — unchanged logic from before)
    # ============================================================
    @app.route("/stock/<symbol>")
    def stock(symbol):
        symbol = normalize_symbol(symbol)
        provider = get_provider()

        try:
            s = provider.get_stock(symbol)
        except Exception as e:
            return render_template("stock.html", view=None, error=str(e), symbol=symbol)

        interest_coverage = None
        asset_turnover = None
        if s.revenue_annual and s.total_assets_annual:
            try:
                asset_turnover = calc.asset_turnover(s.revenue_annual.values[-1], s.total_assets_annual.values[-1])
            except IndexError:
                pass

        fcf_growth = None
        if s.free_cf_annual and len(s.free_cf_annual.values) >= 2:
            fcf_growth = calc.pct_change(s.free_cf_annual.values[-1], s.free_cf_annual.values[-2])

        book_value_growth = None
        if s.equity_annual and len(s.equity_annual.values) >= 2:
            book_value_growth = calc.pct_change(s.equity_annual.values[-1], s.equity_annual.values[-2])

        eps_growth = None
        if s.eps_annual and len(s.eps_annual.values) >= 2:
            eps_growth = calc.pct_change(s.eps_annual.values[-1], s.eps_annual.values[-2])

        score = compute_vinstock_score({
            "pe": s.pe_ratio, "pb": s.pb_ratio, "peg": s.peg_ratio, "ev_ebitda": s.ev_to_ebitda,
            "revenue_growth": s.revenue_growth, "earnings_growth": s.earnings_growth, "eps_growth": eps_growth,
            "roe": s.roe, "roce": s.roce, "net_margin": s.net_margin,
            "debt_to_equity": s.debt_to_equity, "current_ratio": s.current_ratio,
            "interest_coverage": interest_coverage,
        })

        qoq_revenue_growth = yoy_revenue_growth = None
        if s.revenue_quarterly and len(s.revenue_quarterly.values) >= 2:
            qoq_revenue_growth = calc.pct_change(s.revenue_quarterly.values[-1], s.revenue_quarterly.values[-2])
        if s.revenue_quarterly and len(s.revenue_quarterly.values) >= 5:
            yoy_revenue_growth = calc.pct_change(s.revenue_quarterly.values[-1], s.revenue_quarterly.values[-5])

        qoq_profit_growth = yoy_profit_growth = None
        if s.net_profit_quarterly and len(s.net_profit_quarterly.values) >= 2:
            qoq_profit_growth = calc.pct_change(s.net_profit_quarterly.values[-1], s.net_profit_quarterly.values[-2])
        if s.net_profit_quarterly and len(s.net_profit_quarterly.values) >= 5:
            yoy_profit_growth = calc.pct_change(s.net_profit_quarterly.values[-1], s.net_profit_quarterly.values[-5])

        peer_symbols = provider.get_peers(symbol) if hasattr(provider, "get_peers") else []
        peers = []
        for psym in peer_symbols[:4]:
            try:
                p = provider.get_stock(psym)
                peers.append({
                    "symbol": psym, "name": p.name or NAME_LOOKUP.get(psym, psym),
                    "market_cap": fmt.fmt_crore(p.market_cap), "pe": fmt.fmt_ratio(p.pe_ratio),
                    "roe": fmt.fmt_pct(p.roe), "roce": fmt.fmt_pct(p.roce),
                    "revenue": fmt.fmt_crore(p.revenue_annual.values[-1] if p.revenue_annual and p.revenue_annual.values else None),
                    "net_profit": fmt.fmt_crore(p.net_profit_annual.values[-1] if p.net_profit_annual and p.net_profit_annual.values else None),
                    "debt_to_equity": fmt.fmt_ratio(p.debt_to_equity),
                })
            except Exception:
                continue

        in_watchlist = False
        if current_user.is_authenticated:
            in_watchlist = WatchlistStock.query.join(Watchlist).filter(
                Watchlist.user_id == current_user.id, WatchlistStock.symbol == symbol
            ).first() is not None

        view = {
            "symbol": s.symbol, "name": s.name, "sector": s.sector or "—", "industry": s.industry or "—",
            "description": s.description or "No description available.",
            "price": fmt.fmt_price(s.price), "change": s.change, "change_pct": s.change_pct,
            "high_52w": fmt.fmt_price(s.high_52w), "low_52w": fmt.fmt_price(s.low_52w), "beta": fmt.fmt_ratio(s.beta),
            "market_cap": fmt.fmt_crore(s.market_cap), "enterprise_value": fmt.fmt_crore(s.enterprise_value),
            "pe_ratio": fmt.fmt_ratio(s.pe_ratio), "forward_pe": fmt.fmt_ratio(s.forward_pe),
            "pb_ratio": fmt.fmt_ratio(s.pb_ratio), "peg_ratio": fmt.fmt_ratio(s.peg_ratio),
            "ev_to_ebitda": fmt.fmt_ratio(s.ev_to_ebitda), "ev_to_revenue": fmt.fmt_ratio(s.ev_to_revenue),
            "price_to_sales": fmt.fmt_ratio(s.price_to_sales), "eps": fmt.fmt_price(s.eps),
            "book_value": fmt.fmt_price(s.book_value), "face_value": fmt.fmt_price(s.face_value),
            "shares_outstanding": fmt.fmt_number(s.shares_outstanding), "dividend_yield": fmt.fmt_pct(s.dividend_yield),
            "dividend_payout_ratio": fmt.fmt_pct(s.dividend_payout_ratio),
            "roe": fmt.fmt_pct(s.roe), "roa": fmt.fmt_pct(s.roa), "roce": fmt.fmt_pct(s.roce),
            "gross_margin": fmt.fmt_pct(s.gross_margin), "operating_margin": fmt.fmt_pct(s.operating_margin),
            "net_margin": fmt.fmt_pct(s.net_margin),
            "debt_to_equity": fmt.fmt_ratio(s.debt_to_equity), "current_ratio": fmt.fmt_ratio(s.current_ratio),
            "quick_ratio": None, "interest_coverage": None, "cash_per_share": fmt.fmt_price(s.cash_per_share),
            "asset_turnover": fmt.fmt_ratio(asset_turnover),
            "revenue_growth": fmt.fmt_pct(s.revenue_growth), "earnings_growth": fmt.fmt_pct(s.earnings_growth),
            "eps_growth": fmt.fmt_pct(eps_growth), "book_value_growth": fmt.fmt_pct(book_value_growth),
            "fcf_growth": fmt.fmt_pct(fcf_growth),
            "price_chart_labels": s.price_chart_labels, "price_chart_values": s.price_chart_values,
            "revenue_annual": _series_or_none(s.revenue_annual), "operating_profit_annual": _series_or_none(s.operating_profit_annual),
            "net_profit_annual": _series_or_none(s.net_profit_annual), "eps_annual": _series_or_none(s.eps_annual),
            "free_cf_annual": _series_or_none(s.free_cf_annual), "debt_trend": _series_or_none(s.debt_trend),
            "roe_trend": _series_or_none(s.roe_trend), "roce_trend": _series_or_none(s.roce_trend),
            "revenue_quarterly": _series_or_none(s.revenue_quarterly), "net_profit_quarterly": _series_or_none(s.net_profit_quarterly),
            "eps_quarterly": _series_or_none(s.eps_quarterly),
            "qoq_revenue_growth": fmt.fmt_pct(qoq_revenue_growth), "yoy_revenue_growth": fmt.fmt_pct(yoy_revenue_growth),
            "qoq_profit_growth": fmt.fmt_pct(qoq_profit_growth), "yoy_profit_growth": fmt.fmt_pct(yoy_profit_growth),
            "peers": peers, "score": score, "data_source": s.source, "warnings": s.warnings,
            "in_watchlist": in_watchlist,
        }
        return render_template("stock.html", view=view, error=None, symbol=symbol)

    @app.route("/stock/<symbol>/quick-add", methods=["POST"])
    @login_required
    def quick_add_to_watchlist(symbol):
        symbol = normalize_symbol(symbol)
        wl = watchlist_service.get_or_create_default_watchlist(db, Watchlist, current_user.id)
        try:
            provider = get_provider()
            s = provider.get_stock(symbol)
            price = s.price
        except Exception:
            price = None
        watchlist_service.add_stock_to_watchlist(db, WatchlistStock, wl.id, symbol, added_price=price)
        flash(f"Added {symbol} to your watchlist.", "success")
        return redirect(url_for("stock", symbol=symbol))


def _row_to_view(r):
    return {
        "symbol": r.symbol, "name": r.name or NAME_LOOKUP.get(r.symbol, r.symbol), "sector": r.sector or "—",
        "price": fmt.fmt_price(r.price), "market_cap": fmt.fmt_crore(r.market_cap),
        "pe_ratio": fmt.fmt_ratio(r.pe_ratio), "pb_ratio": fmt.fmt_ratio(r.pb_ratio),
        "roe": fmt.fmt_pct(r.roe), "roce": fmt.fmt_pct(r.roce), "debt_to_equity": fmt.fmt_ratio(r.debt_to_equity),
        "revenue_growth": fmt.fmt_pct(r.revenue_growth), "earnings_growth": fmt.fmt_pct(r.earnings_growth),
        "dividend_yield": fmt.fmt_pct(r.dividend_yield), "high_52w": fmt.fmt_price(r.high_52w),
        "low_52w": fmt.fmt_price(r.low_52w), "vinstock_score": r.vinstock_score, "vinstock_rating": r.vinstock_rating,
    }


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
