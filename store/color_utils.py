"""
Утилиты для интеллектуального распознавания, нормализации и отображения цветов товаров.
Поддерживает русский, узбекский и английский языки, составные названия,
дедупликацию и безопасные fallback-цвета (исключает ложное дублирование черного цвета).
"""
from __future__ import annotations

import re
from typing import Any

# Карта популярных цветов: {нормализованная подстрока: (hex_код, is_light, каноническое_имя)}
COLOR_PALETTE: list[tuple[str, str, bool, str]] = [
    # Черный / Темный
    ('черненый металл', '#2b2b2b', False, 'Черненый металл'),
    ('черненый', '#2b2b2b', False, 'Черненый'),
    ('темно-синий', '#1e3a5f', False, 'Темно-синий'),
    ('темно синий', '#1e3a5f', False, 'Темно-синий'),
    ('to\'q ko\'k', '#1e3a5f', False, 'To\'q ko\'k'),
    ('navy', '#1e3a5f', False, 'Navy'),
    ('черн', '#18181b', False, 'Черный'),
    ('qora', '#18181b', False, 'Qora'),
    ('black', '#18181b', False, 'Black'),
    ('графит', '#374151', False, 'Графит'),
    ('charcoal', '#374151', False, 'Charcoal'),
    ('антрацит', '#27272a', False, 'Антрацит'),

    # Белый / Светлый / Кремовый
    ('слоновая кость', '#fffff0', True, 'Слоновая кость'),
    ('айвори', '#fffff0', True, 'Айвори'),
    ('ivory', '#fffff0', True, 'Ivory'),
    ('молочн', '#fdfbf7', True, 'Молочный'),
    ('qaymoqrang', '#fdfbf7', True, 'Qaymoqrang'),
    ('кремов', '#fffdd0', True, 'Кремовый'),
    ('cream', '#fffdd0', True, 'Cream'),
    ('бел', '#ffffff', True, 'Белый'),
    ('oq', '#ffffff', True, 'Oq'),
    ('white', '#ffffff', True, 'White'),

    # Бежевый / Песочный
    ('бежев', '#d4b996', True, 'Бежевый'),
    ('bej', '#d4b996', True, 'Bej'),
    ('beige', '#d4b996', True, 'Beige'),
    ('песочн', '#e2c9a5', True, 'Песочный'),
    ('sand', '#e2c9a5', True, 'Sand'),
    ('нюд', '#e8d3c5', True, 'Нюд'),
    ('nude', '#e8d3c5', True, 'Nude'),

    # Серый / Стальной / Серебряный
    ('светло-серый', '#d1d5db', True, 'Светло-серый'),
    ('светло серый', '#d1d5db', True, 'Светло-серый'),
    ('och kulrang', '#d1d5db', True, 'Och kulrang'),
    ('серебр', '#c0c0c0', True, 'Серебряный'),
    ('kumush', '#c0c0c0', True, 'Kumush'),
    ('silver', '#c0c0c0', True, 'Silver'),
    ('стальн', '#94a3b8', False, 'Стальной'),
    ('po\'lat', '#94a3b8', False, 'Po\'lat'),
    ('steel', '#94a3b8', False, 'Steel'),
    ('сер', '#6b7280', False, 'Серый'),
    ('kulrang', '#6b7280', False, 'Kulrang'),
    ('grey', '#6b7280', False, 'Grey'),
    ('gray', '#6b7280', False, 'Gray'),

    # Синий / Голубой / Бирюзовый
    ('голуб', '#60a5fa', False, 'Голубой'),
    ('och ko\'k', '#60a5fa', False, 'Och ko\'k'),
    ('moviy', '#60a5fa', False, 'Moviy'),
    ('light blue', '#60a5fa', False, 'Light Blue'),
    ('бирюзов', '#14b8a6', False, 'Бирюзовый'),
    ('zangori', '#14b8a6', False, 'Zangori'),
    ('turquoise', '#14b8a6', False, 'Turquoise'),
    ('морская волна', '#0d9488', False, 'Морская волна'),
    ('джинсов', '#3b82f6', False, 'Джинсовый'),
    ('син', '#2563eb', False, 'Синий'),
    ('ko\'k', '#2563eb', False, 'Ko\'k'),
    ('kok', '#2563eb', False, 'Ko\'k'),
    ('blue', '#2563eb', False, 'Blue'),

    # Зеленый / Ментоловый / Мятный / Оливковый
    ('ментолов', '#a7f3d0', True, 'Ментоловый'),
    ('мятн', '#86efac', True, 'Мятный'),
    ('mint', '#a7f3d0', True, 'Mint'),
    ('оливков', '#808000', False, 'Оливковый'),
    ('zaytuntus', '#808000', False, 'Zaytuntus'),
    ('olive', '#808000', False, 'Olive'),
    ('хаки', '#6b705c', False, 'Хаки'),
    ('xaki', '#6b705c', False, 'Xaki'),
    ('khaki', '#6b705c', False, 'Khaki'),
    ('изумруд', '#059669', False, 'Изумрудный'),
    ('emerald', '#059669', False, 'Emerald'),
    ('зелен', '#16a34a', False, 'Зеленый'),
    ('yashil', '#16a34a', False, 'Yashil'),
    ('green', '#16a34a', False, 'Green'),

    # Коричневый / Шоколадный / Бронзовый / Медный
    ('шоколад', '#4a2c11', False, 'Шоколадный'),
    ('shokolad', '#4a2c11', False, 'Shokolad'),
    ('chocolate', '#4a2c11', False, 'Chocolate'),
    ('терракот', '#c2410c', False, 'Терракотовый'),
    ('terracotta', '#c2410c', False, 'Terracotta'),
    ('бронз', '#cd7f32', False, 'Бронзовый'),
    ('bronza', '#cd7f32', False, 'Bronza'),
    ('bronze', '#cd7f32', False, 'Bronze'),
    ('медн', '#b87333', False, 'Медный'),
    ('mis', '#b87333', False, 'Mis'),
    ('copper', '#b87333', False, 'Copper'),
    ('коричнев', '#78350f', False, 'Коричневый'),
    ('jigarrang', '#78350f', False, 'Jigarrang'),
    ('jigar rang', '#78350f', False, 'Jigarrang'),
    ('brown', '#78350f', False, 'Brown'),

    # Красный / Бордовый / Коралловый
    ('бордов', '#881337', False, 'Бордовый'),
    ('bordo', '#881337', False, 'Bordo'),
    ('burgundy', '#881337', False, 'Burgundy'),
    ('вишнев', '#9f1239', False, 'Вишневый'),
    ('коралл', '#f43f5e', False, 'Коралловый'),
    ('coral', '#f43f5e', False, 'Coral'),
    ('красн', '#dc2626', False, 'Красный'),
    ('qizil', '#dc2626', False, 'Qizil'),
    ('red', '#dc2626', False, 'Red'),

    # Розовый / Персиковый / Пудровый
    ('пудров', '#fbcfe8', True, 'Пудровый'),
    ('персиков', '#fdba74', True, 'Персиковый'),
    ('peach', '#fdba74', True, 'Peach'),
    ('розов', '#f472b6', True, 'Розовый'),
    ('pushti', '#f472b6', True, 'Pushti'),
    ('pink', '#f472b6', True, 'Pink'),

    # Желтый / Горчичный / Оранжевый / Золотой
    ('золот', '#eab308', True, 'Золотой'),
    ('tilla', '#eab308', True, 'Tilla'),
    ('gold', '#eab308', True, 'Gold'),
    ('горчичн', '#ca8a04', False, 'Горчичный'),
    ('mustard', '#ca8a04', False, 'Mustard'),
    ('оранжев', '#ea580c', False, 'Оранжевый'),
    ('sabzirang', '#ea580c', False, 'Sabzirang'),
    ('orange', '#ea580c', False, 'Orange'),
    ('лимон', '#fef08a', True, 'Лимонный'),
    ('желт', '#eab308', True, 'Желтый'),
    ('sariq', '#eab308', True, 'Sariq'),
    ('yellow', '#eab308', True, 'Yellow'),

    # Фиолетовый / Сиреневый / Лавандовый
    ('сиренев', '#c084fc', True, 'Сиреневый'),
    ('лаванд', '#e9d5ff', True, 'Лавандовый'),
    ('lavender', '#e9d5ff', True, 'Lavender'),
    ('фиолетов', '#7e22ce', False, 'Фиолетовый'),
    ('binafsha', '#7e22ce', False, 'Binafsha'),
    ('purple', '#7e22ce', False, 'Purple'),
    ('violet', '#7e22ce', False, 'Violet'),
]


