"""
watchlist_service.py — watchlist CRUD logic, kept separate from Flask routes.
"""


def get_or_create_default_watchlist(db, Watchlist, user_id):
    wl = Watchlist.query.filter_by(user_id=user_id).order_by(Watchlist.id.asc()).first()
    if wl is None:
        wl = Watchlist(user_id=user_id, name="My Watchlist")
        db.session.add(wl)
        db.session.commit()
    return wl


def create_watchlist(db, Watchlist, user_id, name):
    name = (name or "").strip() or "Untitled Watchlist"
    existing = Watchlist.query.filter_by(user_id=user_id, name=name).first()
    if existing:
        return None, "You already have a watchlist with this name."
    wl = Watchlist(user_id=user_id, name=name)
    db.session.add(wl)
    db.session.commit()
    return wl, None


def add_stock_to_watchlist(db, WatchlistStock, watchlist_id, symbol, notes=None, tag=None, added_price=None):
    symbol = symbol.upper().strip()
    existing = WatchlistStock.query.filter_by(watchlist_id=watchlist_id, symbol=symbol).first()
    if existing:
        return None, "This stock is already in the watchlist."
    item = WatchlistStock(
        watchlist_id=watchlist_id, symbol=symbol,
        notes=notes, tag=tag, added_price=added_price,
    )
    db.session.add(item)
    db.session.commit()
    return item, None


def remove_stock_from_watchlist(db, WatchlistStock, watchlist_id, symbol):
    symbol = symbol.upper().strip()
    item = WatchlistStock.query.filter_by(watchlist_id=watchlist_id, symbol=symbol).first()
    if item is None:
        return False
    db.session.delete(item)
    db.session.commit()
    return True


def update_watchlist_item(db, WatchlistStock, watchlist_id, symbol, notes=None, tag=None):
    symbol = symbol.upper().strip()
    item = WatchlistStock.query.filter_by(watchlist_id=watchlist_id, symbol=symbol).first()
    if item is None:
        return None, "Stock not found in this watchlist."
    if notes is not None:
        item.notes = notes
    if tag is not None:
        item.tag = tag
    db.session.commit()
    return item, None


def delete_watchlist(db, Watchlist, user_id, watchlist_id):
    wl = Watchlist.query.filter_by(id=watchlist_id, user_id=user_id).first()
    if wl is None:
        return False
    db.session.delete(wl)
    db.session.commit()
    return True
