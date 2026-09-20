"""Константы витрины (без импорта моделей, чтобы не было циклов)."""

# Старые демо-товары из первой версии load_sample_data — не показываем в каталоге и bootstrap
LEGACY_PLACEHOLDER_PRODUCT_SLUGS: frozenset[str] = frozenset(
    {
        "classic-t-shirt",
        "classic-jeans",
        "elegant-dress",
        "demiseason-jacket",
        "office-shirt",
        "cozy-sweatshirt",
        "midi-skirt",
        "classic-pants",
    }
)