# Дополнительные fallback-оттенки при отсутствии точного совпадения,
# чтобы разные цвета не сливались в одинаковый черный цвет.
_DISTINCT_FALLBACKS = [
    '#52525b',  # цинковый серый
    '#9a3412',  # теплый медный
    '#047857',  # хвойный
    '#1d4ed8',  # кобальт
    '#b45309',  # янтарь
    '#6d28d9',  # аметист
    '#0f766e',  # малахит
]


def resolve_single_color(raw_name: str, fallback_index: int = 0) -> dict[str, Any]:
    """
    Интеллектуально распознает цвет по его названию на русском, узбекском или английском.
    Возвращает dict с name, code, is_light, data_color.
    """
    clean_name = raw_name.strip()
    if not clean_name:
        return {'name': '', 'code': '#000000', 'is_light': False, 'data_color': ''}

    # Если уже передан HEX-код вида #fff или #3498db
    if re.match(r'^#[0-9a-fA-F]{3,8}$', clean_name):
        code = clean_name.lower()
        is_light = code in ('#ffffff', '#fff', '#fdfbf7', '#fffff0', '#f5f5f5', '#fafafa')
        return {
            'name': clean_name,
            'code': code,
            'is_light': is_light,
            'data_color': clean_name.lower(),
        }

    lower_name = clean_name.lower()

    # Проверяем совпадения в палитре
    for pattern, hex_code, is_light, canonical_name in COLOR_PALETTE:
        if pattern in lower_name:
            # Если имя в базе было просто «Черный», сохраняем его, а если сложная фраза («ментоловый»), капитализируем
            display_name = clean_name[0].upper() + clean_name[1:] if len(clean_name) > 1 else clean_name.upper()
            return {
                'name': display_name,
                'code': hex_code,
                'is_light': is_light,
                'data_color': lower_name,
            }

    # Если цвет не найден в палитре:
    # НЕ делаем его слепо черным #000000 (иначе два неизвестных цвета станут дубликатами черного).
    # Используем детерминированный оттенок из distinct fallbacks.
    idx = (abs(hash(lower_name)) + fallback_index) % len(_DISTINCT_FALLBACKS)
    fallback_code = _DISTINCT_FALLBACKS[idx]
    display_name = clean_name[0].upper() + clean_name[1:] if len(clean_name) > 1 else clean_name.upper()

    return {
        'name': display_name,
        'code': fallback_code,
        'is_light': False,
        'data_color': lower_name,
    }


