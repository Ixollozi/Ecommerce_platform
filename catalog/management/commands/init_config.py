from django.core.management.base import BaseCommand
from catalog.models import (
    Config, StoreConfig, ContactConfig, SocialConfig, HeroConfig,
    Feature, AboutConfig, SEOConfig, ThemeConfig
)
from catalog.config_loader import load_config_from_file


class Command(BaseCommand):
    help = 'Инициализирует конфигурацию из config.json в базу данных (новые модели)'

    def handle(self, *args, **options):
        # Загружаем конфигурацию из файла
        config_data = load_config_from_file()
        
        if not config_data:
            self.stdout.write(self.style.ERROR('Файл config.json не найден или пуст'))
            return
        
        # Store
        store_data = config_data.get('catalog', {})
        if store_data:
            store, created = StoreConfig.objects.get_or_create(
                is_active=True,
                defaults={
                    'name': store_data.get('name', 'Fashion Store'),
                    'title': store_data.get('title', 'Fashion Store - Online Clothing Store'),
                    'description': store_data.get('description', ''),
                    'currency': store_data.get('currency', 'сум'),
                }
            )
            if not created:
                store.name = store_data.get('name', store.name)
                store.title = store_data.get('title', store.title)
                store.description = store_data.get('description', store.description)
                if 'currency' in store_data:
                    store.currency = store_data.get('currency') or store.currency
                store.save()
            self.stdout.write(self.style.SUCCESS(f'[OK] Настройки магазина: {"созданы" if created else "обновлены"}'))
        
        # Contact
        contact_data = config_data.get('contact', {})
        if contact_data:
            contact, created = ContactConfig.objects.get_or_create(
                is_active=True,
                defaults={
                    'phone': contact_data.get('phone', ''),
                    'email': contact_data.get('email', ''),
                    'address_city': contact_data.get('address', {}).get('city', ''),
                    'address_street': contact_data.get('address', {}).get('street', ''),
                    'address_full': contact_data.get('address', {}).get('full', ''),
                    'working_hours_weekdays': contact_data.get('working_hours', {}).get('weekdays', ''),
                    'working_hours_weekend': contact_data.get('working_hours', {}).get('weekend', ''),
                }
            )
            if not created:
                contact.phone = contact_data.get('phone', contact.phone)
                contact.email = contact_data.get('email', contact.email)
                if 'address' in contact_data:
                    contact.address_city = contact_data['address'].get('city', contact.address_city)
                    contact.address_street = contact_data['address'].get('street', contact.address_street)
                    contact.address_full = contact_data['address'].get('full', contact.address_full)
                if 'working_hours' in contact_data:
                    contact.working_hours_weekdays = contact_data['working_hours'].get('weekdays', contact.working_hours_weekdays)
                    contact.working_hours_weekend = contact_data['working_hours'].get('weekend', contact.working_hours_weekend)
                contact.save()
            self.stdout.write(self.style.SUCCESS(f'[OK] Контакты: {"созданы" if created else "обновлены"}'))
        
        # Social
        social_data = config_data.get('social', {})
        if social_data:
            social, created = SocialConfig.objects.get_or_create(
                is_active=True,
                defaults={
                    'instagram': social_data.get('instagram', '#'),
                    'facebook': social_data.get('facebook', '#'),
                    'twitter': social_data.get('twitter', '#'),
                    'vk': social_data.get('vk', '#'),
                    'telegram': social_data.get('telegram', '#'),
                    'whatsapp': social_data.get('whatsapp', '#'),
                }
            )
            if not created:
                social.instagram = social_data.get('instagram', social.instagram)
                social.facebook = social_data.get('facebook', social.facebook)
                social.twitter = social_data.get('twitter', social.twitter)
                social.vk = social_data.get('vk', social.vk)
                social.telegram = social_data.get('telegram', social.telegram)
                social.whatsapp = social_data.get('whatsapp', social.whatsapp)
                social.save()
            self.stdout.write(self.style.SUCCESS(f'[OK] Социальные сети: {"созданы" if created else "обновлены"}'))
        
        # Hero
        hero_data = config_data.get('hero', {})
        if hero_data:
            hero, created = HeroConfig.objects.get_or_create(
                is_active=True,
                defaults={
                    'title': hero_data.get('title', ''),
                    'subtitle': hero_data.get('subtitle', ''),
                    'button_text': hero_data.get('button_text', ''),
                }
            )
            if not created:
                hero.title = hero_data.get('title', hero.title)
                hero.subtitle = hero_data.get('subtitle', hero.subtitle)
                hero.button_text = hero_data.get('button_text', hero.button_text)
                hero.save()
            self.stdout.write(self.style.SUCCESS(f'[OK] Главный баннер: {"создан" if created else "обновлен"}'))
        
        # Features
        features_data = config_data.get('features', [])
        if features_data:
            Feature.objects.filter(is_active=True).delete()  # Удаляем старые
            for idx, feature_data in enumerate(features_data):
                Feature.objects.create(
                    icon=feature_data.get('icon', ''),
                    title=feature_data.get('title', ''),
                    description=feature_data.get('description', ''),
                    order=idx,
                    is_active=True
                )
            self.stdout.write(self.style.SUCCESS(f'[OK] Особенности: создано {len(features_data)} записей'))
        
        # About
        about_data = config_data.get('about', {})
        if about_data:
            values_str = '\n'.join(about_data.get('values', []))
            about, created = AboutConfig.objects.get_or_create(
                is_active=True,
                defaults={
                    'title': about_data.get('title', ''),
                    'description': about_data.get('description', ''),
                    'mission': about_data.get('mission', ''),
                    'vision': about_data.get('vision', ''),
                    'values': values_str,
                }
            )
            if not created:
                about.title = about_data.get('title', about.title)
                about.description = about_data.get('description', about.description)
                about.mission = about_data.get('mission', about.mission)
                about.vision = about_data.get('vision', about.vision)
                about.values = values_str
                about.save()
            self.stdout.write(self.style.SUCCESS(f'[OK] О нас: {"создано" if created else "обновлено"}'))
        
        # SEO
        seo_data = config_data.get('seo', {})
        if seo_data:
            seo, created = SEOConfig.objects.get_or_create(
                is_active=True,
                defaults={
                    'meta_title': seo_data.get('meta_title', ''),
                    'meta_description': seo_data.get('meta_description', ''),
                    'meta_keywords': seo_data.get('meta_keywords', ''),
                }
            )
            if not created:
                seo.meta_title = seo_data.get('meta_title', seo.meta_title)
                seo.meta_description = seo_data.get('meta_description', seo.meta_description)
                seo.meta_keywords = seo_data.get('meta_keywords', seo.meta_keywords)
                seo.save()
            self.stdout.write(self.style.SUCCESS(f'[OK] SEO настройки: {"созданы" if created else "обновлены"}'))
        
        # Theme
        theme_data = config_data.get('theme', {})
        if theme_data:
            theme, created = ThemeConfig.objects.get_or_create(
                is_active=True,
                defaults={
                    'primary_color': theme_data.get('primary_color', '#1976d2'),
                    'secondary_color': theme_data.get('secondary_color', '#ffa726'),
                    'text_color': theme_data.get('text_color', '#333'),
                    'background_color': theme_data.get('background_color', '#fff'),
                }
            )
            if not created:
                theme.primary_color = theme_data.get('primary_color', theme.primary_color)
                theme.secondary_color = theme_data.get('secondary_color', theme.secondary_color)
                theme.text_color = theme_data.get('text_color', theme.text_color)
                theme.background_color = theme_data.get('background_color', theme.background_color)
                theme.save()
            self.stdout.write(self.style.SUCCESS(f'[OK] Настройки темы: {"созданы" if created else "обновлены"}'))
        
        self.stdout.write(self.style.SUCCESS('\n[OK] Инициализация конфигурации завершена!'))

