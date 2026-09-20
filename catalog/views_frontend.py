from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import Product, Category, Cart, CartItem


def get_dummy_products():
    """Возвращает заглушки товаров"""
    factor = 10000
    return [
        {
            'name': 'Classic T-shirt',
            'slug': 'dummy-tshirt',
            'price': 20 * factor,
            'old_price': None,
            'image_url': '',
            'image': None,
        },
        {
            'name': 'Classic Jeans',
            'slug': 'dummy-jeans',
            'price': 35 * factor,
            'old_price': None,
            'image_url': '',
            'image': None,
        },
        {
            'name': 'Elegant Dress',
            'slug': 'dummy-dress',
            'price': 50 * factor,
            'old_price': None,
            'image_url': '',
            'image': None,
        },
        {
            'name': 'Demiseason Jacket',
            'slug': 'dummy-jacket',
            'price': 60 * factor,
            'old_price': None,
            'image_url': '',
            'image': None,
        },
        {
            'name': 'Office Shirt',
            'slug': 'dummy-shirt',
            'price': 25 * factor,
            'old_price': None,
            'image_url': '',
            'image': None,
        },
        {
            'name': 'Cozy Sweatshirt',
            'slug': 'dummy-sweatshirt',
            'price': 40 * factor,
            'old_price': None,
            'image_url': '',
            'image': None,
        },
        {
            'name': 'Midi Skirt',
            'slug': 'dummy-skirt',
            'price': 28 * factor,
            'old_price': None,
            'image_url': '',
            'image': None,
        },
        {
            'name': 'Classic Pants',
            'slug': 'dummy-pants',
            'price': 33 * factor,
            'old_price': None,
            'image_url': '',
            'image': None,
        },
    ]


def get_dummy_categories():
    """Возвращает заглушки категорий"""
    from django.templatetags.static import static

    return [
        {
            'name': "Men's Clothing",
            'slug': 'mens-clothing',
            'image_url': static('img/gallery-1.jpg'),
            'image': None,
        },
        {
            'name': "Women's Clothing",
            'slug': 'womens-clothing',
            'image_url': static('img/gallery-2.jpg'),
            'image': None,
        },
        {
            'name': "Kids' Clothing",
            'slug': 'kids-clothing',
            'image_url': static('img/gallery-3.jpg'),
            'image': None,
        },
        {
            'name': 'Accessories',
            'slug': 'accessories',
            'image_url': static('img/gallery-4.jpg'),
            'image': None,
        },
        {
            'name': 'Home Hygge',
            'slug': 'home-hygge',
            'image_url': static('img/organic-row3-l.jpg'),
            'image': None,
        },
        {
            'name': 'Notebooks',
            'slug': 'notebooks',
            'image_url': static('img/organic-row3-m.jpg'),
            'image': None,
        },
        {
            'name': 'Reusable Bottles',
            'slug': 'reusable-bottles',
            'image_url': static('img/organic-row3-r.jpg'),
            'image': None,
        },
        {
            'name': 'Candles',
            'slug': 'candles',
            'image_url': static('img/gallery-1.jpg'),
            'image': None,
        },
        {
            'name': 'Tech Refined',
            'slug': 'tech-refined',
            'image_url': static('img/organic-tech-tl.jpg'),
            'image': None,
        },
        {
            'name': 'Phones',
            'slug': 'phones',
            'image_url': static('img/organic-tech-tr.jpg'),
            'image': None,
        },
        {
            'name': 'Watches',
            'slug': 'watches',
            'image_url': static('img/organic-tech-br.jpg'),
            'image': None,
        },
    ]


