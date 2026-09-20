"""
Единая страница конфигурации для админ-панели
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from .models import (
    StoreConfig, ContactConfig, SocialConfig, HeroConfig,
    Feature, AboutConfig, SEOConfig, ThemeConfig
)


def unified_config_view(request):
    """
    Единая страница конфигурации со всеми настройками
    """
    # Получаем активные конфиги
    store_config = StoreConfig.objects.filter(is_active=True).first()
    if not store_config:
        store_config = StoreConfig.objects.first()
    
    contact_config = ContactConfig.objects.filter(is_active=True).first()
    if not contact_config:
        contact_config = ContactConfig.objects.first()
    
    social_config = SocialConfig.objects.filter(is_active=True).first()
    if not social_config:
        social_config = SocialConfig.objects.first()
    
    hero_config = HeroConfig.objects.filter(is_active=True).first()
    if not hero_config:
        hero_config = HeroConfig.objects.first()
    
    about_config = AboutConfig.objects.filter(is_active=True).first()
    if not about_config:
        about_config = AboutConfig.objects.first()
    
    seo_config = SEOConfig.objects.filter(is_active=True).first()
    if not seo_config:
        seo_config = SEOConfig.objects.first()
    
    theme_config = ThemeConfig.objects.filter(is_active=True).first()
    if not theme_config:
        theme_config = ThemeConfig.objects.first()
    
    features = Feature.objects.filter(is_active=True).order_by('order', 'title')
    
    context = {
        **admin.site.each_context(request),
        'title': 'Конфигурация сайта',
        'store_config': store_config,
        'contact_config': contact_config,
        'social_config': social_config,
        'hero_config': hero_config,
        'about_config': about_config,
        'seo_config': seo_config,
        'theme_config': theme_config,
        'features': features,
    }
    
    return render(request, 'admin/unified_config.html', context)


