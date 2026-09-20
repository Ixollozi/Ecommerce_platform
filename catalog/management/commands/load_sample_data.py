from django.core.management.base import BaseCommand

from catalog.models import (
    AboutConfig,
    AboutStat,
    Category,
    ContactConfig,
    ContactMessage,
    FAQ,
    Feature,
    HeroConfig,
    Order,
    OrderItem,
    Partner,
    Product,
    ProductFeatureConfig,
    SocialConfig,
)


class Command(BaseCommand):
    help = 'Загружает примерные данные в базу'

    def handle(self, *args, **options):
        categories_data = [
            {
                'name': 'Мужская одежда',
                'slug': 'mens-clothing',
                'image_url': 'https://images.unsplash.com/photo-1441984904996-e0b69264a3d9?w=600',
            },
            {
                'name': 'Женская одежда',
                'slug': 'womens-clothing',
                'image_url': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600',
            },
            {
                'name': 'Детская одежда',
                'slug': 'kids-clothing',
                'image_url': 'https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=600',
            },
            {
                'name': 'Аксессуары',
                'slug': 'accessories',
                'image_url': 'https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=600',
            },
            {
                'name': 'Дом и уют',
                'slug': 'home-hygge',
                'image_url': 'https://images.unsplash.com/photo-1616046229478-9901c5536a45?w=600',
            },
            {
                'name': 'Блокноты',
                'slug': 'notebooks',
                'image_url': 'https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=600',
            },
            {
                'name': 'Бутылки',
                'slug': 'reusable-bottles',
                'image_url': 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600',
            },
            {
                'name': 'Свечи',
                'slug': 'candles',
                'image_url': 'https://images.unsplash.com/photo-1603006905003-be475563bc59?w=600',
            },
            {
                'name': 'Техника',
                'slug': 'tech-refined',
                'image_url': 'https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=600',
            },
            {
                'name': 'Телефоны',
                'slug': 'phones',
                'image_url': 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600',
            },
            {
                'name': 'Часы',
                'slug': 'watches',
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600',
            },
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'image_url': cat_data.get('image_url', ''),
                },
            )
            if not created and not category.image_url and cat_data.get('image_url'):
                category.image_url = cat_data['image_url']
                category.save(update_fields=['image_url'])
            categories[cat_data['slug']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Категория: {category.name}'))

        products_data = [
            {
                'name': 'Классическая футболка',
                'slug': 'classic-t-shirt',
                'description': 'Классическая футболка из хлопка. Мягкая ткань, свободный крой.',
                'price': 189000,
                'old_price': 220000,
                'category': 'mens-clothing',
                'image_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600',
                'available_sizes': 'S, M, L, XL',
                'available_colors': 'Черный, Белый, Синий',
                'stock': 50,
            },
            {
                'name': 'Джинсы классические',
                'slug': 'classic-jeans',
                'description': 'Классические джинсы из денима средней плотности.',
                'price': 349000,
                'old_price': None,
                'category': 'mens-clothing',
                'image_url': 'https://images.unsplash.com/photo-1542272604-787c3835535d?w=600',
                'available_sizes': 'M, L, XL',
                'available_colors': 'Синий, Черный',
                'stock': 30,
            },
            {
                'name': 'Элегантное платье',
                'slug': 'elegant-dress',
                'description': 'Платье для особых случаев. Лёгкая ткань, аккуратный крой.',
                'price': 459000,
                'old_price': None,
                'category': 'womens-clothing',
                'image_url': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600',
                'available_sizes': 'S, M, L',
                'available_colors': 'Черный, Красный',
                'stock': 25,
            },
            {
                'name': 'Демисезонная куртка',
                'slug': 'demiseason-jacket',
                'description': 'Куртка для прохладной погоды. Утеплённая подкладка.',
                'price': 620000,
                'old_price': 690000,
                'category': 'mens-clothing',
                'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600',
                'available_sizes': 'M, L, XL',
                'available_colors': 'Черный, Серый',
                'stock': 20,
            },
            {
                'name': 'Рубашка офисная',
                'slug': 'office-shirt',
                'description': 'Офисная рубашка из хлопка. Идеально под пиджак.',
                'price': 245000,
                'old_price': None,
                'category': 'mens-clothing',
                'image_url': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600',
                'available_sizes': 'S, M, L',
                'available_colors': 'Белый, Голубой',
                'stock': 40,
            },
            {
                'name': 'Свитшот уютный',
                'slug': 'cozy-sweatshirt',
                'description': 'Мягкий свитшот из футера. На каждый день.',
                'price': 275000,
                'old_price': None,
                'category': 'mens-clothing',
                'image_url': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=600',
                'available_sizes': 'M, L, XL',
                'available_colors': 'Серый, Черный',
                'stock': 35,
            },
            {
                'name': 'Керамическая ваза',
                'slug': 'ceramic-vase',
                'description': 'Ручная керамика. Спокойный оттенок для домашнего интерьера.',
                'price': 185000,
                'old_price': None,
                'category': 'home-hygge',
                'image_url': 'https://images.unsplash.com/photo-1578508973413-b4492c1a4a6a?w=600',
                'available_sizes': '',
                'available_colors': 'Бежевый, Белый',
                'stock': 18,
            },
            {
                'name': 'Льняной блокнот',
                'slug': 'linen-notebook',
                'description': 'Блокнот в твёрдой обложке. 120 страниц без линовки.',
                'price': 89000,
                'old_price': 110000,
                'category': 'notebooks',
                'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600',
                'available_sizes': '',
                'available_colors': 'Коричневый, Серый',
                'stock': 60,
            },
            {
                'name': 'Бутылка для воды',
                'slug': 'steel-bottle',
                'description': 'Термобутылка 500 мл. Держит температуру до 12 часов.',
                'price': 165000,
                'old_price': None,
                'category': 'reusable-bottles',
                'image_url': 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600',
                'available_sizes': '500ml',
                'available_colors': 'Черный, Зеленый',
                'stock': 42,
            },
            {
                'name': 'Ароматическая свеча',
                'slug': 'scented-candle',
                'description': 'Соевая свеча с деревянным фитилём. Аромат древесины и цитруса.',
                'price': 125000,
                'old_price': None,
                'category': 'candles',
                'image_url': 'https://images.unsplash.com/photo-1603006905003-be475563bc59?w=600',
                'available_sizes': '',
                'available_colors': 'Бежевый',
                'stock': 28,
            },
            {
                'name': 'Беспроводные наушники',
                'slug': 'wireless-earbuds',
                'description': 'Компактные наушники с шумоподавлением и кейсом.',
                'price': 890000,
                'old_price': 990000,
                'category': 'tech-refined',
                'image_url': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600',
                'available_sizes': '',
                'available_colors': 'Белый, Черный',
                'stock': 15,
            },
            {
                'name': 'Минималистичные часы',
                'slug': 'minimal-watch',
                'description': 'Кварцевые часы с кожаным ремешком. Диаметр 40 мм.',
                'price': 520000,
                'old_price': None,
                'category': 'watches',
                'image_url': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600',
                'available_sizes': '',
                'available_colors': 'Черный, Коричневый',
                'stock': 22,
            },
        ]

        products = []
        for product_data in products_data:
            category = categories[product_data.pop('category')]
            image_url = product_data.pop('image_url', '')
            product, created = Product.objects.get_or_create(
                slug=product_data['slug'],
                defaults={
                    **product_data,
                    'category': category,
                    'rating': 4.5,
                    'reviews_count': 12,
                    'image_url': image_url,
                    'is_active': True,
                },
            )
            if not created and product.price < 1000:
                product.price = product_data['price']
                product.old_price = product_data.get('old_price')
                product.save(update_fields=['price', 'old_price'])
            products.append(product)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Товар: {product.name}'))

        for feature_data in [
            {
                'icon': 'fas fa-shipping-fast',
                'title': 'Быстрая доставка',
                'description': '2–5 дней по Узбекистану',
                'order': 0,
            },
            {
                'icon': 'fas fa-undo',
                'title': 'Лёгкий возврат',
                'description': '14 дней без лишних вопросов',
                'order': 1,
            },
            {
                'icon': 'fas fa-shield-alt',
                'title': 'Гарантия качества',
                'description': 'Проверенные бренды и материалы',
                'order': 2,
            },
            {
                'icon': 'fas fa-headset',
                'title': 'Поддержка',
                'description': 'Ответим в течение дня',
                'order': 3,
            },
        ]:
            Feature.objects.get_or_create(
                title=feature_data['title'],
                defaults={**feature_data, 'is_active': True},
            )

        if not ProductFeatureConfig.objects.exists():
            ProductFeatureConfig.objects.create(
                title='Бесплатная доставка',
                icon='fas fa-shipping-fast',
                text='От 300 000 сум',
                order=1,
                is_active=True,
            )
            ProductFeatureConfig.objects.create(
                title='Оригинал',
                icon='fas fa-check-circle',
                text='Гарантия подлинности',
                order=2,
                is_active=True,
            )

        HeroConfig.objects.get_or_create(
            is_active=True,
            defaults={
                'title': 'Objects with quiet intent.',
                'subtitle': 'A calm edit of electronics, home, and everyday pieces.',
                'button_text': 'Shop the edit',
                'background_image_url': 'https://images.unsplash.com/photo-1616046229478-9901c5536a45?w=1600',
            },
        )

        about, about_created = AboutConfig.objects.get_or_create(
            is_active=True,
            defaults={
                'title': 'About Apex Goods',
                'description': (
                    'We curate electronics, home objects, and everyday essentials '
                    'with quiet intent — quality over noise, form with purpose.'
                ),
                'mission': (
                    'Make thoughtful goods accessible: durable materials, fair prices, '
                    'and a calm shopping experience.'
                ),
                'vision': (
                    'Become the go-to edit for modern living across Uzbekistan — '
                    'from home rituals to refined tech.'
                ),
                'values': 'Quality\nHonesty\nCustomer Care\nInnovation',
                'image_url': 'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=1200',
            },
        )
        if about_created:
            self.stdout.write(self.style.SUCCESS('AboutConfig создан'))

        for i, (value, label) in enumerate([
            ('10+', 'Years of care'),
            ('5k+', 'Happy customers'),
            ('24/7', 'Online catalog'),
            ('14', 'Day returns'),
        ]):
            AboutStat.objects.get_or_create(
                value=value,
                label=label,
                defaults={'order': i, 'is_active': True},
            )

        ContactConfig.objects.get_or_create(
            is_active=True,
            defaults={
                'phone': '+998(90) 333-33-33',
                'email': 'info@demo-eshop.localhost',
                'address_city': 'Tashkent',
                'address_street': '',
                'address_full': 'Tashkent',
                'working_hours_weekdays': 'Mon–Sun: 9:00 – 21:00',
                'working_hours_weekend': 'Mon–Sun: 9:00 – 21:00',
            },
        )

        SocialConfig.objects.get_or_create(
            is_active=True,
            defaults={
                'instagram': 'https://instagram.com/',
                'facebook': 'https://facebook.com/',
                'twitter': 'https://x.com/',
                'telegram': 'https://t.me/',
                'vk': '',
                'whatsapp': '',
            },
        )

        for p in [
            {'name': 'Click', 'icon': 'fas fa-credit-card', 'order': 0},
            {'name': 'Payme', 'icon': 'fas fa-wallet', 'order': 1},
            {'name': 'UzPost', 'icon': 'fas fa-truck', 'order': 2},
        ]:
            Partner.objects.get_or_create(name=p['name'], defaults={**p, 'is_active': True})

        for i, (q, a) in enumerate([
            ('Как оформить заказ?', 'Добавьте товары в корзину и оформите заказ на странице корзины.'),
            ('Сроки доставки?', 'Ташкент 1–2 дня, регионы 2–5 дней.'),
            ('Можно вернуть товар?', 'Да, в течение 14 дней при сохранении товарного вида.'),
            ('Какие способы оплаты?', 'Карта онлайн, наличные курьеру, электронные кошельки.'),
        ]):
            FAQ.objects.get_or_create(
                question=q,
                defaults={'answer': a, 'order': i, 'is_active': True},
            )

        if not ContactMessage.objects.exists():
            ContactMessage.objects.create(
                name='Дилшод',
                email='dilshod@example.com',
                phone='+998901112233',
                subject='delivery',
                message='Есть доставка в Самарканд?',
                is_read=False,
            )
            ContactMessage.objects.create(
                name='Малика',
                email='malika@example.com',
                phone='+998907778899',
                subject='product',
                message='Платье есть в размере S?',
                is_read=False,
            )
            self.stdout.write(self.style.SUCCESS('Сообщения созданы'))

        if not Order.objects.exists() and len(products) >= 6:
            demos = [
                ('Алишер', 'Каримов', 'pending', 'card', [(0, 2, 'M', 'Черный')]),
                ('Нигора', 'Рахимова', 'processing', 'cash', [(2, 1, 'S', 'Черный')]),
                ('Жавлон', 'Усманов', 'delivered', 'wallet', [(1, 1, 'L', 'Синий'), (4, 1, 'M', 'Белый')]),
                ('Сара', 'Исмоилова', 'cancelled', 'card', [(5, 1, 'L', 'Серый')]),
            ]
            for first, last, status, pay, items in demos:
                lines = []
                total = 0
                for idx, qty, size, color in items:
                    product = products[idx]
                    lines.append((product, qty, size, color))
                    total += product.price * qty
                order = Order.objects.create(
                    session_key='demo-seed',
                    first_name=first,
                    last_name=last,
                    email=f'{first.lower()}@example.com',
                    phone='+998901234567',
                    address='ул. Навои, 12',
                    city='Ташкент',
                    total=total,
                    status=status,
                    payment_method=pay,
                )
                for product, qty, size, color in lines:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        price=product.price,
                        size=size,
                        color=color,
                    )
                self.stdout.write(self.style.SUCCESS(f'Заказ #{order.id} ({status})'))

        self.stdout.write(self.style.SUCCESS('Тестовые данные готовы.'))