def index(request):
    """Главная страница"""
    from .models import HeroConfig
    from .organic_bento import MAX_CATEGORIES, build_organic_boards

    categories = list(Category.objects.all().order_by('name')[:MAX_CATEGORIES])
    if not categories:
        categories = get_dummy_categories()

    organic_boards = build_organic_boards(categories)
    hero_config_obj = HeroConfig.objects.filter(is_active=True).first()
    featured_products = list(
        Product.objects.filter(is_active=True)
        .exclude(category__slug='demo')
        .select_related('category')
        .prefetch_related('images')
        .order_by('-rating', '-created_at')[:8]
    )

    # Prefer a balanced trio for the homepage mosaic (home / apparel / accessories)
    by_slug = {
        getattr(c, 'slug', None) or (c.get('slug') if isinstance(c, dict) else None): c
        for c in categories
    }
    preferred = [
        ('home-hygge', 'candles', 'reusable-bottles'),
        ('mens-clothing', 'womens-clothing', 'kids-clothing'),
        ('accessories', 'phones', 'tech-refined'),
    ]
    home_tiles = []
    used = set()
    for group in preferred:
        picked = None
        for slug in group:
            if slug in by_slug and slug not in used:
                picked = by_slug[slug]
                used.add(slug)
                break
        if picked is None:
            for c in categories:
                slug = getattr(c, 'slug', None) or (c.get('slug') if isinstance(c, dict) else None)
                if slug and slug not in used:
                    picked = c
                    used.add(slug)
                    break
        if picked is not None:
            home_tiles.append(picked)

    context = {
        'categories': categories,
        'home_tiles': home_tiles,
        'organic_boards': organic_boards,
        'hero_config_obj': hero_config_obj,
        'featured_products': featured_products,
        # Alias: several themes loop `{% for product in products %}` on the homepage
        'products': featured_products,
    }
    return render(request, 'index.html', context)


def catalog(request):
    """Страница каталога"""
    # Получаем товары из БД
    products_queryset = (
        Product.objects.filter(is_active=True)
        .exclude(category__slug='demo')
        .select_related('category')
        .prefetch_related('images')
    )
    has_real_products = Product.objects.filter(is_active=True).exclude(category__slug='demo').exists()
    
    # Фильтрация по категории
    category_slug = request.GET.get('category', None)
    if category_slug:
        products_queryset = products_queryset.filter(category__slug=category_slug)
    
    # Фильтрация по цене
    min_price = request.GET.get('min_price', None)
    max_price = request.GET.get('max_price', None)
    if min_price:
        try:
            products_queryset = products_queryset.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            products_queryset = products_queryset.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass
    
    # Поиск
    search_query = request.GET.get('search', None)
    if search_query:
        products_queryset = products_queryset.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )
    
    # Фильтрация по цвету
    color_filter = request.GET.get('color', None)
    if color_filter:
        from .color_utils import resolve_single_color
        resolved = resolve_single_color(color_filter)
        color_query = resolved.get('name') or color_filter
        # Ищем товары, у которых в available_colors есть указанный цвет
        products_queryset = products_queryset.filter(
            Q(available_colors__icontains=color_query) | Q(available_colors__icontains=color_filter)
        )
    
    # Сортировка
    sort_by = request.GET.get('sort', 'newest')
    
    # Применяем сортировку для реальных товаров из БД
    if sort_by == 'popularity':
        # По популярности: сначала по рейтингу, потом по количеству отзывов, потом по дате создания
        products_queryset = products_queryset.order_by('-rating', '-reviews_count', '-created_at')
    elif sort_by == 'price_low':
        # По цене: от низкой к высокой
        products_queryset = products_queryset.order_by('price', '-created_at')
    elif sort_by == 'price_high':
        # По цене: от высокой к низкой
        products_queryset = products_queryset.order_by('-price', '-created_at')
    elif sort_by == 'newest':
        # По новизне: сначала новые
        products_queryset = products_queryset.order_by('-created_at')
    else:
        # По умолчанию: по новизне
        products_queryset = products_queryset.order_by('-created_at')
    
    # Создаем пагинатор
    paginator = Paginator(products_queryset, 12)  # 12 товаров на страницу
    
    page = request.GET.get('page', 1)
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    # Получаем категории из БД
    categories = list(Category.objects.all().order_by('name'))
    if not categories:
        categories = get_dummy_categories()

    dummy_products = get_dummy_products() if not has_real_products else []
    
    context = {
        'products': products_page,
        'dummy_products': dummy_products,
        'categories': categories,
        'current_category': category_slug,
        'current_sort': sort_by,
        'current_search': search_query,
        'min_price': min_price,
        'max_price': max_price,
        'current_color': color_filter,
    }
    return render(request, 'catalog.html', context)


