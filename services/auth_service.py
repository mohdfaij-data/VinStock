"""
auth_service.py — registration/login helper functions, kept separate from
Flask routes so the logic is testable without spinning up a request context.
"""


def register_user(db, User, UserPreference, Watchlist, email, name, password):
    """
    Create a new user with a default watchlist and preferences row.
    Returns (user, error). error is a user-facing string if something's wrong,
    in which case user is None.
    """
    email = email.strip().lower()
    if not email or "@" not in email:
        return None, "Please enter a valid email address."
    if not name or not name.strip():
        return None, "Please enter your name."
    if not password or len(password) < 6:
        return None, "Password must be at least 6 characters."

    existing = User.query.filter_by(email=email).first()
    if existing:
        return None, "An account with this email already exists."

    user = User(email=email, name=name.strip())
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # get user.id before creating dependent rows

    default_watchlist = Watchlist(user_id=user.id, name="My Watchlist")
    db.session.add(default_watchlist)
    db.session.flush()

    prefs = UserPreference(user_id=user.id, default_watchlist_id=default_watchlist.id)
    db.session.add(prefs)

    db.session.commit()
    return user, None


def authenticate_user(User, email, password):
    """Returns (user, error). user is None and error is set on failure."""
    email = (email or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password or ""):
        return None, "Invalid email or password."
    return user, None
