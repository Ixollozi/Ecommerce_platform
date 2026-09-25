# Ecommerce Platform

Мультисайт-платформа интернет-магазинов на Django: один процесс обслуживает много доменов (host-based routing), у каждого сайта свои тема, SQLite и media.

**Repo:** https://github.com/Ixollozi/Ecommerce_platform

## Архитектура

```
Browser → nginx (по домену) → gunicorn :9000 → ecommerce_platform
                                              ↓
                              catalog (модели, API, админка, витрина)
                                              ↓
                         sites/<slug>/{config.json, db.sqlite3, media/}
                         themes/<name>/...
                         sites/registry.json  (список сайтов и тем)
```

| Компонент | Назначение |
|-----------|------------|
| `ecommerce_platform/` | Django project (settings, urls, wsgi/asgi, celery) |
| `catalog/` | Приложение магазина (модели, API, админка, темы/платформа) |
| `themes/` | Витрины (main, front2, eshop, hero, wood, national, ceramics, meridian, …) |
| `sites/` | Runtime данные сайтов (**не в git**) |
| `sites.example/` | Пример registry и демо-конфигов |
| `scripts/` | Локальный запуск и проверки |

На VPS код живёт в `/var/www/platform` (git clone `main`). Под `/var/www` больше нет per-site клонов — только `platform/`.

Имена в коде: пакет **`ecommerce_platform`**, app **`catalog`**. Физические таблицы SQLite по-прежнему `store_*` (чтобы не ломать существующие БД).

## Локальный запуск (platform mode)

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# PLATFORM_MODE=1 уже в .env.example
```

Скопируйте пример сайтов:

```bash
# Windows PowerShell
Copy-Item -Recurse sites.example sites

# Linux/macOS
cp -r sites.example sites
```

Дальше:

```bash
python manage.py platform_migrate
python manage.py platform_bootstrap   # суперюзеры/базовый конфиг по сайтам, если нужно
python manage.py platform_runserver
# или: scripts/run_platform_local.ps1
```

Демо-хосты из `sites.example/registry.json` (например `*.localhost`) удобно открывать через `/etc/hosts` или встроенный mapping в браузере/прокси.

Проверки:

```bash
python scripts/verify_platform.py
python scripts/verify_all.py
```

### Одиночный сайт (без PLATFORM_MODE)

Можно работать с корневым `config.json` и `db.sqlite3`, выставив `PLATFORM_MODE=0` в `.env`, затем обычные `migrate` / `runserver`. Для мультисайта используйте platform mode.

Перед первым `migrate` на БД, которая ещё с app label `store`:

```bash
python manage.py relabel_store_app
python manage.py migrate
```

В platform mode это делает `platform_migrate` сам.

## Production (VPS)

- Код: `/var/www/platform` ← `git pull --ff-only origin main`
- Сервис: `systemctl restart platform` (gunicorn → `ecommerce_platform.wsgi:application`, `:9000`)
- Nginx: весь трафик домена (включая `/static` и `/media`) → `:9000`
- Обновление: `bash /root/update_all_sites.sh --full` или `bash /root/deploy_clothing_platform.sh`
- Новый сайт: `bash /root/deploy_new_site.sh`
- Логи app: `journalctl -u platform -n 100 --no-pager` / `-f` (формат с `site=` / `host=`; уровень `LOG_LEVEL` в `.env`)
- Логи nginx: `/var/log/nginx/<domain>_access.log`, `_error.log`

SSH (пример): `ssh -i <key> root@138.249.7.168`

## Полезные команды

```bash
python manage.py platform_migrate      # migrate по всем сайтам
python manage.py platform_bootstrap
python manage.py platform_runserver
python manage.py relabel_store_app     # store→catalog в django_migrations/contenttypes
python manage.py cleanup_old_carts [--dry-run] [--days 30]
python manage.py load_sample_data
python manage.py init_config
```

Корзины старше 30 дней чистятся командой `cleanup_old_carts` и при обращении к корзине (не чаще раза в час).

## API (кратко)

База: `/api/` (сессионная корзина — в fetch нужен `credentials: 'include'`).

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/categories/` | Категории |
| GET | `/api/products/` | Товары (`category`, `min_price`, `max_price`, `search`, `ordering`) |
| GET | `/api/products/{slug}/` | Товар |
| GET | `/api/products/popular/` | Популярные |
| GET | `/api/cart/current/` | Корзина |
| POST | `/api/cart/add_item/` | В корзину |
| PUT | `/api/cart/update_item/` | Количество |
| DELETE | `/api/cart/remove_item/?item_id=` | Убрать позицию |
| DELETE | `/api/cart/clear/` | Очистить |
| GET/POST | `/api/orders/` | Заказы / создать |
| GET | `/api/orders/{id}/` | Заказ |

Админка: `/admin/`.

## Модели (catalog)

Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, Partner, конфиги магазина/SEO/Telegram, FAQ, ContactMessage, уведомления.

## Структура репозитория

```
├── ecommerce_platform/     # Django project
├── catalog/                # app: models, API, admin, platform/*, management
├── themes/                 # витрины по темам
├── sites.example/          # пример registry + демо-сайты
├── templates/              # общие/фолбэк шаблоны
├── locale/                 # i18n
├── scripts/                # local run / verify
├── manage.py
├── requirements.txt
├── .env.example
└── config.json             # фолбэк для single-site режима
```

## Примечания

- Секреты и `sites/*/db.sqlite3` / media **не коммитить**.
- В проде задайте `DJANGO_SECRET_KEY`, отключите debug, держите `.env` только на сервере.
- Ключ `"store"` в `config.json` — секция настроек магазина (не имя Django-app).
