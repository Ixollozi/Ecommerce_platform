"""
Утилита для загрузки конфигурации из моделей или config.json
"""
import json
import os
from pathlib import Path

# Используем BASE_DIR напрямую, чтобы избежать циклических импортов
BASE_DIR = Path(__file__).resolve().parent.parent


def get_active_base_dir() -> Path:
    """Project root in single-site mode, site folder in platform mode."""
    try:
        from catalog.platform.context import get_current_site

        site = get_current_site()
        if site is not None:
            return site.root
    except Exception:
        pass
    return BASE_DIR


def load_config_from_models():
    """
    Загружает конфигурацию из отдельных моделей (StoreConfig, ContactConfig и т.д.)
    ОСНОВА - данные из админки. config.json используется ТОЛЬКО как заглушка, если в БД нет данных.
    """
    try:
        from .models import (
            StoreConfig, ContactConfig, SocialConfig, HeroConfig,
            Feature, AboutConfig, SEOConfig, ThemeConfig
        )
        
        # Загружаем config.json только для использования как заглушка
        file_config = load_config_from_file() or {}
        
        config = {}
        
        # Store - ПРИОРИТЕТ: админка, если нет - config.json как заглушка
        # Проверяем наличие ЛЮБОЙ записи (активной или неактивной), но приоритет у активной
        store = StoreConfig.objects.filter(is_active=True).first()
        if not store:
            # Если нет активной, проверяем есть ли вообще записи
            store = StoreConfig.objects.first()
        
        if store:
            # Используем данные из админки (даже если они пустые - это приоритет!)
            config['store'] = {
                'name': store.name or '',  # Используем значение из БД, даже если пустое
                'title': store.title or '',
                'description': store.description or '',
                'currency': getattr(store, 'currency', None) or 'сум',
                'logo': store.logo.url if store.logo else '',
                'favicon': store.favicon.url if store.favicon else '',
            }
        elif 'store' in file_config:
            # Заглушка из config.json только если в БД вообще нет записей
            config['store'] = file_config['store']
        
        # Contact - ПРИОРИТЕТ: админка, если нет - config.json как заглушка
        contact = ContactConfig.objects.filter(is_active=True).first()
        if contact:
            # Используем данные из админки
            config['contact'] = {
                'phone': contact.phone,
                'email': contact.email,
                'address': {
                    'city': contact.address_city,
                    'street': contact.address_street,
                    'full': contact.address_full,
                },
                'map_url': contact.map_url or '',
                'working_hours': {
                    'weekdays': contact.working_hours_weekdays,
                    'weekend': contact.working_hours_weekend,
                }
            }
        elif 'contact' in file_config:
            # Заглушка из config.json
            config['contact'] = file_config['contact']
        
        # Social - ПРИОРИТЕТ: админка, если нет - config.json как заглушка
        social = SocialConfig.objects.filter(is_active=True).first()
        if social:
            # Используем данные из админки
            config['social'] = {
                'instagram': social.instagram,
                'facebook': social.facebook,
                'twitter': social.twitter,
                'vk': social.vk,
                'telegram': social.telegram,
                'whatsapp': social.whatsapp,
            }
        elif 'social' in file_config:
            # Заглушка из config.json
            config['social'] = file_config['social']
        
        # Hero - ПРИОРИТЕТ: админка, если нет - config.json как заглушка
        hero = HeroConfig.objects.filter(is_active=True).first()
        if hero:
            # Используем данные из админки
            # Приоритет: загруженное изображение > URL изображения > заглушка из config.json
            bg_image = ''
            if hero.background_image:
                bg_image = hero.background_image.url
            elif hero.background_image_url:
                bg_image = hero.background_image_url
            else:
                bg_image = file_config.get('hero', {}).get('background_image', '')
            
            config['hero'] = {
                'title': hero.title,
                'subtitle': hero.subtitle,
                'button_text': hero.button_text,
                'background_image': bg_image,
            }
        elif 'hero' in file_config:
            # Заглушка из config.json
            config['hero'] = file_config['hero']
        
        # Features - ПРИОРИТЕТ: админка, если нет - config.json как заглушка
        features = Feature.objects.filter(is_active=True).order_by('order', 'title')
        if features.exists():
            # Используем данные из админки
            config['features'] = [
                {
                    'icon': f.icon,
                    'title': f.title,
                    'description': f.description,
                }
                for f in features
            ]
        elif 'features' in file_config:
            # Заглушка из config.json
            config['features'] = file_config['features']
        
        # About - ПРИОРИТЕТ: админка, если нет - config.json как заглушка
        about = AboutConfig.objects.filter(is_active=True).first()
        if about:
            # Используем данные из админки
            config['about'] = {
                'title': about.title,
                'description': about.description,
                'mission': about.mission,
                'vision': about.vision,
                'values': about.get_values_list(),
            }
        elif 'about' in file_config:
            # Заглушка из config.json
            config['about'] = file_config['about']
        
        # SEO - ПРИОРИТЕТ: админка, если нет - config.json как заглушка
        seo = SEOConfig.objects.filter(is_active=True).first()
        if seo:
            # Используем данные из админки
            config['seo'] = {
                'meta_title': seo.meta_title,
                'meta_description': seo.meta_description,
                'meta_keywords': seo.meta_keywords,
            }
        elif 'seo' in file_config:
            # Заглушка из config.json
            config['seo'] = file_config['seo']
        
        # Theme - ПРИОРИТЕТ: админка, если нет - config.json как заглушка
        theme = ThemeConfig.objects.filter(is_active=True).first()
        if theme:
            # Используем данные из админки
            config['theme'] = {
                'primary_color': theme.primary_color,
                'secondary_color': theme.secondary_color,
                'text_color': theme.text_color,
                'background_color': theme.background_color,
            }
        elif 'theme' in file_config:
            # Заглушка из config.json
            config['theme'] = file_config['theme']
        
        # Добавляем ТОЛЬКО те секции из config.json, которых нет в админке (например, django)
        # Это системные настройки, которые не управляются через админку
        system_sections = ['django']  # Секции, которые всегда берутся из config.json
        for key in system_sections:
            if key in file_config and key not in config:
                config[key] = file_config[key]
        
        # Возвращаем конфигурацию (из админки или заглушку из config.json)
        return config if config else None
            
    except Exception as e:
        # Если таблицы еще не созданы или другая ошибка, используем config.json как заглушку
        file_config = load_config_from_file()
        if file_config:
            return file_config
        return None