def product_detail(request, slug=None):
    """Страница товара"""
    product = None
    related_products = []
    
    # Сначала пытаемся найти товар в БД
    if slug:
        try:
            product = Product.objects.prefetch_related('images').get(slug=slug, is_active=True)
            
            # Получаем связанные товары из той же категории
            if product.category:
                related_products = list(
                    Product.objects.filter(
                        category=product.category,
                        is_active=True,
                    )
                    .exclude(id=product.id)
                    .prefetch_related('images')[:4]
                )
            else:
                # Если нет категории, берем любые активные товары
                related_products = list(
                    Product.objects.filter(is_active=True)
                    .exclude(id=product.id)
                    .prefetch_related('images')[:4]
                )
        except Product.DoesNotExist:
            pass
    
    # Если товар не найден в БД, ищем в заглушках по slug
    if not product:
        dummy_products = get_dummy_products()
        if slug:
            # Ищем заглушку по slug
            dummy_product_data = next((p for p in dummy_products if p.get('slug') == slug), None)
        else:
            # Берем первую заглушку
            dummy_product_data = dummy_products[0] if dummy_products else None
        
        if dummy_product_data:
            # Создаем объект-заглушку с нужными атрибутами
            class DummyProduct:
                def __init__(self, data):
                    self.id = None  # Нет ID для заглушек
                    self.name = data.get('name', '')
                    self.slug = data.get('slug', '')
                    self.price = data.get('price', 0)
                    self.old_price = data.get('old_price')
                    self.description = 'Classic product description. This is a high-quality product with excellent materials and craftsmanship.'
                    self.image_url = data.get('image_url') or ''
                    self.image = None
                    self.available_sizes = ''
                    self.available_colors = 'Черный, Белый, Синий, Красный'
                    self.stock = 10
                    self.rating = 4.0
                    self.reviews_count = 12
                    self.category = None
                    self.images = []
            
            product = DummyProduct(dummy_product_data)
            
            # Для связанных товаров берем другие заглушки
            related_products_data = [p for p in dummy_products if p.get('slug') != product.slug][:4]
            related_products = []
            for data in related_products_data:
                related_products.append(DummyProduct(data))
    
    # Вычисляем скидку, если есть старая цена
    discount = None
    if product and hasattr(product, 'old_price') and product.old_price:
        discount = int(((product.old_price - product.price) / product.old_price) * 100)
    
    # Парсим доступные цвета с интеллектуальным маппингом и дедупликацией
    from .color_utils import parse_product_colors
    colors = parse_product_colors(getattr(product, 'available_colors', None)) if product else []
    
    # Получаем features товара из базы данных
    from .models import ProductFeatureConfig
    product_features = ProductFeatureConfig.objects.filter(is_active=True).order_by('order', 'title')

    # Приводим изображения к единому виду (iterable list) для шаблона:
    # у реального Product это RelatedManager, у DummyProduct — обычный list.
    product_images = []
    if product is not None and hasattr(product, "images"):
        images_attr = getattr(product, "images")
        if hasattr(images_attr, "all"):
            try:
                product_images = list(images_attr.all())
            except Exception:
                product_images = []
        else:
            try:
                product_images = list(images_attr)
            except Exception:
                product_images = []

    # Unified gallery URLs: primary + spare ProductImage photos (deduped).
    from .media_urls import product_gallery_urls

    gallery_images = product_gallery_urls(product) if product is not None else []
    
    context = {
        'product': product,
        'related_products': related_products,
        'discount': discount,
        'colors': colors,
        'product_images': product_images,
        'gallery_images': gallery_images,
        'product_features': product_features,
    }
    return render(request, 'product.html', context)


def cart(request):
    """Страница корзины"""
    # Получаем или создаем корзину для текущей сессии
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    cart, created = Cart.objects.get_or_create(session_key=session_key)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product').prefetch_related('product__images')
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'cart.html', context)


def about(request):
    """Страница о нас"""
    from .models import AboutConfig, AboutStat
    about_config = AboutConfig.objects.filter(is_active=True).first()
    about_stats = list(AboutStat.objects.filter(is_active=True).order_by('order', 'created_at')[:6])
    about_values = about_config.get_values_list() if about_config else []
    context = {
        'about_config': about_config,
        'about_stats': about_stats,
        'about_values': about_values,
    }
    return render(request, 'about.html', context)


def contact(request):
    """Страница контактов"""
    return render(request, 'contact.html')


def delivery(request):
    """Страница доставки"""
    return render(request, 'delivery.html')


def faq(request):
    """Страница часто задаваемых вопросов"""
    from .models import FAQ
    faqs = FAQ.objects.filter(is_active=True).order_by('order', 'created_at')
    context = {
        'faqs': faqs,
    }
    return render(request, 'faq.html', context)


