"""
Middleware для гарантированного сохранения языка в сессии
"""
from django.utils import translation
from django.conf import settings


class LanguageSessionMiddleware:
    """
    Middleware для гарантированного сохранения языка в сессии
    Работает вместе с LocaleMiddleware
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # После обработки запроса сохраняем текущий язык в сессии
        if hasattr(request, 'session') and hasattr(request, 'LANGUAGE_CODE'):
            current_language = translation.get_language()
            if current_language and current_language in dict(settings.LANGUAGES):
                # Сохраняем язык в сессии для следующего запроса
                request.session['django_language'] = current_language
                request.session.modified = True
        
        return response

