"""Product / category image display tags."""
from django import template

from catalog.media_urls import category_display_image_url, product_display_image_url

register = template.Library()


@register.filter(name="display_image")
def display_image(obj):
    """
    URL for cards and media.
    Works for Product (upload → URL → gallery) and Category (upload → URL).
    """
    if obj is None:
        return ""
    # Products have price; categories do not.
    if hasattr(obj, "price") or hasattr(obj, "images"):
        return product_display_image_url(obj)
    return category_display_image_url(obj)


@register.simple_tag
def product_image_url(product):
    return product_display_image_url(product)


@register.simple_tag
def category_image_url(category):
    return category_display_image_url(category)
