"""JSON для витрины React (script#django-bootstrap) из моделей и API-сериализаторов."""
from __future__ import annotations

from decimal import Decimal

from datetime import date, datetime

from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.translation import gettext as _

from .models import (
    AboutConfig,
    AboutStat,
    Cart,
    ContactConfig,
    FAQ,
    Feature,
    HeroConfig,
    Partner,
    Product,
    ProductFeatureConfig,
    SocialConfig,
    StoreConfig,
)
from .constants import LEGACY_PLACEHOLDER_PRODUCT_SLUGS
from .serializers import CartSerializer, ProductSerializer
from .spa_ui_strings import get_faq_static_groups, get_spa_ui_strings


def _media_url(request, file_field) -> str:
    if not file_field:
        return ""
    try:
        return request.build_absolute_uri(file_field.url)
    except Exception:
        return ""


def _decimal_to_json(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _decimal_to_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_json(v) for v in obj]
    return obj


def _site_payload(request) -> dict:
    store = StoreConfig.objects.filter(is_active=True).first()
    store_payload = {
        "name": store.name if store else _("Магазин"),
        "title": store.title if store else "",
        "description": store.description if store else "",
        "currency": (store.currency if store else None) or "сум",
        "logoUrl": _media_url(request, store.logo) if store else "",
        "faviconUrl": _media_url(request, store.favicon) if store else "",
    }

    hero = HeroConfig.objects.filter(is_active=True).first()
    hero_bg = ""
    if hero:
        if hero.background_image:
            hero_bg = _media_url(request, hero.background_image)
        elif hero.background_image_url:
            hero_bg = (hero.background_image_url or "").strip()
    hero_payload = None
    if hero:
        hero_payload = {
            "title": hero.title or "",
            "subtitle": hero.subtitle or "",
            "buttonText": hero.button_text or "",
            "backgroundImageUrl": hero_bg,
        }

    about = AboutConfig.objects.filter(is_active=True).first()
    about_img = ""
    if about:
        if about.image:
            about_img = _media_url(request, about.image)
        elif about.image_url:
            about_img = (about.image_url or "").strip()
    about_payload = None
    if about:
        about_payload = {
            "title": about.title or "",
            "description": about.description or "",
            "mission": about.mission or "",
            "vision": about.vision or "",
            "values": about.get_values_list(),
            "imageUrl": about_img,
        }

    about_stats = [
        {"value": s.value, "label": s.label}
        for s in AboutStat.objects.filter(is_active=True).order_by("order", "created_at")
    ]

    features = [
        {"icon": f.icon, "title": f.title, "description": f.description}
        for f in Feature.objects.filter(is_active=True).order_by("order", "title")
    ]

    contact = ContactConfig.objects.filter(is_active=True).first()
    contact_payload = None
    if contact:
        contact_payload = {
            "phone": contact.phone or "",
            "email": contact.email or "",
            "addressFull": contact.address_full or "",
            "addressCity": contact.address_city or "",
            "addressStreet": contact.address_street or "",
            "mapUrl": (contact.map_url or "").strip(),
            "weekdays": contact.working_hours_weekdays or "",
            "weekend": contact.working_hours_weekend or "",
        }

    social = SocialConfig.objects.filter(is_active=True).first()
    social_payload = None
    if social:
        social_payload = {
            "instagram": (social.instagram or "").strip(),
            "facebook": (social.facebook or "").strip(),
            "twitter": (social.twitter or "").strip(),
            "vk": (social.vk or "").strip(),
            "telegram": (social.telegram or "").strip(),
            "whatsapp": (social.whatsapp or "").strip(),
        }

    partners = [
        {
            "name": p.name,
            "icon": p.icon or "",
            "url": (p.url or "").strip() if p.url else "",
            "logoUrl": _media_url(request, p.logo) if p.logo else "",
            "description": p.description or "",
        }
        for p in Partner.objects.filter(is_active=True).order_by("order", "name")
    ]

    faqs = [
        {"question": f.question, "answer": f.answer}
        for f in FAQ.objects.filter(is_active=True).order_by("order", "created_at")
    ]

    product_features = [
        {"title": x.title, "text": x.text, "icon": x.icon}
        for x in ProductFeatureConfig.objects.filter(is_active=True).order_by("order", "title")
    ]

    return {
        "store": store_payload,
        "hero": hero_payload,
        "about": about_payload,
        "aboutStats": about_stats,
        "features": features,
        "contact": contact_payload,
        "social": social_payload,
        "partners": partners,
        "faqs": faqs,
        "productFeatures": product_features,
    }


