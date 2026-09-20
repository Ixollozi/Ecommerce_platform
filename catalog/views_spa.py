"""Отдаёт SPA: Django Templates + JSON bootstrap + ассеты из Vite manifest."""
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

from catalog.frontend_paths import spa_index_path
from catalog.spa_bootstrap import build_spa_bootstrap
from catalog.vite_manifest import get_spa_vite_assets


def spa(request):
    index_fs = spa_index_path()
    if index_fs is None:
        extra = (
            "<p>На сервере после сборки: <code>python manage.py collectstatic</code>.</p>"
            if not settings.DEBUG
            else ""
        )
        return HttpResponse(
            "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Витрина не собрана</title></head>"
            "<body style=\"font-family:sans-serif;padding:2rem;\">"
            "<h1>Фронтенд не найден</h1>"
            "<p>Выполните <code>python manage.py build_frontend</code> в каталоге проекта.</p>"
            f"{extra}"
            "</body></html>",
            status=503,
            content_type="text/html; charset=utf-8",
        )

    assets = get_spa_vite_assets()
    if not assets or not assets.get("js"):
        return HttpResponse(
            "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Нет manifest.json</title></head>"
            "<body style=\"font-family:sans-serif;padding:2rem;\">"
            "<h1>Нет Vite manifest</h1>"
            "<p>Пересоберите фронт: <code>python manage.py build_frontend</code>.</p>"
            "</body></html>",
            status=503,
            content_type="text/html; charset=utf-8",
        )

    bootstrap = build_spa_bootstrap(request)
    ctx = {
        "spa_js_urls": assets["js"],
        "spa_css_urls": assets.get("css") or [],
        "spa_bootstrap": bootstrap,
    }
    return render(request, "spa.html", ctx)
