"""
Кастомные теги для работы с переводами и форматированием
"""
from django import template
from django.utils.translation import get_language, activate, gettext_lazy as _

register = template.Library()


@register.simple_tag(takes_context=True)
def get_current_language(context):
    """Возвращает текущий язык"""
    return get_language()


@register.simple_tag
def get_available_languages():
    """Возвращает список доступных языков"""
    from django.conf import settings
    return settings.LANGUAGES


@register.filter
def format_price(value):
    """
    Форматирует число с пробелами для разделения тысяч
    Например: 1000000 -> "1 000 000"
    """
    if value is None:
        return "0"
    try:
        # Преобразуем в целое число
        num = int(float(value))
        # Форматируем с пробелами
        return f"{num:,}".replace(",", " ")
    except (ValueError, TypeError):
        return str(value)


@register.simple_tag(takes_context=True)
def price_with_currency(context, value):
    """Цена с валютой из StoreConfig текущего сайта."""
    amount = format_price(value)
    currency = context.get('currency') or 'сум'
    return f"{amount} {currency}"


@register.filter
def yandex_map_url(value):
    """
    Преобразует URL Яндекс карты в формат для iframe
    Например: https://yandex.uz/maps/-/CLhZvD6F -> https://yandex.uz/map-widget/v1/-/CLhZvD6F
    """
    if not value:
        return ""
    return value.replace('/maps/-/', '/map-widget/v1/-/')
