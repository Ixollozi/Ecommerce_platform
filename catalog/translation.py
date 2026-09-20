"""
Настройки переводов для моделей
"""
from modeltranslation.translator import register, TranslationOptions
from .models import (
    Category, Product, Partner,
    StoreConfig, ContactConfig, HeroConfig, Feature,
    AboutConfig, SEOConfig, ProductFeatureConfig, AboutStat, FAQ
)


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'available_colors')


@register(Partner)
class PartnerTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(StoreConfig)
class StoreConfigTranslationOptions(TranslationOptions):
    fields = ('name', 'title', 'description')


@register(ContactConfig)
class ContactConfigTranslationOptions(TranslationOptions):
    fields = ('address_city', 'address_street', 'address_full', 'working_hours_weekdays', 'working_hours_weekend')


@register(HeroConfig)
class HeroConfigTranslationOptions(TranslationOptions):
    fields = ('title', 'subtitle', 'button_text')


@register(Feature)
class FeatureTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(AboutConfig)
class AboutConfigTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'mission', 'vision', 'values')


@register(SEOConfig)
class SEOConfigTranslationOptions(TranslationOptions):
    fields = ('meta_title', 'meta_description', 'meta_keywords')


@register(ProductFeatureConfig)
class ProductFeatureConfigTranslationOptions(TranslationOptions):
    fields = ('title', 'text')


@register(AboutStat)
class AboutStatTranslationOptions(TranslationOptions):
    fields = ('label',)


@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')