def parse_product_colors(available_colors_str: str | None) -> list[dict[str, Any]]:
    """
    Парсит строку доступных цветов товара с дедупликацией и нормализацией.
    Пример: 'Черный, Белый, Синий' -> [
        {'name': 'Черный', 'code': '#18181b', 'is_light': False, 'data_color': 'черный'},
        ...
    ]
    Исключает дублирование названий и визуальных цветов.
    """
    if not available_colors_str:
        return []

    # Разделяем по запятой, точке с запятой или слэшу
    raw_tokens = re.split(r'[,;/|]+', str(available_colors_str))
    cleaned_tokens = [t.strip() for t in raw_tokens if t.strip()]

    result: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    used_codes: set[str] = set()

    for idx, token in enumerate(cleaned_tokens):
        norm_key = token.lower().strip()
        if norm_key in seen_names:
            continue
        seen_names.add(norm_key)

        color_info = resolve_single_color(token, fallback_index=idx)

        # Если такой hex-код уже был добавлен для ДРУГОГО цвета,
        # слегка сдвигаем fallback, чтобы кружки на карточке не выглядели идентичными дублями
        if color_info['code'] in used_codes:
            for alt_code in _DISTINCT_FALLBACKS:
                if alt_code not in used_codes:
                    color_info['code'] = alt_code
                    break

        used_codes.add(color_info['code'])
        result.append(color_info)

    return result
