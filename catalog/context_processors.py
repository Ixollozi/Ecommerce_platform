"""
Context processors для передачи конфигурации в шаблоны
"""
from .config_loader import get_config
from .models import Partner, Feature, Cart


def store_config(request):
    """
    Передает конфигурацию магазина во все шаблоны
    """
    config = get_config()
    # Получаем партнеров из БД вместо конфига
    partners = Partner.objects.filter(is_active=True).order_by('order', 'name')
    # Получаем features из БД вместо конфига
    features = Feature.objects.filter(is_active=True).order_by('order', 'title')
    
    # Cart badge count (header)
    cart_items_count = 0
    try:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key).first()
        if cart:
            cart_items_count = cart.items_count
    except Exception:
        cart_items_count = 0

    store = config.get('store') or config.get('catalog') or {}
    return {
        'store_config': config,
        'store_name': store.get('name') or 'Fashion Store',
        'store_title': store.get('title') or store.get('name') or 'Fashion Store',
        'store_description': store.get('description', ''),
        'currency': store.get('currency', 'сум') or 'сум',
        'contact_info': config.get('contact', {}),
        'social_links': config.get('social', {}),
        'partners': partners,  # Теперь из БД
        'features': features,  # Теперь из БД
        'about_info': config.get('about', {}),
        'hero_config': config.get('hero', {}),
        'seo_config': config.get('seo', {}),
        'theme_config': config.get('theme', {}),
        'cart_items_count': cart_items_count,
        'current_site': getattr(request, 'site', None),
    }

