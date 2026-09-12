"""
Команда наполнения сайта bahromusta тестовыми данными (металлические изделия, ножи, ковка).
"""
import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from store.models import (
    Category, Product, ProductImage, StoreConfig, HeroConfig,
    ContactConfig, AboutConfig, AboutStat, Feature
)


class Command(BaseCommand):
    help = 'Загружает реалистичные тестовые данные для сайта Bahromusta (тема hero: металл, ножи, ковка)'

    def handle(self, *args, **options):
        self.stdout.write('Загрузка тестовых данных для Bahromusta...')

        # 1. Настройка магазина StoreConfig
        store_cfg, _ = StoreConfig.objects.get_or_create(id=1)
        store_cfg.name = 'Bahromusta'
        store_cfg.title = 'Bahromusta — Авторские металлические изделия и ручная ковка'
        store_cfg.description = 'Мастерская ручной ковки мастера Бахромбека Худоймуродова (Шерабад, Сурхандарья). Традиционные ножи, мангалы, интерьерная ковка.'
        store_cfg.currency = 'сум'
        store_cfg.is_active = True
        store_cfg.save()

        # 2. HeroConfig (Главный баннер в теме hero)
        hero_cfg, _ = HeroConfig.objects.get_or_create(id=1)
        hero_cfg.title = 'Металл и пламя ручной ковки'
        hero_cfg.subtitle = 'Традиционные узбекские клинки, очаги и интерьерная ковка от мастера Бахромбека'
        hero_cfg.button_text = 'Смотреть изделия'
        hero_cfg.button_url = '/catalog/'
        hero_cfg.is_active = True
        hero_cfg.save()

        # 3. Контакты
        contact_cfg, _ = ContactConfig.objects.get_or_create(id=1)
        contact_cfg.phone = '+998(77) 058-98-10'
        contact_cfg.email = 'info@bahromusta.uz'
        contact_cfg.address_city = 'Сурхандарьинская область, Шерабадский район'
        contact_cfg.address_full = 'Сурхандарьинская область, Шерабадский район, с/с UZUNSOY'
        contact_cfg.working_hours_weekdays = '9:00 - 20:00'
        contact_cfg.working_hours_weekend = '10:00 - 18:00'
        contact_cfg.is_active = True
        contact_cfg.save()

        # 4. О мастере AboutConfig
        about_cfg, _ = AboutConfig.objects.get_or_create(id=1)
        about_cfg.title = 'О мастере'
        about_cfg.description = (
            'Xudoymurodov Baxrombek Baxtiyor O\'g\'li — потомственный мастер по металлу, '
            'член ассоциации «Хунарманд». В своей мастерской в Шерабаде он создает прочные, '
            'долговечные и эстетичные изделия из кованой стали, меди и латуни: от традиционных '
            'узбекских ножей (пичок) и мангалов до изящных предметов интерьера.'
        )
        about_cfg.mission = 'Создавать надежные, функциональные и долговечные изделия из металла ручной ковки по честной цене.'
        about_cfg.vision = 'Сохранять вековые традиции кузнечного ремесла Сурхандарьи, объединяя их с современными стандартами прочности и эстетики.'
        about_cfg.values = (
            'Только качественная кованая сталь и проверенные сплавы.\n'
            'Ручная термообработка, закалка и тщательная подгонка деталей.\n'
            'Уникальный авторский орнамент и долговечность на десятилетия.\n'
            'Индивидуальный подход к каждому заказу и честная гарантия.'
        )
        about_cfg.is_active = True
        about_cfg.save()

        # 5. Статистика мастера
        AboutStat.objects.all().delete()
        stats_data = [
            ('15+', 'Лет кузнечного опыта', 1),
            ('2 500+', 'Созданных изделий', 2),
            ('100%', 'Ручная горячая ковка', 3),
            ('10 лет', 'Гарантия на клинки', 4),
        ]
        for val, lbl, order in stats_data:
            AboutStat.objects.create(value=val, label=lbl, order=order, is_active=True)

        # 6. Преимущества Feature
        Feature.objects.all().delete()
        features_data = [
            ('fa-hammer', 'Ручная ковка', 'Каждое изделие отковано вручную на наковальне с соблюдением технологии термообработки.', 1),
            ('fa-shield-halved', 'Сталь высокой прочности', 'Используем инструментальную сталь ШХ15, 65Г и нержавеющие сплавы повышенной твердости.', 2),
            ('fa-truck-fast', 'Доставка по всему Узбекистану', 'Бережно упаковываем и оперативно доставляем изделия в любой город и регион.', 3),
            ('fa-certificate', 'Сертификат «Хунарманд»', 'Официальный член Ассоциации народных мастеров Узбекистана «Хунарманд».', 4),
        ]
        for icon, title, desc, order in features_data:
            Feature.objects.create(icon=icon, title=title, description=desc, order=order, is_active=True)

        # 7. Категории
        categories = {
            'knives': ('Традиционные ножи (Пичок)', 'nozhi-pichok', 'Аутентичные узбекские ножи ручной ковки из кованой стали с рукоятями из ценных пород дерева.'),
            'bbq': ('Мангалы и очаги', 'mangaly-i-ochagi', 'Толстостенные кованые мангалы, грили и подставки под казан.'),
            'decor': ('Кованый интерьер и декор', 'kovanyj-interer-i-dekor', 'Подсвечники, дровницы, панно и светильники ручной работы.'),
            'tools': ('Утварь и аксессуары', 'utvar-i-aksessuary', 'Кованые шампуры, щипцы, кочерги и походная утварь.'),
        }

        cat_objs = {}
        for key, (name, slug, desc) in categories.items():
            cat, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'description': desc}
            )
            cat.name = name
            cat.description = desc
            cat.save()
            cat_objs[key] = cat

        # 8. Товары с красивыми цветами и описаниями
        products_data = [
            {
                'name': 'Нож «Шерабад» ручной ковки (Пичок)',
                'slug': 'nozh-sherabad-ruchnoj-kovki',
                'category': cat_objs['knives'],
                'price': 480000,
                'old_price': 550000,
                'available_colors': 'Стальной, Черненый металл, Бронза',
                'description': 'Традиционный узбекский клинок ручной ковки из высокоуглеродистой стали ШХ15. Рукоять выполнена из древесины грецкого ореха с латунной инкрустацией и чеканным узором мастера. Идеальный бритвенный рез и исключительная долговечность.',
                'stock': 8,
                'rating': 5.0,
                'reviews_count': 18,
                'is_active': True,
                'image_url': 'https://images.unsplash.com/photo-1593618998160-e34014e67546?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Мангал кованый «Сурхан» с восточной вязью',
                'slug': 'mangal-kovanyj-surhan',
                'category': cat_objs['bbq'],
                'price': 1850000,
                'old_price': 2200000,
                'available_colors': 'Черненый металл, Графит',
                'description': 'Мощный авторский мангал из горячекатаной стали толщиной 4 мм. Украшен декоративной ручной ковкой и термостойкой патиной до 900°C. В комплекте удобные боковые полки и съемное кольцо под казан.',
                'stock': 4,
                'rating': 4.9,
                'reviews_count': 12,
                'is_active': True,
                'image_url': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Кованый настольный канделябр «Бухара»',
                'slug': 'kovanyj-kandelyabr-buhara',
                'category': cat_objs['decor'],
                'price': 320000,
                'old_price': 380000,
                'available_colors': 'Бронза, Черненый металл, Золотой',
                'description': 'Элегантный трехрожковый подсвечник ручной ковки в восточном стиле. Создает атмосферу благородного уюта и традиционного тепла. Покрыт матовым защитным воском.',
                'stock': 12,
                'rating': 4.8,
                'reviews_count': 9,
                'is_active': True,
                'image_url': 'https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Набор шампуров кованых «Бахром» (6 шт.)',
                'slug': 'nabor-shampurov-kovanyh-bahrom',
                'category': cat_objs['tools'],
                'price': 390000,
                'old_price': 460000,
                'available_colors': 'Стальной, Черненый',
                'description': 'Надежные толстостенные шампуры (3 мм) из нержавеющей стали с витыми коваными рукоятями в форме восточного узора. Идеально лежат в руке и не прогибаются под тяжестью мяса.',
                'stock': 15,
                'rating': 5.0,
                'reviews_count': 24,
                'is_active': True,
                'image_url': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Кованая дровница «Очаг» с каминным набором',
                'slug': 'kovanaya-drovnitsa-ochag',
                'category': cat_objs['decor'],
                'price': 680000,
                'old_price': None,
                'available_colors': 'Черный, Графит, Медный',
                'description': 'Компактная интерьерная подставка для дров с сопутствующими инструментами (кочерга, совок, щипцы). Прочная сварная и клепаная конструкция с витыми коваными элементами.',
                'stock': 5,
                'rating': 4.9,
                'reviews_count': 7,
                'is_active': True,
                'image_url': 'https://images.unsplash.com/photo-1543083477-4f785aeafaa9?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Сундук деревянный с кованой оковкой «Хунарманд»',
                'slug': 'sunduk-derevyannyj-s-kovanoj-okovkoj',
                'category': cat_objs['decor'],
                'price': 2600000,
                'old_price': 3100000,
                'available_colors': 'Коричневый, Медный, Черненый',
                'description': 'Массивный сундук из дерева карагач, окованный узорными стальными полосами ручной чеканки. Оснащен аутентичным кованым замком и боковыми ручками для переноски.',
                'stock': 2,
                'rating': 5.0,
                'reviews_count': 5,
                'is_active': True,
                'image_url': 'https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Казан чугунный 12л с кованой треногой',
                'slug': 'kazan-chugunnyj-s-kovanoj-trenogoj',
                'category': cat_objs['tools'],
                'price': 790000,
                'old_price': 890000,
                'available_colors': 'Черненый металл, Черный',
                'description': 'Наманганский шлифованный чугунный казан на 12 литров в комплекте с прочной кованой полевой подставкой (таганком). Незаменим для плова на открытом огне.',
                'stock': 9,
                'rating': 5.0,
                'reviews_count': 32,
                'is_active': True,
                'image_url': 'https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?auto=format&fit=crop&w=800&q=80',
            },
            {
                'name': 'Панно настенное кованое «Гирих»',
                'slug': 'panno-nastennoe-kovanoe-girih',
                'category': cat_objs['decor'],
                'price': 520000,
                'old_price': 600000,
                'available_colors': 'Черненый металл, Бронза, Золотой',
                'description': 'Настенное металлическое панно с традиционным геометрическим восточным орнаментом (гирих), выкованное вручную на наковальне.',
                'stock': 7,
                'rating': 4.8,
                'reviews_count': 6,
                'is_active': True,
                'image_url': 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=800&q=80',
            },
        ]

        for p_data in products_data:
            slug = p_data.pop('slug')
            prod, _ = Product.objects.update_or_create(
                slug=slug,
                defaults=p_data
            )
            self.stdout.write(f'  [OK] Товар: {prod.slug}')

        # 9. Загрузка нескольких реальных фотографий для галереи товаров
        from store.platform.context import get_current_site
        import urllib.request

        current_site = get_current_site()
        media_products_dir = (current_site.media_dir / 'products') if current_site else (Path(settings.BASE_DIR) / 'media' / 'products')
        media_products_dir.mkdir(parents=True, exist_ok=True)

        gallery_downloads = {
            'nozh_1_main.jpg': 'https://images.unsplash.com/photo-1593618998160-e34014e67546?auto=format&fit=crop&w=900&q=80',
            'nozh_2_blade.jpg': 'https://images.unsplash.com/photo-1589256469067-ea99122bbdc4?auto=format&fit=crop&w=900&q=80',
            'nozh_3_handle.jpg': 'https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?auto=format&fit=crop&w=900&q=80',
            'nozh_4_sheath.jpg': 'https://images.unsplash.com/photo-1530595467537-0b5996c41f2d?auto=format&fit=crop&w=900&q=80',
            'mangal_1_main.jpg': 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=900&q=80',
            'mangal_2_fire.jpg': 'https://images.unsplash.com/photo-1527661591475-527312dd65f5?auto=format&fit=crop&w=900&q=80',
            'mangal_3_detail.jpg': 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=900&q=80',
            'drovnitsa_1_main.jpg': 'https://images.unsplash.com/photo-1543083477-4f785aeafaa9?auto=format&fit=crop&w=900&q=80',
            'drovnitsa_2_coals.jpg': 'https://images.unsplash.com/photo-1517457373958-b7bdd4587205?auto=format&fit=crop&w=900&q=80',
        }

        headers = {'User-Agent': 'Mozilla/5.0'}
        for fname, url in gallery_downloads.items():
            dest = media_products_dir / fname
            if not dest.exists() or dest.stat().st_size == 0:
                try:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as resp, open(dest, 'wb') as f:
                        f.write(resp.read())
                    self.stdout.write(f'  [IMG] Загружен: {fname}')
                except Exception as e:
                    self.stdout.write(f'  [WARN] Ошибка загрузки {fname}: {e}')

        # Привязываем галерею к ножу «Шерабад» (4 уникальных ракурса)
        knife_prod = Product.objects.filter(slug='nozh-sherabad-ruchnoj-kovki').first()
        if knife_prod:
            knife_prod.image = 'products/nozh_1_main.jpg'
            knife_prod.save(update_fields=['image'])
            knife_prod.images.all().delete()
            for extra_img in ['products/nozh_2_blade.jpg', 'products/nozh_3_handle.jpg', 'products/nozh_4_sheath.jpg']:
                if (media_products_dir / Path(extra_img).name).exists():
                    ProductImage.objects.create(product=knife_prod, image=extra_img)
            self.stdout.write(f'  [GALLERY] Нож «Шерабад»: установлено 4 уникальных фото')

        # Привязываем галерею к мангалу «Сурхан» (3 уникальных ракурса)
        mangal_prod = Product.objects.filter(slug='mangal-kovanyj-surhan').first()
        if mangal_prod:
            mangal_prod.image = 'products/mangal_1_main.jpg'
            mangal_prod.save(update_fields=['image'])
            mangal_prod.images.all().delete()
            for extra_img in ['products/mangal_2_fire.jpg', 'products/mangal_3_detail.jpg']:
                if (media_products_dir / Path(extra_img).name).exists():
                    ProductImage.objects.create(product=mangal_prod, image=extra_img)
            self.stdout.write(f'  [GALLERY] Мангал «Сурхан»: установлено 3 уникальных фото')

        # Привязываем галерею к дровнице «Очаг» (2 уникальных фото)
        drovnitsa_prod = Product.objects.filter(slug='kovanaya-drovnitsa-ochag').first()
        if drovnitsa_prod:
            drovnitsa_prod.image = 'products/drovnitsa_1_main.jpg'
            drovnitsa_prod.save(update_fields=['image'])
            drovnitsa_prod.images.all().delete()
            if (media_products_dir / 'drovnitsa_2_coals.jpg').exists():
                ProductImage.objects.create(product=drovnitsa_prod, image='products/drovnitsa_2_coals.jpg')
            self.stdout.write(f'  [GALLERY] Дровница «Очаг»: установлено 2 уникальных фото')

        self.stdout.write(self.style.SUCCESS('Тестовые данные для Bahromusta успешно загружены!'))
