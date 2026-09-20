from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django import forms
from modeltranslation.admin import TabbedTranslationAdmin
from modeltranslation.translator import translator
from .models import (
    Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, Partner, Config,
    StoreConfig, ContactConfig, SocialConfig, HeroConfig, Feature, AboutConfig, SEOConfig, ThemeConfig,
    ProductFeatureConfig, AboutStat, TelegramConfig, ContactMessage, FAQ,
    TelegramNotificationSettings, TelegramSubscriber, NotificationOutbox,
)
from .currency import format_money, get_store_currency


# Импортируем переводы перед регистрацией админки
try:
    from . import translation
except ImportError:
    pass


@admin.register(Category)
class CategoryAdmin(TabbedTranslationAdmin):
    list_display = ['name', 'slug', 'image_preview', 'products_count', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Изображение', {
            'fields': ('image', 'image_url', 'image_preview')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', obj.image.url)
        elif obj.image_url:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', obj.image_url)
        return "Нет изображения"
    image_preview.short_description = 'Превью'

    def products_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:catalog_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} товаров</a>', url, count)
    products_count.short_description = 'Товаров'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'image_preview', 'created_at')
    readonly_fields = ('image_preview', 'created_at')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 80px; max-height: 80px;" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = 'Превью'


@admin.register(Product)
class ProductAdmin(TabbedTranslationAdmin):
    exclude = ('available_sizes',)
    list_display = ['name', 'category', 'price_display', 'old_price_display', 'stock', 'is_active', 'image_preview', 'created_at']
    list_filter = ['category', 'is_active', 'created_at', 'rating']
    search_fields = ['name', 'description', 'available_colors']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'image_preview', 'image_url_preview', 'discount_percent', 'colors_help']
    inlines = [ProductImageInline]
    list_editable = ['is_active', 'stock']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Цены', {
            'fields': ('price', 'old_price', 'discount_percent')
        }),
        ('Изображения', {
            'fields': ('image', 'image_preview', 'image_url', 'image_url_preview'),
            'description': (
                'Основное изображение показывается в каталоге и на карточке. '
                'Если загружен файл — он важнее поля URL. '
                'Дополнительные фото добавляйте ниже (инлайн «Изображения товара»).'
            ),
        }),
        ('Характеристики', {
            'fields': ('available_colors', 'colors_help', 'stock', 'is_active'),
            'description': 'Укажите доступные цвета для товара'
        }),
        ('Рейтинг', {
            'fields': ('rating', 'reviews_count')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def colors_help(self, obj):
        """Подсказка о доступных цветах"""
        colors_list = [
            ('Черный', '#000000'),
            ('Белый', '#FFFFFF'),
            ('Синий', '#2196F3'),
            ('Красный', '#F44336'),
            ('Зеленый', '#4CAF50'),
            ('Желтый', '#FFEB3B'),
            ('Серый', '#9E9E9E'),
        ]
        html = '<div style="margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px;">'
        html += '<strong>Доступные цвета:</strong><br>'
        html += '<div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 10px;">'
        for color_name, color_code in colors_list:
            html += f'''
            <div style="display: inline-flex; align-items: center; gap: 5px; padding: 5px 10px; background: white; border-radius: 4px; border: 1px solid #ddd;">
                <span style="display: inline-block; width: 20px; height: 20px; border-radius: 50%; background-color: {color_code}; border: 1px solid #ccc;"></span>
                <span>{color_name}</span>
            </div>
            '''
        html += '</div>'
        html += '<p style="margin-top: 10px; margin-bottom: 0; color: #666; font-size: 0.9em;">'
        html += '💡 <strong>Подсказка:</strong> Указывайте цвета через запятую, например: "Черный, Белый, Синий"'
        html += '</p></div>'
        return mark_safe(html)
    colors_help.short_description = 'Подсказка по цветам'

    def price_display(self, obj):
        return format_money(obj.price)
    price_display.short_description = 'Цена'

    def old_price_display(self, obj):
        if obj.old_price:
            amount = f"{obj.old_price:,.0f}".replace(',', ' ')
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">{} {}</span>',
                amount,
                get_store_currency(),
            )
        return "-"
    old_price_display.short_description = 'Старая цена'

    def image_preview(self, obj):
        from .media_urls import product_display_image_url
        url = product_display_image_url(obj) if obj and obj.pk else ''
        if url:
            return format_html('<img src="{}" style="max-width: 150px; max-height: 150px;" />', url)
        return "Нет изображения"
    image_preview.short_description = 'Превью'

    def image_url_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="max-width: 150px; max-height: 150px;" />', obj.image_url)
        return "Нет URL изображения"
    image_url_preview.short_description = 'Превью URL'

    def save_model(self, request, obj, form, change):
        # Uploaded file wins over stale demos / external URLs.
        if 'image' in form.changed_data and form.cleaned_data.get('image'):
            obj.image_url = ''
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        # If primary empty but gallery has files — promote first extra to primary.
        if obj.pk and not obj.image:
            first = obj.images.order_by('id').first()
            if first and first.image:
                obj.image = first.image.name
                # Drop stale external demo URL so the upload is what customers see.
                update = ['image']
                if obj.image_url:
                    obj.image_url = ''
                    update.append('image_url')
                obj.save(update_fields=update)

    def discount_percent(self, obj):
        if obj.old_price and obj.old_price > obj.price:
            discount = ((obj.old_price - obj.price) / obj.old_price) * 100
            return format_html('<span style="color: #d32f2f; font-weight: bold;">-{}%</span>', round(discount, 0))
        return "-"
    discount_percent.short_description = 'Скидка'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'created_at']
    list_filter = ['created_at', 'product__category']
    search_fields = ['product__name']
    readonly_fields = ['image_preview', 'created_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = 'Превью'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'items_count_display', 'total_display', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['session_key']
    readonly_fields = ['created_at', 'updated_at', 'items_count_display', 'total_display']
    fieldsets = (
        ('Информация', {
            'fields': ('session_key', 'items_count_display', 'total_display')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def items_count_display(self, obj):
        count = obj.items_count
        url = reverse('admin:catalog_cartitem_changelist') + f'?cart__id__exact={obj.id}'
        return format_html('<a href="{}">{} товаров</a>', url, count)
    items_count_display.short_description = 'Товаров в корзине'

    def total_display(self, obj):
        return format_money(obj.total)
    total_display.short_description = 'Итого'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    exclude = ('size',)
    list_display = ['product', 'cart', 'quantity', 'color', 'total_display', 'created_at']
    list_filter = ['cart', 'created_at', 'product__category']
    search_fields = ['product__name', 'cart__session_key']
    readonly_fields = ['total_display', 'created_at', 'updated_at']

    def total_display(self, obj):
        return format_money(obj.total)
    total_display.short_description = 'Итого'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_display']
    fields = ('product', 'quantity', 'price', 'color', 'total_display')
    can_delete = False

    def total_display(self, obj):
        if obj and obj.pk:
            return format_money(obj.total)
        return "-"
    total_display.short_description = 'Итого'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'email', 'phone', 'total_display', 'status', 'status_badge', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'city', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'address']
    readonly_fields = ['created_at', 'updated_at', 'total_display', 'items_count_display', 'status_badge']
    inlines = [OrderItemInline]
    list_editable = ['status']
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('status', 'payment_method', 'total_display', 'items_count_display')
        }),
        ('Информация о клиенте', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Адрес доставки', {
            'fields': ('address', 'city', 'postal_code')
        }),
        ('Дополнительно', {
            'fields': ('session_key', 'notes')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def customer_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    customer_name.short_description = 'Клиент'

    def total_display(self, obj):
        total_formatted = f"{obj.total:,.0f}".replace(',', ' ')
        return format_html(
            '<strong style="font-size: 16px; color: #1976d2;">{} {}</strong>',
            total_formatted,
            get_store_currency(),
        )
    total_display.short_description = 'Итого'

    def status_badge(self, obj):
        colors = {
            'pending': '#ff9800',
            'processing': '#2196f3',
            'shipped': '#9c27b0',
            'delivered': '#4caf50',
            'cancelled': '#f44336',
        }
        color = colors.get(obj.status, '#757575')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

    def items_count_display(self, obj):
        return f"{obj.items.count()} товаров"
    items_count_display.short_description = 'Товаров в заказе'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    exclude = ('size',)
    list_display = ['order', 'product', 'quantity', 'price', 'color', 'total_display']
    list_filter = ['order__status', 'order__created_at', 'product__category']
    search_fields = ['product__name', 'order__first_name', 'order__last_name', 'order__email']
    readonly_fields = ['total_display']

    def total_display(self, obj):
        if obj and obj.pk:
            return format_money(obj.total)
        return "-"
    total_display.short_description = 'Итого'


# Настройка админ-сайта
admin.site.site_header = "Панель магазина"
admin.site.site_title = "Admin"
admin.site.index_title = "Обзор"
admin.site.index_template = 'admin/index.html'

# Практичный порядок в сайдбаре: сначала продажи и каталог
_ADMIN_MODEL_ORDER = {
    'order': 10,
    'orderitem': 11,
    'product': 20,
    'category': 21,
    'productimage': 22,
    'contactmessage': 30,
    'faq': 31,
    'partner': 32,
    'telegramnotificationsettings': 40,
    'telegramsubscriber': 41,
    'notificationoutbox': 42,
    'storeconfig': 50,
    'contactconfig': 51,
    'socialconfig': 52,
    'heroconfig': 53,
    'feature': 54,
    'aboutconfig': 55,
    'aboutstat': 56,
    'seoconfig': 57,
    'themeconfig': 58,
    'productfeatureconfig': 59,
    'config': 60,
    'cart': 90,
    'cartitem': 91,
}

_original_get_app_list = admin.site.get_app_list


def _sorted_admin_app_list(request, app_label=None):
    app_list = _original_get_app_list(request, app_label)
    for app in app_list:
        if app.get('app_label') != 'store':
            continue
        app['models'].sort(
            key=lambda m: (
                _ADMIN_MODEL_ORDER.get(str(m.get('object_name', '')).lower(), 80),
                m.get('name', ''),
            )
        )
    return app_list


admin.site.get_app_list = _sorted_admin_app_list


@admin.register(Partner)
class PartnerAdmin(TabbedTranslationAdmin):
    list_display = ['name', 'icon', 'logo_preview', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at', 'logo_preview']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'icon', 'url', 'description', 'is_active', 'order')
        }),
        ('Логотип', {
            'fields': ('logo', 'logo_preview')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', obj.logo.url)
        return "Нет логотипа"
    logo_preview.short_description = 'Превью логотипа'


class ConfigAdminForm(forms.ModelForm):
    """
    Форма для редактирования конфигурации с валидацией JSON
    """
    class Meta:
        model = Config
        fields = '__all__'
        widgets = {
            'config_data': forms.Textarea(attrs={
                'rows': 30,
                'style': 'font-family: monospace; font-size: 12px;',
                'placeholder': 'Введите валидный JSON...'
            }),
        }

    def clean_config_data(self):
        config_data = self.cleaned_data.get('config_data')
        if isinstance(config_data, str):
            import json
            try:
                config_data = json.loads(config_data)
            except json.JSONDecodeError as e:
                raise forms.ValidationError(f'Невалидный JSON: {e}')
        return config_data


@admin.register(Config)
class ConfigAdmin(admin.ModelAdmin):
    form = ConfigAdminForm
    list_display = ['key', 'is_active', 'config_preview', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at', 'config_info']
    fieldsets = (
        ('Основная информация', {
            'fields': ('key', 'is_active', 'description')
        }),
        ('Конфигурация', {
            'fields': ('config_data', 'config_info'),
            'description': 'Введите конфигурацию в формате JSON. При сохранении она будет синхронизирована с config.json'
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def config_preview(self, obj):
        """Показывает краткую информацию о конфигурации"""
        if obj.config_data:
            sections = list(obj.config_data.keys())[:5]
            sections_str = ', '.join(sections)
            if len(obj.config_data) > 5:
                sections_str += f' ... (+{len(obj.config_data) - 5} секций)'
            return format_html('<span style="font-family: monospace;">{}</span>', sections_str)
        return "Пустая конфигурация"
    config_preview.short_description = 'Секции конфигурации'

    def config_info(self, obj):
        """Показывает информацию о структуре конфигурации"""
        if not obj.config_data:
            return "Конфигурация пуста"
        
        import json
        try:
            config_str = json.dumps(obj.config_data, ensure_ascii=False, indent=2)
            size = len(config_str)
            sections = list(obj.config_data.keys())
            
            info = f"""
            <div style="background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;">
                <strong>Информация о конфигурации:</strong><br>
                • Секций: {len(sections)}<br>
                • Размер: {size} символов<br>
                • Секции: {', '.join(sections[:10])}{'...' if len(sections) > 10 else ''}
            </div>
            """
            return mark_safe(info)
        except Exception as e:
            return format_html('<span style="color: red;">Ошибка: {}</span>', str(e))
    config_info.short_description = 'Информация'

    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение для синхронизации с файлом"""
        super().save_model(request, obj, form, change)
        if obj.is_active:
            obj.sync_to_file()
            self.message_user(request, 'Конфигурация сохранена и синхронизирована с config.json')


@admin.register(StoreConfig)
class StoreConfigAdmin(TabbedTranslationAdmin):
    def has_module_permission(self, request):
        """Скрываем из списка админки, но оставляем доступ к редактированию"""
        return False
    list_display = ['name', 'currency', 'is_active', 'updated_at']
    readonly_fields = ['updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'title', 'description', 'currency', 'is_active')
        }),
        ('Изображения', {
            'fields': ('logo', 'favicon')
        }),
        ('Даты', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ContactConfig)
class ContactConfigAdmin(TabbedTranslationAdmin):
    def has_module_permission(self, request):
        """Скрываем из списка админки, но оставляем доступ к редактированию"""
        return False
    list_display = ['phone', 'email', 'is_active', 'updated_at']
    readonly_fields = ['updated_at']
    fieldsets = (
        ('Контактная информация', {
            'fields': ('phone', 'email', 'is_active')
        }),
        ('Адрес', {
            'fields': ('address_city', 'address_street', 'address_full', 'map_url')
        }),
        ('Рабочие часы', {
            'fields': ('working_hours_weekdays', 'working_hours_weekend')
        }),
        ('Даты', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(SocialConfig)
class SocialConfigAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        """Скрываем из списка админки, но оставляем доступ к редактированию"""
        return False
    list_display = ['instagram', 'facebook', 'telegram', 'is_active', 'updated_at']
    readonly_fields = ['updated_at']
    fieldsets = (
        ('Социальные сети', {
            'fields': ('instagram', 'facebook', 'twitter', 'vk', 'telegram', 'whatsapp', 'is_active')
        }),
        ('Даты', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(HeroConfig)
class HeroConfigAdmin(TabbedTranslationAdmin):
    def has_module_permission(self, request):
        """Скрываем из списка админки, но оставляем доступ к редактированию"""
        return False
    list_display = ['title', 'subtitle', 'is_active', 'updated_at']
    readonly_fields = ['updated_at', 'background_image_preview']
    fieldsets = (
        ('Содержимое', {
            'fields': ('title', 'subtitle', 'button_text', 'is_active')
        }),
        ('Изображение', {
            'fields': ('background_image', 'background_image_url', 'background_image_preview'),
            'description': 'Загрузите изображение или укажите URL. Приоритет у загруженного изображения.'
        }),
        ('Даты', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def background_image_preview(self, obj):
        """Показывает превью фонового изображения"""
        if obj.pk:
            if obj.background_image:
                return format_html('<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 5px; margin-top: 10px;" />', obj.background_image.url)
            elif obj.background_image_url:
                return format_html('<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 5px; margin-top: 10px;" />', obj.background_image_url)
        return "Сохраните для предпросмотра"
    background_image_preview.short_description = 'Превью изображения'


@admin.register(Feature)
class FeatureAdmin(TabbedTranslationAdmin):
    def has_module_permission(self, request):
        """Скрываем из списка админки, но оставляем доступ к редактированию"""
        return False
    list_display = ['title', 'icon', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['order', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'icon', 'order', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AboutConfig)
class AboutConfigAdmin(TabbedTranslationAdmin):
    def has_module_permission(self, request):
        """Скрываем из списка админки, но оставляем доступ к редактированию"""
        return False
    list_display = ['title', 'is_active', 'updated_at']
    readonly_fields = ['updated_at', 'image_preview']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'is_active')
        }),
        ('Миссия и видение', {
            'fields': ('mission', 'vision')
        }),
        ('Ценности', {
            'fields': ('values',),
            'description': 'Указывайте каждое значение с новой строки'
        }),
        ('Изображение', {
            'fields': ('image', 'image_url', 'image_preview'),
            'description': 'Загрузите изображение или укажите URL. Приоритет у загруженного изображения.'
        }),
        ('Даты', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        """Показывает превью изображения"""
        if obj.pk:
            if obj.image:
                return format_html('<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 5px; margin-top: 10px;" />', obj.image.url)
            elif obj.image_url:
                return format_html('<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 5px; margin-top: 10px;" />', obj.image_url)
        return "Сохраните для предпросмотра"
    image_preview.short_description = 'Превью изображения'


@admin.register(AboutStat)
class AboutStatAdmin(TabbedTranslationAdmin):
    def has_module_permission(self, request):
        """Скрываем из списка админки"""
        return False
    
    list_display = ['value', 'label', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['value', 'label']
    list_editable = ['order', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('value', 'label', 'order', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SEOConfig)
class SEOConfigAdmin(TabbedTranslationAdmin):
    def has_module_permission(self, request):
        """Скрываем из списка админки, но оставляем доступ к редактированию"""
        return False
    list_display = ['meta_title', 'is_active', 'updated_at']
    readonly_fields = ['updated_at']
    fieldsets = (
        ('SEO настройки', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'is_active')
        }),
        ('Даты', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ThemeConfig)
class ThemeConfigAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        """Скрываем из списка админки, но оставляем доступ к редактированию"""
        return False
    list_display = ['primary_color', 'secondary_color', 'is_active', 'updated_at']
    readonly_fields = ['updated_at', 'color_preview']
    fieldsets = (
        ('Цвета темы', {
            'fields': ('primary_color', 'secondary_color', 'text_color', 'background_color', 'is_active', 'color_preview')
        }),
        ('Даты', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def color_preview(self, obj):
        """Показывает превью цветов"""
        if obj.pk:
            html = f"""
            <div style="display: flex; gap: 10px; margin: 10px 0;">
                <div style="width: 50px; height: 50px; background: {obj.primary_color}; border: 1px solid #ddd; border-radius: 5px;"></div>
                <div style="width: 50px; height: 50px; background: {obj.secondary_color}; border: 1px solid #ddd; border-radius: 5px;"></div>
                <div style="width: 50px; height: 50px; background: {obj.text_color}; border: 1px solid #ddd; border-radius: 5px;"></div>
                <div style="width: 50px; height: 50px; background: {obj.background_color}; border: 1px solid #ddd; border-radius: 5px;"></div>
            </div>
            <p><small>Основной | Вторичный | Текст | Фон</small></p>
            """
            return mark_safe(html)
        return "Сохраните для предпросмотра"
    color_preview.short_description = 'Превью цветов'


@admin.register(ProductFeatureConfig)
class ProductFeatureConfigAdmin(TabbedTranslationAdmin):
    list_display = ['title', 'icon', 'text', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'text']
    list_editable = ['order', 'is_active']
    readonly_fields = ['created_at', 'updated_at', 'icon_preview']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'text', 'icon', 'icon_preview', 'order', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def icon_preview(self, obj):
        """Показывает превью иконки"""
        if obj.icon:
            return format_html(
                '<i class="{}" style="font-size: 24px; color: #1976d2;"></i> <span style="margin-left: 10px;">{}</span>',
                obj.icon, obj.icon
            )
        return "Иконка не указана"
    icon_preview.short_description = 'Превью иконки'


@admin.register(TelegramConfig)
class TelegramConfigAdmin(admin.ModelAdmin):
    """Legacy Telegram settings. Prefer TelegramNotificationSettings."""

    def has_module_permission(self, request):
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'subject_display', 'is_read', 'created_at']
    list_filter = ['subject', 'is_read', 'created_at']
    search_fields = ['name', 'email', 'phone', 'message']
    readonly_fields = ['created_at', 'updated_at', 'subject_display']
    list_editable = ['is_read']
    fieldsets = (
        ('Информация о отправителе', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Сообщение', {
            'fields': ('subject', 'subject_display', 'message', 'is_read')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def subject_display(self, obj):
        return obj.get_subject_display()
    subject_display.short_description = 'Тема'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()


@admin.register(FAQ)
class FAQAdmin(TabbedTranslationAdmin):
    list_display = ('question', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'created_at')

    fieldsets = (
        ('Основная информация', {
            'fields': ('question', 'answer', 'order', 'is_active')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')


@admin.register(TelegramNotificationSettings)
class TelegramNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        'is_active',
        'bot_token_preview',
        'notify_new_orders',
        'notify_status_changes',
        'notify_contact_messages',
        'updated_at',
    )
    readonly_fields = ('updated_at', 'test_connection', 'env_token_hint')

    def has_add_permission(self, request):
        # Одна запись настроек на сайт
        if TelegramNotificationSettings.objects.exists():
            return False
        return super().has_add_permission(request)

    def changelist_view(self, request, extra_context=None):
        obj = TelegramNotificationSettings.objects.first()
        if obj:
            from django.shortcuts import redirect
            return redirect(
                reverse('admin:catalog_telegramnotificationsettings_change', args=[obj.pk])
            )
        return super().changelist_view(request, extra_context)

    fieldsets = (
        (
            'Токен бота',
            {
                'fields': ('bot_token', 'env_token_hint'),
                'description': (
                    'Токен от @BotFather. Можно указать здесь для сайта, '
                    'или оставить пустым и задать TELEGRAM_BOT_TOKEN в .env / окружении.'
                ),
            },
        ),
        (
            'Уведомления',
            {
                'fields': (
                    'is_active',
                    'notify_new_orders',
                    'notify_status_changes',
                    'notify_contact_messages',
                ),
            },
        ),
        (
            'Проверка',
            {
                'fields': ('test_connection',),
                'description': 'Сначала добавьте получателя в «Telegram — кому слать».',
            },
        ),
        ('Даты', {'fields': ('updated_at',), 'classes': ('collapse',)}),
    )

    def bot_token_preview(self, obj):
        if obj.bot_token:
            token = obj.bot_token
            if len(token) > 20:
                return f'{token[:10]}...{token[-6:]}'
            return token
        return 'Из TELEGRAM_BOT_TOKEN / .env'

    bot_token_preview.short_description = 'Токен бота'

    def env_token_hint(self, obj):
        from django.conf import settings as dj_settings

        token = (getattr(dj_settings, 'TELEGRAM_BOT_TOKEN', None) or '').strip()
        if token:
            return mark_safe(
                f'<span style="color:#2e7d32;">.env TELEGRAM_BOT_TOKEN задан '
                f'({token[:6]}…{token[-4:]})</span>'
            )
        return mark_safe(
            '<span style="color:#c62828;">TELEGRAM_BOT_TOKEN в .env пустой — '
            'укажите токен здесь или в .env</span>'
        )

    env_token_hint.short_description = 'Токен из окружения'

    def test_connection(self, obj):
        """Hint only — never call Telegram on page render (was making admin crawl)."""
        if not obj or not obj.pk:
            return 'Сохраните настройки, затем добавьте получателя и проверьте токен через бота.'

        token = obj.resolved_bot_token()
        if not token:
            return mark_safe(
                '<span style="color:#b91c1c;">Нет токена: заполните поле выше или TELEGRAM_BOT_TOKEN в .env</span>'
            )

        has_sub = TelegramSubscriber.objects.filter(is_active=True).exists()
        if not has_sub:
            return mark_safe(
                '<span style="color:#b45309;">Добавьте получателя в «Telegram — кому слать». '
                'Тест уйдёт автоматически при новом заказе.</span>'
            )

        return mark_safe(
            '<span style="color:#15803d;">Токен и получатель заданы. '
            'Создайте тестовый заказ — уведомление придёт в Telegram.</span>'
        )

    test_connection.short_description = 'Готовность'


@admin.register(TelegramSubscriber)
class TelegramSubscriberAdmin(admin.ModelAdmin):
    list_display = ('telegram_chat_id', 'telegram_username', 'display_name', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('telegram_username', 'display_name', 'telegram_chat_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (
            None,
            {
                'fields': ('telegram_chat_id', 'telegram_username', 'display_name', 'is_active'),
                'description': 'ID чата — число из @userinfobot. Можно и личный chat, и group id.',
            },
        ),
        ('Даты', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


@admin.register(NotificationOutbox)
class NotificationOutboxAdmin(admin.ModelAdmin):
    list_display = ('id', 'event_type', 'status', 'attempts', 'created_at', 'last_error')
    list_filter = ('status', 'event_type')
    search_fields = ('last_error',)
    readonly_fields = ('event_type', 'payload', 'status', 'attempts', 'last_error', 'created_at', 'updated_at')
