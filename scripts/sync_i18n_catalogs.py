# -*- coding: utf-8 -*-
"""Extract msgids from themes/store and fill locale PO catalogs for ru/en/uz."""
from __future__ import annotations

import re
import time
from pathlib import Path

import polib
from deep_translator import GoogleTranslator

ROOT = Path(__file__).resolve().parents[1]
LOCALE = ROOT / "locale"

TRANS_PATTERNS = [
    re.compile(r"""\{%\s*trans\s+["'](.+?)["']\s*%\}""", re.S),
    re.compile(r"""\{%\s*blocktrans[^%]*%\}(.+?)\{%\s*endblocktrans\s*%\}""", re.S),
    re.compile(r'''\b_\(\s*"""(.+?)"""\s*\)''', re.S),
    re.compile(r"""\b_\(\s*'''(.+?)'''\s*\)""", re.S),
    re.compile(r"""\b_\(\s*["'](.+?)["']\s*\)""", re.S),
    re.compile(r'''\bgettext\(\s*"""(.+?)"""\s*\)''', re.S),
    re.compile(r"""\bgettext\(\s*["'](.+?)["']\s*\)""", re.S),
    re.compile(r'''\bgettext_lazy\(\s*"""(.+?)"""\s*\)''', re.S),
    re.compile(r"""\bgettext_lazy\(\s*["'](.+?)["']\s*\)""", re.S),
]

SCAN_DIRS = [
    ROOT / "themes",
    ROOT / "catalog",
    ROOT / "templates",
]
SKIP_PARTS = {"venv", "node_modules", ".git", "static", "migrations", "__pycache__", "frontend"}


def looks_cyrillic(s: str) -> bool:
    return bool(re.search(r"[\u0400-\u04FF]", s))


def normalize(s: str) -> str:
    s = s.replace("\\n", "\n").replace("\\t", "\t")
    s = re.sub(r"\s+", " ", s.strip())
    return s