def _bootstrap_product_row(d: dict) -> dict:
    cat = d.get("category") or {}
    cat_name = cat.get("name", "") if isinstance(cat, dict) else ""
    # Prefer serializer image_display (file > URL > gallery), then raw fields.
    img = d.get("image_display") or d.get("image") or d.get("image_url") or ""
    if isinstance(img, dict):
        img = img.get("url") or ""
    price = d.get("price")
    try:
        price_f = float(price) if price is not None else 0.0
    except (TypeError, ValueError):
        price_f = 0.0
    stock = d.get("stock") or 0
    try:
        stock_i = int(stock)
    except (TypeError, ValueError):
        stock_i = 0
    rating_f = float(d.get("rating") or 0)
    reviews_i = int(d.get("reviews_count") or 0)

    # Extra photos for product detail gallery (SPA may use if supported).
    gallery = []
    seen = set()
    if img:
        gallery.append(img)
        seen.add(img)
    for item in d.get("images") or []:
        if not isinstance(item, dict):
            continue
        url = item.get("image") or ""
        if url and url not in seen:
            seen.add(url)
            gallery.append(url)
    # If primary empty but gallery has files — use first gallery as card image.
    if not img and gallery:
        img = gallery[0]

    return {
        "id": d["id"],
        "slug": d.get("slug") or "",
        "name": d.get("name") or "",
        "price": price_f,
        "image": img or "",
        "images": gallery,
        "description": d.get("description") or "",
        "category": cat_name,
        "material": "",
        "dimensions": "",
        "inStock": stock_i > 0,
        "isNew": False,
        "isBestseller": False,
        "rating": rating_f,
        "reviewsCount": reviews_i,
    }


def _apply_product_flags(products: list[dict]) -> None:
    """Главная: блоки «новинки» / «хиты» по дате и рейтингу (полей в модели пока нет)."""
    for i, p in enumerate(products):
        p["isNew"] = i < 4
    best = sorted(
        products,
        key=lambda x: (-float(x.get("rating") or 0), -int(x.get("reviewsCount") or 0), -int(x["id"])),
    )[:4]
    best_ids = {x["id"] for x in best}
    for p in products:
        p["isBestseller"] = p["id"] in best_ids


def build_spa_bootstrap(request) -> dict:
    limit = int(getattr(settings, "SPA_BOOTSTRAP_PRODUCT_LIMIT", 500))
    qs = (
        Product.objects.filter(is_active=True)
        .exclude(slug__in=LEGACY_PLACEHOLDER_PRODUCT_SLUGS)
        .select_related("category")
        .prefetch_related("images")
        .order_by("-created_at")[:limit]
    )
    ser = ProductSerializer(qs, many=True, context={"request": request})
    products = [_bootstrap_product_row(row) for row in ser.data]
    _apply_product_flags(products)

    names = sorted({p["category"] for p in products if p.get("category")})
    category_names = [_("Все")] + names

    if not request.session.session_key:
        request.session.create()
    cart = Cart.objects.filter(session_key=request.session.session_key).first()
    initial_cart = None
    if cart:
        initial_cart = _decimal_to_json(CartSerializer(cart, context={"request": request}).data)

    site = _site_payload(request)

    ui_strings = get_spa_ui_strings()
    store_payload = site.get("store") or {}
    store_name = (store_payload.get("name") or "").strip()
    store_currency = (store_payload.get("currency") or "").strip() or "сум"
    ui_strings["currencySuffix"] = store_currency
    if store_name:
        ui_strings["aboutHeroTitleFallback"] = _("О %(name)s") % {"name": store_name}
    else:
        ui_strings["aboutHeroTitleFallback"] = ui_strings.get("aboutSplitFallbackTitle", _("О мастерской"))

    payload = {
        "csrfToken": get_token(request),
        "apiBase": "/api",
        "priceUzsMultiplier": int(getattr(settings, "SPA_PRICE_UZS_MULTIPLIER", 10000)),
        "products": products,
        "categoryNames": category_names,
        "initialCart": initial_cart,
        "languageCode": getattr(request, "LANGUAGE_CODE", None) or settings.LANGUAGE_CODE,
        "languages": [
            {"code": code, "label": str(label)}
            for code, label in settings.LANGUAGES
        ],
        "ui": ui_strings,
        "faqStaticGroups": get_faq_static_groups(),
        **site,
    }
    return _decimal_to_json(payload)