def load_config_from_db():
    """
    Загружает конфигурацию из базы данных (модель Config - JSON)
    Второй приоритет
    """
    try:
        # Импортируем здесь, чтобы избежать циклических импортов
        from .models import Config
        config = Config.get_active_config()
        if config:
            return config
    except Exception as e:
        # Если таблица еще не создана или другая ошибка, игнорируем
        pass
    return None


def load_config_from_file():
    """
    Загружает конфигурацию из config.json
    """
    config_path = get_active_base_dir() / 'config.json'
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config.json: {e}")
        return None


def load_config():
    """
    Загружает конфигурацию с приоритетом:
    1. Из отдельных моделей (StoreConfig, ContactConfig и т.д.) - самый высокий приоритет
       Если данных нет в БД, использует config.json как заглушку
    2. Из базы данных (модель Config - JSON)
    3. Из config.json
    4. Конфигурация по умолчанию
    """
    # Сначала пытаемся загрузить из отдельных моделей (уже включает fallback на config.json)
    config = load_config_from_models()
    if config:
        return config
    
    # Затем из модели Config (JSON)
    config = load_config_from_db()
    if config:
        return config
    
    # Затем из файла
    config = load_config_from_file()
    if config:
        return config
    
    # Иначе используем конфигурацию по умолчанию
    return get_default_config()


def get_default_config():
    """
    Возвращает конфигурацию по умолчанию
    """
    return {
        "store": {
            "name": "Fashion Store",
            "title": "Fashion Store - Online Clothing Store",
            "description": "Your reliable partner in the world of fashion. Quality clothing at affordable prices.",
        },
        "contact": {
            "phone": "+7 (800) 123-45-67",
            "email": "info@ecommerce_platform.ru",
            "address": {
                "city": "Tashkent",
                "street": "Example Street, 1",
                "full": "Tashkent, Example Street, 1"
            },
        },
        "social": {
            "instagram": "#",
            "facebook": "#",
            "twitter": "#",
            "vk": "#",
        },
        "partners": [],
        "features": [],
        "about": {
            "title": "About Us",
            "description": "We are a modern fashion store.",
        },
        "django": {
            "debug": True,
            "allowed_hosts": ["*"],
            "secret_key": "django-insecure-your-secret-key-change-in-production",
            "time_zone": "Asia/Tashkent",
            "language_code": "ru",
            "languages": ["ru", "en", "uz"],
            "default_language": "ru",
        },
    }


# УБРАЛИ КЭШИРОВНИЕ - данные всегда берутся свежими из БД (админка имеет приоритет)
# Это гарантирует, что изменения в админке сразу отображаются на сайте


def get_config():
    """
    Получает конфигурацию БЕЗ кэширования - всегда свежие данные из БД
    Приоритет: админка > config.json (заглушка)
    """
    return load_config()


def reload_config():
    """
    Перезагружает конфигурацию (теперь не нужна, так как кэш убран, но оставляем для совместимости)
    """
    # Кэш убран, данные всегда свежие из БД
    return get_config()


def get_django_config():
    """
    Получает настройки Django из config.json
    """
    config = get_config()
    return config.get('django', {})