def extract_msgids() -> set[str]:
    found: set[str] = set()
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if any(p in SKIP_PARTS for p in path.parts):
                continue
            if path.suffix.lower() not in {".html", ".py", ".txt"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            for pat in TRANS_PATTERNS:
                for m in pat.finditer(text):
                    msg = normalize(m.group(1))
                    # skip template vars inside blocktrans leftovers
                    if "{{" in msg or "{%" in msg:
                        continue
                    if msg and len(msg) < 500:
                        found.add(msg)
    return found


def load_or_create(lang: str) -> polib.POFile:
    path = LOCALE / lang / "LC_MESSAGES" / "django.po"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        po = polib.pofile(str(path))
    else:
        po = polib.POFile()
        po.metadata = {
            "Project-Id-Version": "clothing_shop",
            "Language": lang,
            "MIME-Version": "1.0",
            "Content-Type": "text/plain; charset=UTF-8",
            "Content-Transfer-Encoding": "8bit",
        }
    return po


def ensure_entry(po: polib.POFile, msgid: str) -> polib.POEntry:
    entry = po.find(msgid)
    if entry is None:
        entry = polib.POEntry(msgid=msgid, msgstr="")
        po.append(entry)
    return entry


# High-quality seeds for common UI (avoid API for these)
SEED_EN_FROM_RU = {
    "Каталог": "Catalog",
    "О нас": "About us",
    "Контакты": "Contacts",
    "Главная": "Home",
    "Корзина": "Cart",
    "Доставка": "Delivery",
    "Частые вопросы": "FAQ",
    "Переключение языка": "Language switcher",
    "Язык": "Language",
    "Перейти к содержимому": "Skip to content",
    "На главную": "Go to homepage",
    "Основная навигация": "Main navigation",
    "Все": "All",
    "Акция": "Sale",
    "Хит": "Hit",
    "В корзину": "Add to cart",
    "Добавить в корзину": "Add to cart",
    "Оформить заказ": "Checkout",
    "Итого": "Total",
    "Цена": "Price",
    "Количество": "Quantity",
    "Удалить": "Remove",
    "Пустая корзина": "Your cart is empty",
    "Продолжить покупки": "Continue shopping",
    "Поиск": "Search",
    "Фильтры": "Filters",
    "Сортировка": "Sort",
    "Новинка": "New",
    "В наличии": "In stock",
    "Нет в наличии": "Out of stock",
    "Описание": "Description",
    "Характеристики": "Specifications",
    "Отзывы": "Reviews",
    "Похожие товары": "Related products",
    "Миниатюры": "Thumbnails",
    "Валюта": "Currency",
    "Сумма": "Amount",
    "Телефон": "Phone",
    "Адрес": "Address",
    "Имя": "Name",
    "Фамилия": "Last name",
    "Город": "City",
    "Комментарий": "Comment",
    "Отправить": "Send",
    "Назад": "Back",
    "Далее": "Next",
    "Закрыть": "Close",
    "Меню": "Menu",
    "Партнеры": "Partners",
    "Доставка и оплата": "Delivery and payment",
    "Возврат товара": "Returns",
    "О компании": "Company",
    "Покупателям": "For customers",
    "Смотреть каталог": "View catalog",
    "Смотреть каталог →": "View catalog →",
    "Перейти в корзину": "Go to cart",
    "Хлебные крошки": "Breadcrumbs",
    "Магазин": "Store",
    "Товар": "Product",
    "Товары": "Products",
    "Страница не найдена": "Page not found",
    "Такой страницы не существует": "This page does not exist",
    "На главную": "Home",
    "О мастерской": "About the workshop",
}

SEED_UZ_FROM_RU = {
    "Каталог": "Katalog",
    "О нас": "Biz haqimizda",
    "Контакты": "Aloqa",
    "Главная": "Bosh sahifa",
    "Корзина": "Savat",
    "Доставка": "Yetkazib berish",
    "Частые вопросы": "Ko‘p so‘raladigan savollar",
    "Переключение языка": "Tilni almashtirish",
    "Язык": "Til",
    "Перейти к содержимому": "Kontentga o‘tish",
    "На главную": "Bosh sahifaga",
    "Основная навигация": "Asosiy navigatsiya",
    "Все": "Barchasi",
    "Акция": "Aksiya",
    "Хит": "Hit",
    "В корзину": "Savatga",
    "Добавить в корзину": "Savatga qo‘shish",
    "Оформить заказ": "Buyurtma berish",
    "Итого": "Jami",
    "Цена": "Narx",
    "Количество": "Miqdor",
    "Удалить": "O‘chirish",
    "Пустая корзина": "Savat bo‘sh",
    "Продолжить покупки": "Xaridni davom ettirish",
    "Поиск": "Qidiruv",
    "Фильтры": "Filtrlar",
    "Сортировка": "Saralash",
    "Новинка": "Yangilik",
    "В наличии": "Mavjud",
    "Нет в наличии": "Mavjud emas",
    "Описание": "Tavsif",
    "Характеристики": "Xususiyatlar",
    "Отзывы": "Sharhlar",
    "Похожие товары": "O‘xshash mahsulotlar",
    "Миниатюры": "Miniatyuralar",
    "Телефон": "Telefon",
    "Адрес": "Manzil",
    "Имя": "Ism",
    "Фамилия": "Familiya",
    "Город": "Shahar",
    "Комментарий": "Izoh",
    "Отправить": "Yuborish",
    "Назад": "Orqaga",
    "Далее": "Keyingi",
    "Закрыть": "Yopish",
    "Меню": "Menyu",
    "Партнеры": "Hamkorlar",
    "Доставка и оплата": "Yetkazib berish va to‘lov",
    "Возврат товара": "Qaytarish",
    "О компании": "Kompaniya haqida",
    "Покупателям": "Xaridorlarga",
    "Смотреть каталог": "Katalogni ko‘rish",
    "Смотреть каталог →": "Katalogni ko‘rish →",
    "Перейти в корзину": "Savatga o‘tish",
    "Хлебные крошки": "Navigatsiya yo‘li",
    "Магазин": "Do‘kon",
    "Товар": "Mahsulot",
    "Товары": "Mahsulotlar",
    "Страница не найдена": "Sahifa topilmadi",
    "Такой страницы не существует": "Bunday sahifa mavjud emas",
    "О мастерской": "Ustaxona haqida",
}

SEED_RU_FROM_EN = {
    "Home": "Главная",
    "Catalog": "Каталог",
    "About": "О нас",
    "About us": "О нас",
    "Contact": "Контакты",
    "Contacts": "Контакты",
    "Cart": "Корзина",
    "Delivery": "Доставка",
    "FAQ": "Частые вопросы",
    "Search": "Поиск",
    "Add to Cart": "В корзину",
    "Add to cart": "В корзину",
    "Checkout": "Оформить заказ",
    "Total": "Итого",
    "Price": "Цена",
    "Quantity": "Количество",
    "Color": "Цвет",
    "Remove": "Удалить",
    "Continue shopping": "Продолжить покупки",
    "View Catalog": "Смотреть каталог",
    "View catalog": "Смотреть каталог",
    "In stock": "В наличии",
    "Out of stock": "Нет в наличии",
    "Description": "Описание",
    "Reviews": "Отзывы",
    "Related products": "Похожие товары",
    "Filter": "Фильтр",
    "Filters": "Фильтры",
    "Sort": "Сортировка",
    "New": "Новинка",
    "Sale": "Акция",
    "Phone": "Телефон",
    "Address": "Адрес",
    "Name": "Имя",
    "Email": "Email",
    "City": "Город",
    "Send": "Отправить",
    "Back": "Назад",
    "Next": "Далее",
    "Close": "Закрыть",
    "Menu": "Меню",
    "Partners": "Партнеры",
    "Language": "Язык",
    "Product": "Товар",
    "Products": "Товары",
    "Store": "Магазин",
    "All": "Все",
    "pcs": "шт",
    "sum": "сум",
    "Cost": "Стоимость",
    "from": "от",
    "free for orders over": "бесплатно при заказе от",
}

SEED_UZ_FROM_EN = {
    "Home": "Bosh sahifa",
    "Catalog": "Katalog",
    "About": "Biz haqimizda",
    "About us": "Biz haqimizda",
    "Contact": "Aloqa",
    "Contacts": "Aloqa",
    "Cart": "Savat",
    "Delivery": "Yetkazib berish",
    "FAQ": "Savol-javob",
    "Search": "Qidiruv",
    "Add to Cart": "Savatga",
    "Add to cart": "Savatga qo‘shish",
    "Checkout": "Buyurtma berish",
    "Total": "Jami",
    "Price": "Narx",
    "Quantity": "Miqdor",
    "Color": "Rang",
    "Remove": "O‘chirish",
    "Continue shopping": "Xaridni davom ettirish",
    "View Catalog": "Katalogni ko‘rish",
    "View catalog": "Katalogni ko‘rish",
    "In stock": "Mavjud",
    "Out of stock": "Mavjud emas",
    "Description": "Tavsif",
    "Reviews": "Sharhlar",
    "Related products": "O‘xshash mahsulotlar",
    "Filter": "Filtr",
    "Filters": "Filtrlar",
    "Sort": "Saralash",
    "New": "Yangilik",
    "Sale": "Aksiya",
    "Phone": "Telefon",
    "Address": "Manzil",
    "Name": "Ism",
    "City": "Shahar",
    "Send": "Yuborish",
    "Back": "Orqaga",
    "Next": "Keyingi",
    "Close": "Yopish",
    "Menu": "Menyu",
    "Partners": "Hamkorlar",
    "Language": "Til",
    "Product": "Mahsulot",
    "Products": "Mahsulotlar",
    "Store": "Do‘kon",
    "All": "Barchasi",
    "pcs": "dona",
    "sum": "so‘m",
    "Cost": "Narxi",
    "from": "dan",
    "free for orders over": "undan oshsa bepul",
}


class TranslatorCache:
    def __init__(self):
        self.cache: dict[tuple[str, str, str], str] = {}
        self.clients = {
            ("ru", "en"): GoogleTranslator(source="ru", target="en"),
            ("ru", "uz"): GoogleTranslator(source="ru", target="uz"),
            ("en", "ru"): GoogleTranslator(source="en", target="ru"),
            ("en", "uz"): GoogleTranslator(source="en", target="uz"),
        }
        self.fail = 0

    def translate(self, text: str, source: str, target: str) -> str:
        key = (source, target, text)
        if key in self.cache:
            return self.cache[key]
        if self.fail > 20:
            return ""
        try:
            client = self.clients[(source, target)]
            out = client.translate(text)
            time.sleep(0.05)
            self.cache[key] = out or ""
            return self.cache[key]
        except Exception:
            self.fail += 1
            return ""


def fill_msgstr(msgid: str, lang: str, tr: TranslatorCache) -> str:
    if not msgid.strip():
        return ""
    cyr = looks_cyrillic(msgid)

    if lang == "ru":
        if cyr:
            return ""  # identity
        if msgid in SEED_RU_FROM_EN:
            return SEED_RU_FROM_EN[msgid]
        return tr.translate(msgid, "en", "ru")

    if lang == "en":
        if not cyr:
            return ""  # identity for English msgids
        if msgid in SEED_EN_FROM_RU:
            return SEED_EN_FROM_RU[msgid]
        return tr.translate(msgid, "ru", "en")

    if lang == "uz":
        if cyr:
            if msgid in SEED_UZ_FROM_RU:
                return SEED_UZ_FROM_RU[msgid]
            return tr.translate(msgid, "ru", "uz")
        if msgid in SEED_UZ_FROM_EN:
            return SEED_UZ_FROM_EN[msgid]
        return tr.translate(msgid, "en", "uz")

    return ""


def main():
    msgids = extract_msgids()
    print(f"extracted {len(msgids)} msgids")
    tr = TranslatorCache()

    for lang in ("ru", "en", "uz"):
        po = load_or_create(lang)
        existing = {e.msgid for e in po}
        added = 0
        filled = 0
        for msgid in sorted(msgids):
            entry = ensure_entry(po, msgid)
            if msgid not in existing:
                added += 1
            if not (entry.msgstr or "").strip():
                val = fill_msgstr(msgid, lang, tr)
                if val:
                    entry.msgstr = val
                    entry.fuzzy = False
                    filled += 1
        # also fill previously empty entries even if not in extract
        for entry in po:
            if entry.msgid and not (entry.msgstr or "").strip() and not entry.obsolete:
                val = fill_msgstr(entry.msgid, lang, tr)
                if val:
                    entry.msgstr = val
                    entry.fuzzy = False
                    filled += 1

        out = LOCALE / lang / "LC_MESSAGES" / "django.po"
        po.save(str(out))
        mo = LOCALE / lang / "LC_MESSAGES" / "django.mo"
        po.save_as_mofile(str(mo))
        print(f"{lang}: entries={len(po)} added={added} filled={filled} -> {out}")


if __name__ == "__main__":
    main()
