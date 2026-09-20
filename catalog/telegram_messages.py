"""
Pure HTML message builders for Telegram (no I/O).
"""

from django.utils.html import escape

from .currency import get_store_currency
from .models import ContactMessage, Order


def format_new_order_message(order: Order) -> str:
    currency = get_store_currency()
    first_name = escape(str(order.first_name))
    last_name = escape(str(order.last_name))
    phone = escape(str(order.phone))
    city = escape(str(order.city))
    address = escape(str(order.address))
    postal_code = escape(str(order.postal_code)) if order.postal_code else ''
    notes = escape(str(order.notes)) if order.notes else ''

    message = f"""🛒 <b>НОВЫЙ ЗАКАЗ #{order.id}</b>

👤 <b>Клиент:</b>
• Имя: {first_name} {last_name}
• Телефон: {phone}

📍 <b>Адрес доставки:</b>
• Город: {city}
• Адрес: {address}
{f'• Индекс: {postal_code}' if postal_code else ''}

📦 <b>Товары:</b>
"""

    for item in order.items.all():
        product_name = escape(str(item.product.name))
        color = escape(str(item.color)) if item.color else ''
        price = f'{item.price:,.0f}'.replace(',', ' ')
        message += f'• {product_name} x{item.quantity}\n'
        if color:
            message += f'  Цвет: {color}\n'
        message += f'  Цена: {price} {currency}\n\n'

    total = f'{order.total:,.0f}'.replace(',', ' ')
    message += f'\n💰 <b>Итого: {total} {currency}</b>'

    if notes:
        message += f'\n\n📝 <b>Примечания:</b>\n{notes}'

    message += f"\n\n⏰ {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    return message


def format_status_change_message(order: Order, old_status: str | None) -> str:
    currency = get_store_currency()
    status_emojis = {
        'pending': '⏳',
        'processing': '🔄',
        'shipped': '📦',
        'delivered': '✅',
        'cancelled': '❌',
    }
    emoji = status_emojis.get(order.status, '📋')
    first_name = escape(str(order.first_name))
    last_name = escape(str(order.last_name))
    phone = escape(str(order.phone))
    status_display = escape(str(order.get_status_display()))

    message = f"""{emoji} <b>ИЗМЕНЕНИЕ СТАТУСА ЗАКАЗА #{order.id}</b>

👤 <b>Клиент:</b> {first_name} {last_name}
📞 <b>Телефон:</b> {phone}

<b>Статус:</b> {status_display}
"""

    if old_status and old_status != order.status:
        old_status_display = escape(str(dict(Order.STATUS_CHOICES).get(old_status, old_status)))
        message += f'<b>Предыдущий статус:</b> {old_status_display}\n'

    total = f'{order.total:,.0f}'.replace(',', ' ')
    message += f'\n💰 <b>Сумма:</b> {total} {currency}'
    message += f"\n⏰ {order.updated_at.strftime('%d.%m.%Y %H:%M')}"
    return message


def format_contact_message(contact: ContactMessage) -> str:
    name = escape(str(contact.name))
    email = escape(str(contact.email))
    phone = escape(str(contact.phone)) if contact.phone else 'Не указан'
    subject = escape(str(contact.get_subject_display()))
    body = escape(str(contact.message))

    return f"""📧 <b>НОВОЕ СООБЩЕНИЕ ИЗ КОНТАКТОВ</b>

👤 <b>От:</b> {name}
📧 <b>Email:</b> {email}
📞 <b>Телефон:</b> {phone}

📋 <b>Тема:</b> {subject}

💬 <b>Сообщение:</b>
{body}

⏰ {contact.created_at.strftime('%d.%m.%Y %H:%M')}"""
