"""formatters.py — turn raw normalized numbers into display strings.
Kept separate from the data layer so providers stay unit-agnostic."""


def fmt_crore(n):
    """Format a raw INR number into Indian Cr/L Cr units."""
    if n is None:
        return None
    try:
        n = float(n)
    except (TypeError, ValueError):
        return None
    crore = n / 1e7
    if abs(crore) >= 100000:
        return f"₹{crore / 100000:.2f} L Cr"
    return f"₹{crore:,.0f} Cr"


def fmt_price(n):
    if n is None:
        return None
    try:
        return f"₹{float(n):,.2f}"
    except (TypeError, ValueError):
        return None


def fmt_pct(n, decimals=2):
    """n is expected as a fraction (0.12 = 12%)."""
    if n is None:
        return None
    try:
        return f"{float(n) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return None


def fmt_ratio(n, decimals=2):
    if n is None:
        return None
    try:
        return f"{float(n):.{decimals}f}"
    except (TypeError, ValueError):
        return None


def fmt_number(n):
    if n is None:
        return None
    try:
        n = float(n)
        if abs(n) >= 1e9:
            return f"{n/1e9:.2f}B"
        if abs(n) >= 1e7:
            return f"{n/1e7:.2f} Cr"
        if abs(n) >= 1e5:
            return f"{n/1e5:.2f} L"
        return f"{n:,.0f}"
    except (TypeError, ValueError):
        return None


def or_dash(value, formatter=None):
    """Render '—' for None, else apply formatter (or str)."""
    if value is None:
        return "—"
    return formatter(value) if formatter else str(value)
