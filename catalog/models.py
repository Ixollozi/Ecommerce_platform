from django.db import models
from django.contrib.auth.models import User
import json
import logging

logger = logging.getLogger(__name__)


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='URL')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Изображение')
    image_url = models.URLField(blank=True, null=True, verbose_name='URL изображения')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_display_image_url(self):
        from .media_urls import category_display_image_url
        return category_display_image_url(self)


class Product(models.Model):
    SIZE_CHOICES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]

    COLOR_CHOICES = [
        ('black', 'Черный'),
        ('white', 'Белый'),
        ('blue', 'Синий'),
        ('red', 'Красный'),
        ('green', 'Зеленый'),
        ('yellow', 'Желтый'),
        ('gray', 'Серый'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='URL')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Старая цена')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Категория')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Основное изображение')
    image_url = models.URLField(blank=True, null=True, verbose_name='URL изображения')
    available_sizes = models.CharField(
        max_length=200, 
        verbose_name='Доступные размеры',
        help_text='Доступные размеры: XS, S, M, L, XL, XXL. Указывайте через запятую, например: "S, M, L, XL"',
        blank=True,
        default=''
    )
    available_colors = models.CharField(
        max_length=200, 
        verbose_name='Доступные цвета',
        help_text='Доступные цвета: Черный, Белый, Синий, Красный, Зеленый, Желтый, Серый. Указывайте через запятую, например: "Черный, Белый, Синий"'
    )
    stock = models.PositiveIntegerField(default=0, verbose_name='Остаток')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name='Рейтинг')
    reviews_count = models.PositiveIntegerField(default=0, verbose_name='Количество отзывов')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_product'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_display_image_url(self):
        from .media_urls import product_display_image_url
        return product_display_image_url(self)

    def get_gallery_urls(self):
        from .media_urls import product_gallery_urls
        return product_gallery_urls(self)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Товар')
    image = models.ImageField(upload_to='products/', verbose_name='Изображение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        db_table = 'store_productimage'
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'

    def __str__(self):
        return f"{self.product.name} - изображение"


class Cart(models.Model):
    session_key = models.CharField(max_length=40, unique=True, verbose_name='Ключ сессии')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_cart'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f"Корзина {self.session_key}"

    @property
    def total(self):
        return sum(item.total for item in self.items.all())

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='Корзина')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    size = models.CharField(max_length=10, blank=True, verbose_name='Размер')
    color = models.CharField(max_length=50, blank=True, verbose_name='Цвет')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_cartitem'
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        unique_together = ['cart', 'product', 'size', 'color']

    def __str__(self):
        return f"{self.product.name} - {self.quantity} шт."

    @property
    def total(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает обработки'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    PAYMENT_CHOICES = [
        ('card', 'Банковская карта'),
        ('cash', 'Наличными'),
        ('wallet', 'Электронный кошелек'),
        ('bank', 'Банковский перевод'),
    ]

    session_key = models.CharField(max_length=40, verbose_name='Ключ сессии')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    address = models.TextField(verbose_name='Адрес доставки')
    city = models.CharField(max_length=100, default='Ташкент', verbose_name='Город')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='Почтовый индекс')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Итого')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, verbose_name='Способ оплаты')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_order'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} - {self.first_name} {self.last_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    size = models.CharField(max_length=10, blank=True, verbose_name='Размер')
    color = models.CharField(max_length=50, blank=True, verbose_name='Цвет')

    class Meta:
        db_table = 'store_orderitem'
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f"{self.product.name} - {self.quantity} шт."

    @property
    def total(self):
        if self.price is None or self.quantity is None:
            return 0
        return self.price * self.quantity


class Partner(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    icon = models.CharField(max_length=100, default='fas fa-star', verbose_name='Иконка (Font Awesome класс)')
    url = models.URLField(blank=True, null=True, verbose_name='Ссылка на сайт')
    logo = models.ImageField(upload_to='partners/', blank=True, null=True, verbose_name='Логотип')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_partner'
        verbose_name = 'Партнер'
        verbose_name_plural = 'Партнеры'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Config(models.Model):
    """
    Модель для хранения конфигурации сайта.
    Позволяет редактировать config.json через админ панель.
    """
    key = models.CharField(max_length=100, unique=True, default='main', verbose_name='Ключ конфигурации')
    config_data = models.JSONField(default=dict, verbose_name='Данные конфигурации')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    description = models.TextField(blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_config'
        verbose_name = 'Конфигурация'
        verbose_name_plural = 'Конфигурации'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Конфигурация: {self.key}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Синхронизируем с config.json при сохранении
        if self.is_active:
            self.sync_to_file()

    def sync_to_file(self):
        """
        Синхронизирует конфигурацию с файлом config.json
        """
        try:
            from pathlib import Path
            import json
            
            BASE_DIR = Path(__file__).resolve().parent.parent
            config_path = BASE_DIR / 'config.json'
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            
            # Перезагружаем кэш конфигурации
            from .config_loader import reload_config
            reload_config()
        except Exception as e:
            logger.warning('Failed to sync config to file: %s', e, exc_info=True)

    @classmethod
    def get_active_config(cls):
        """
        Получает активную конфигурацию из базы данных
        """
        try:
            config = cls.objects.filter(is_active=True).first()
            if config:
                return config.config_data
        except Exception:
            pass
        return None


class StoreConfig(models.Model):
    """Конфигурация магазина"""
    CURRENCY_SUM = 'сум'
    CURRENCY_UZS = 'UZS'
    CURRENCY_USD = 'USD'
    CURRENCY_EUR = 'EUR'
    CURRENCY_RUB = 'RUB'
    CURRENCY_CHOICES = [
        (CURRENCY_SUM, 'сум'),
        (CURRENCY_UZS, 'UZS'),
        (CURRENCY_USD, 'USD'),
        (CURRENCY_EUR, 'EUR'),
        (CURRENCY_RUB, 'RUB'),
    ]

    name = models.CharField(max_length=200, default='Fashion Store', verbose_name='Название магазина')
    title = models.CharField(max_length=200, default='Fashion Store - Online Clothing Store', verbose_name='Заголовок')
    description = models.TextField(default='Your reliable partner in the world of fashion. Quality clothing at affordable prices.', verbose_name='Описание')
    currency = models.CharField(
        max_length=8,
        choices=CURRENCY_CHOICES,
        default=CURRENCY_SUM,
        verbose_name='Валюта',
        help_text='Отображается рядом с ценами товаров на сайте и в админке',
    )
    logo = models.ImageField(upload_to='config/', blank=True, null=True, verbose_name='Логотип')
    favicon = models.ImageField(upload_to='config/', blank=True, null=True, verbose_name='Иконка сайта (favicon)')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_storeconfig'
        verbose_name = 'Настройки магазина'
        verbose_name_plural = 'Настройки магазина'

    def __str__(self):
        return f"Настройки магазина: {self.name}"

    def save(self, *args, **kwargs):
        # Обеспечиваем, что только одна запись активна
        if self.is_active:
            StoreConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class ContactConfig(models.Model):
    """Конфигурация контактов"""
    phone = models.CharField(max_length=50, default='+7 (800) 111111111111', verbose_name='Телефон')
    email = models.EmailField(default='info@ecommerce_platform.ru', verbose_name='Email')
    address_city = models.CharField(max_length=100, default='Tashkent', verbose_name='Город')
    address_street = models.CharField(max_length=200, default='Example Street, 1', verbose_name='Улица')
    address_full = models.CharField(max_length=300, default='Tashkent, Example Street, 1', verbose_name='Полный адрес')
    map_url = models.URLField(max_length=500, blank=True, null=True, verbose_name='URL Яндекс карты', help_text='Вставьте ссылку на Яндекс карту, например: https://yandex.uz/maps/-/CLhZvD6F')
    working_hours_weekdays = models.CharField(max_length=50, default='9:00 - 20:00', verbose_name='Рабочие часы (будни)')
    working_hours_weekend = models.CharField(max_length=50, default='10:00 - 18:00', verbose_name='Рабочие часы (выходные)')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_contactconfig'
        verbose_name = 'Контактная информация'
        verbose_name_plural = 'Контактная информация'

    def __str__(self):
        return f"Контакты: {self.phone}"

    def save(self, *args, **kwargs):
        if self.is_active:
            ContactConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class ProductFeatureConfig(models.Model):
    """Конфигурация features товара (отображаются на странице товара)"""
    title = models.CharField(max_length=200, verbose_name='Название')
    icon = models.CharField(max_length=100, default='fas fa-star', verbose_name='Иконка (Font Awesome класс)', help_text='Например: fas fa-shipping-fast')
    text = models.CharField(max_length=200, verbose_name='Текст')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_productfeatureconfig'
        verbose_name = 'Feature товара'
        verbose_name_plural = 'Features товаров'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class SocialConfig(models.Model):
    """Конфигурация социальных сетей"""
    instagram = models.URLField(default='#', blank=True, verbose_name='Instagram')
    facebook = models.URLField(default='#', blank=True, verbose_name='Facebook')
    twitter = models.URLField(default='#', blank=True, verbose_name='Twitter')
    vk = models.URLField(default='#', blank=True, verbose_name='VK')
    telegram = models.URLField(default='#', blank=True, verbose_name='Telegram')
    whatsapp = models.URLField(default='#', blank=True, verbose_name='WhatsApp')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_socialconfig'
        verbose_name = 'Социальные сети'
        verbose_name_plural = 'Социальные сети'

    def __str__(self):
        return "Социальные сети"

    def save(self, *args, **kwargs):
        if self.is_active:
            SocialConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class HeroConfig(models.Model):
    """Конфигурация главного баннера (Hero)"""
    title = models.CharField(max_length=200, default='New Collection', verbose_name='Заголовок')
    subtitle = models.CharField(max_length=200, default='Discover style and comfort', verbose_name='Подзаголовок')
    button_text = models.CharField(max_length=100, default='View Catalog', verbose_name='Текст кнопки')
    background_image = models.ImageField(upload_to='config/', blank=True, null=True, verbose_name='Фоновое изображение', help_text='Загрузите изображение или укажите URL ниже')
    background_image_url = models.URLField(blank=True, null=True, verbose_name='URL фонового изображения', help_text='Укажите URL изображения, если не загружаете файл')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_heroconfig'
        verbose_name = 'Главный баннер'
        verbose_name_plural = 'Главный баннер'

    def __str__(self):
        return f"Hero: {self.title}"

    def save(self, *args, **kwargs):
        if self.is_active:
            HeroConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Feature(models.Model):
    """Особенности/преимущества магазина"""
    icon = models.CharField(max_length=100, default='fas fa-star', verbose_name='Иконка (Font Awesome класс)', help_text='Например: fas fa-shipping-fast')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_feature'
        verbose_name = 'Особенность'
        verbose_name_plural = 'Особенности'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class AboutConfig(models.Model):
    """Конфигурация страницы "О нас" """
    title = models.CharField(max_length=200, default='About Us', verbose_name='Заголовок')
    description = models.TextField(default='We are a modern fashion store offering quality clothing for the whole family. Our mission is to make fashion accessible to everyone.', verbose_name='Описание')
    mission = models.TextField(default='To provide high-quality fashion items at affordable prices', verbose_name='Миссия')
    vision = models.TextField(default='To become the leading fashion retailer in the region', verbose_name='Видение')
    values = models.TextField(default='Quality\nCustomer Service\nInnovation\nSustainability', verbose_name='Ценности', help_text='Указывайте каждое значение с новой строки')
    image = models.ImageField(upload_to='config/', blank=True, null=True, verbose_name='Изображение', help_text='Загрузите изображение или укажите URL ниже')
    image_url = models.URLField(blank=True, null=True, verbose_name='URL изображения', help_text='Укажите URL изображения, если не загружаете файл')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_aboutconfig'
        verbose_name = 'О нас'
        verbose_name_plural = 'О нас'

    def __str__(self):
        return f"О нас: {self.title}"

    def get_values_list(self):
        """Возвращает список ценностей"""
        return [v.strip() for v in self.values.split('\n') if v.strip()]

    def save(self, *args, **kwargs):
        if self.is_active:
            AboutConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class AboutStat(models.Model):
    """Статистика для страницы "О нас" """
    value = models.CharField(max_length=50, default='10+', verbose_name='Значение', help_text='Например: 10+, 5000+, 24/7')
    label = models.CharField(max_length=200, default='Years in the market', verbose_name='Подпись')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_aboutstat'
        verbose_name = 'Статистика "О нас"'
        verbose_name_plural = 'Статистика "О нас"'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.value} - {self.label}"


class SEOConfig(models.Model):
    """SEO настройки"""
    meta_title = models.CharField(max_length=200, default='Fashion Store - Online Clothing Store', verbose_name='Meta заголовок')
    meta_description = models.TextField(default='Buy quality clothing online. Wide selection of men\'s, women\'s and children\'s clothing.', verbose_name='Meta описание')
    meta_keywords = models.CharField(max_length=500, default='clothing, fashion, online store, clothes', verbose_name='Meta ключевые слова')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_seoconfig'
        verbose_name = 'SEO настройки'
        verbose_name_plural = 'SEO настройки'

    def __str__(self):
        return f"SEO: {self.meta_title}"

    def save(self, *args, **kwargs):
        if self.is_active:
            SEOConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class ThemeConfig(models.Model):
    """Настройки темы (цвета)"""
    primary_color = models.CharField(max_length=7, default='#1976d2', verbose_name='Основной цвет', help_text='HEX цвет, например: #1976d2')
    secondary_color = models.CharField(max_length=7, default='#ffa726', verbose_name='Вторичный цвет', help_text='HEX цвет, например: #ffa726')
    text_color = models.CharField(max_length=7, default='#333', verbose_name='Цвет текста', help_text='HEX цвет, например: #333')
    background_color = models.CharField(max_length=7, default='#fff', verbose_name='Цвет фона', help_text='HEX цвет, например: #fff')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_themeconfig'
        verbose_name = 'Настройки темы'
        verbose_name_plural = 'Настройки темы'

    def __str__(self):
        return f"Тема: {self.primary_color}"

    def save(self, *args, **kwargs):
        if self.is_active:
            ThemeConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class TelegramConfig(models.Model):
    """Конфигурация Telegram бота для уведомлений"""
    bot_token = models.CharField(max_length=200, blank=True, verbose_name='Токен бота', help_text='Токен бота от @BotFather')
    group_chat_id = models.CharField(max_length=100, blank=True, verbose_name='ID группы/чата', help_text='ID группы или чата для отправки уведомлений (например: -1001234567890)')
    is_active = models.BooleanField(default=False, verbose_name='Активен', help_text='Включить отправку уведомлений в Telegram')
    notify_new_orders = models.BooleanField(default=True, verbose_name='Уведомлять о новых заказах')
    notify_status_changes = models.BooleanField(default=True, verbose_name='Уведомлять об изменении статуса')
    notify_contact_messages = models.BooleanField(default=True, verbose_name='Уведомлять о сообщениях из контактов')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_telegramconfig'
        verbose_name = 'Настройки Telegram'
        verbose_name_plural = 'Настройки Telegram'

    def __str__(self):
        return f"Telegram: {'Активен' if self.is_active else 'Неактивен'}"

    def save(self, *args, **kwargs):
        # Обеспечиваем, что только одна запись активна
        if self.is_active:
            TelegramConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active_config(cls):
        """Получает активную конфигурацию Telegram"""
        try:
            return cls.objects.filter(is_active=True).first()
        except Exception:
            return None


class ContactMessage(models.Model):
    """Сообщения из формы контактов"""
    SUBJECT_CHOICES = [
        ('order', 'Вопрос по заказу'),
        ('product', 'Вопрос по товару'),
        ('delivery', 'Доставка'),
        ('return', 'Возврат'),
        ('other', 'Другое'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, verbose_name='Тема')
    message = models.TextField(verbose_name='Сообщение')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_contactmessage'
        verbose_name = 'Сообщение из контактов'
        verbose_name_plural = 'Сообщения из контактов'
        ordering = ['-created_at']

    def __str__(self):
        return f"Сообщение от {self.name} - {self.get_subject_display()}"


class FAQ(models.Model):
    """Часто задаваемые вопросы"""
    question = models.CharField(max_length=500, verbose_name='Вопрос')
    answer = models.TextField(verbose_name='Ответ')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок отображения', help_text='Чем меньше число, тем выше вопрос в списке')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_faq'
        verbose_name = 'Часто задаваемый вопрос'
        verbose_name_plural = 'Часто задаваемые вопросы'
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.question


class TelegramNotificationSettings(models.Model):
    """Per-site Telegram toggles and optional bot token override."""

    bot_token = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Токен бота',
        help_text='От @BotFather. Если пусто — используется TELEGRAM_BOT_TOKEN из окружения.',
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='Включить уведомления в Telegram',
    )
    notify_new_orders = models.BooleanField(default=True, verbose_name='Сообщать о новых заказах')
    notify_status_changes = models.BooleanField(default=True, verbose_name='Сообщать о смене статуса заказа')
    notify_contact_messages = models.BooleanField(default=True, verbose_name='Сообщать о сообщениях с формы «Контакты»')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_telegramnotificationsettings'
        verbose_name = 'Telegram — настройки'
        verbose_name_plural = 'Telegram — настройки'

    def __str__(self):
        return 'Telegram: активен' if self.is_active else 'Telegram: выключен'

    def save(self, *args, **kwargs):
        if self.is_active:
            TelegramNotificationSettings.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()

    def resolved_bot_token(self) -> str:
        from django.conf import settings as dj_settings

        db_token = (self.bot_token or '').strip()
        if db_token:
            return db_token
        return (getattr(dj_settings, 'TELEGRAM_BOT_TOKEN', None) or '').strip()


class TelegramSubscriber(models.Model):
    """Private chat recipients for this site database."""

    telegram_chat_id = models.BigIntegerField(
        verbose_name='ID чата в Telegram',
        db_index=True,
        help_text='Число из @userinfobot или после привязки бота.',
    )
    telegram_username = models.CharField(max_length=255, blank=True, verbose_name='Ник в Telegram')
    display_name = models.CharField(max_length=255, blank=True, verbose_name='Как подписать в списке')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_telegramsubscriber'
        verbose_name = 'Telegram — получатель'
        verbose_name_plural = 'Telegram — кому слать'
        ordering = ['-created_at']

    def __str__(self):
        return self.display_name or self.telegram_username or str(self.telegram_chat_id)


class NotificationOutbox(models.Model):
    """Transactional outbox for async Telegram delivery."""

    class EventType(models.TextChoices):
        ORDER_PLACED = 'order_placed', 'Новый заказ'
        ORDER_STATUS_CHANGED = 'order_status_changed', 'Смена статуса'
        CONTACT_MESSAGE = 'contact_message', 'Контакты'

    class Status(models.TextChoices):
        PENDING = 'pending', 'В очереди'
        PROCESSING = 'processing', 'Обработка'
        SENT = 'sent', 'Отправлено'
        FAILED = 'failed', 'Ошибка'

    event_type = models.CharField(max_length=64, choices=EventType.choices, verbose_name='Событие')
    payload = models.JSONField(default=dict, verbose_name='Payload')
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус',
        db_index=True,
    )
    attempts = models.PositiveIntegerField(default=0, verbose_name='Попытки')
    last_error = models.TextField(blank=True, verbose_name='Последняя ошибка')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        db_table = 'store_notificationoutbox'
        verbose_name = 'Очередь Telegram'
        verbose_name_plural = 'Очередь Telegram'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f'{self.event_type} #{self.pk} ({self.status})'