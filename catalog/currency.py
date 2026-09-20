"""Store currency helpers (per-site StoreConfig)."""

from functools import lru_cache


def get_store_currency() -> str:
    """Currency label from the active StoreConfig for the current DB."""
    from .models import StoreConfig

    store = StoreConfig.objects.filter(is_active=True).first()
    if store is None:
        store = StoreConfig.objects.first()
    return (getattr(store, 'currency', None) if store else None) or 'сум'


def format_money(amount) -> str:
    """Format amount with thousands spaces and store currency."""
    try:
        num = f"{int(float(amount)):,.0f}".replace(',', ' ')
    except (TypeError, ValueError):
        num = str(amount)
    return f"{num} {get_store_currency()}"
