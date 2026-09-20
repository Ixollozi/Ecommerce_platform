# Ecommerce Platform

Мультисайт-платформа интернет-магазинов на Django (host-based routing, темы, per-site SQLite).

Repo: https://github.com/Ixollozi/Ecommerce_platform

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
```

2. Активируйте виртуальное окружение:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте миграции:
```bash
python manage.py makemigrations
```

5. Выполните миграции:
```bash
python manage.py migrate
```

6. Создайте суперпользователя (опционально):
```bash
python manage.py createsuperuser
```

7. Загрузите примерные данные:
```bash
python manage.py load_sample_data
```

8. Запустите сервер:
```bash
python manage.py runserver
```

## Автоматическая очистка старых корзин

Система автоматически удаляет корзины, которые не обновлялись более 30 дней, вместе с их элементами (CartItem).

### Автоматическая очистка работает двумя способами:

1. **При каждом запросе к корзине** (с ограничением частоты - не чаще раза в час)
2. **Через management команду** (для ручного запуска или настройки cron)

### Ручной запуск очистки:

```bash
# Проверить, что будет удалено (без фактического удаления)
python manage.py cleanup_old_carts --dry-run

# Удалить корзины старше 30 дней
python manage.py cleanup_old_carts

# Удалить корзины старше указанного количества дней
python manage.py cleanup_old_carts --days 60
```

### Настройка периодической очистки через cron (Linux/Mac):

Добавьте в crontab для ежедневного запуска в 2:00 ночи:

```bash
crontab -e
```

Добавьте строку:
```
0 2 * * * cd /path/to/your/project && /path/to/venv/bin/python manage.py cleanup_old_carts
```

### Настройка периодической очистки через Task Scheduler (Windows):

1. Откройте "Планировщик заданий" (Task Scheduler)
2. Создайте новое задание
3. Настройте запуск команды:
   ```
   C:\path\to\venv\Scripts\python.exe C:\path\to\project\manage.py cleanup_old_carts
   ```
4. Установите расписание (например, ежедневно в 2:00)

API будет доступно по адресу: `http://127.0.0.1:8000/api/`

## API Endpoints

### Категории
- `GET /api/categories/` - Список всех категорий
- `GET /api/categories/{slug}/` - Детали категории

### Товары
- `GET /api/products/` - Список товаров
  - Параметры:
    - `category` - фильтр по slug категории
    - `min_price` - минимальная цена
    - `max_price` - максимальная цена
    - `search` - поиск по названию и описанию
    - `ordering` - сортировка (по умолчанию: `-created_at`)
- `GET /api/products/{slug}/` - Детали товара
- `GET /api/products/popular/` - Популярные товары

### Корзина
- `GET /api/cart/current/` - Получить текущую корзину
- `POST /api/cart/add_item/` - Добавить товар в корзину
  ```json
  {
    "product_id": 1,
    "quantity": 2,
    "size": "M",
    "color": "Черный"
  }
  ```
- `PUT /api/cart/update_item/` - Обновить количество товара
  ```json
  {
    "item_id": 1,
    "quantity": 3
  }
  ```
- `DELETE /api/cart/remove_item/?item_id=1` - Удалить товар из корзины
- `DELETE /api/cart/clear/` - Очистить корзину

### Заказы
- `GET /api/orders/` - Список заказов текущей сессии
- `POST /api/orders/` - Создать заказ
  ```json
  {
    "first_name": "Иван",
    "last_name": "Иванов",
    "email": "ivan@example.com",
    "phone": "+998901234567",
    "address": "Ташкент, ул. Примерная, д. 1",
    "city": "Ташкент",
    "postal_code": "100000",
    "payment_method": "card",
    "notes": "",
    "items": [
      {
        "product_id": 1,
        "quantity": 2,
        "size": "M",
        "color": "Черный"
      }
    ]
  }
  ```
- `GET /api/orders/{id}/` - Детали заказа

## Админ-панель

Доступна по адресу: `http://127.0.0.1:8000/admin/`

Используйте учетные данные суперпользователя для входа.

## Структура проекта

```
backend/
├── ecommerce_platform/          # Основной проект Django
│   ├── settings.py        # Настройки
│   ├── urls.py            # Главные URL
│   └── wsgi.py            # WSGI конфигурация
├── catalog/                 # Приложение магазина
│   ├── models.py          # Модели данных
│   ├── serializers.py     # Сериализаторы DRF
│   ├── views.py            # API представления
│   ├── urls.py            # URL маршруты API
│   └── admin.py           # Админ-панель
├── manage.py              # Управление Django
├── requirements.txt      # Зависимости
└── README.md             # Документация
```

## Модели данных

- **Category** - Категории товаров
- **Product** - Товары
- **ProductImage** - Изображения товаров
- **Cart** - Корзина покупок
- **CartItem** - Элементы корзины
- **Order** - Заказы
- **OrderItem** - Элементы заказа

## Интеграция с фронтендом

Для работы с API из фронтенда используйте fetch или axios:

```javascript
// Получить список товаров
fetch('http://127.0.0.1:8000/api/products/')
  .then(response => response.json())
  .then(data => console.log(data));

// Получить популярные товары
fetch('http://127.0.0.1:8000/api/products/popular/')
  .then(response => response.json())
  .then(data => console.log(data));

// Получить текущую корзину
fetch('http://127.0.0.1:8000/api/cart/current/')
  .then(response => response.json())
  .then(data => console.log(data));

// Добавить в корзину
fetch('http://127.0.0.1:8000/api/cart/add_item/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include', // Важно для работы с сессиями
  body: JSON.stringify({
    product_id: 1,
    quantity: 2,
    size: 'M',
    color: 'Черный'
  })
})
.then(response => response.json())
.then(data => console.log(data));

// Обновить количество товара в корзине
fetch('http://127.0.0.1:8000/api/cart/update_item/', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',
  body: JSON.stringify({
    item_id: 1,
    quantity: 3
  })
});

// Удалить товар из корзины
fetch('http://127.0.0.1:8000/api/cart/remove_item/?item_id=1', {
  method: 'DELETE',
  credentials: 'include'
});

// Создать заказ
fetch('http://127.0.0.1:8000/api/orders/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',
  body: JSON.stringify({
    first_name: 'Иван',
    last_name: 'Иванов',
    email: 'ivan@example.com',
    phone: '+998901234567',
    address: 'Ташкент, ул. Примерная, д. 1',
    city: 'Ташкент',
    postal_code: '100000',
    payment_method: 'card',
    notes: '',
    items: [
      {
        product_id: 1,
        quantity: 2,
        size: 'M',
        color: 'Черный'
      }
    ]
  })
})
.then(response => response.json())
.then(data => console.log('Заказ создан:', data));
```

**Важно:** Для работы с корзиной и заказами необходимо использовать `credentials: 'include'` в fetch, чтобы сохранялись сессии Django.

## Примечания

- CORS настроен для работы с локальным фронтендом
- Используется сессионная корзина (не требует аутентификации)
- В продакшене измените SECRET_KEY и настройте ALLOWED_HOSTS

