from django.db.models import Count, Q, Sum

from .currency import get_store_currency
from .models import Category, ContactMessage, Order, Partner, Product


def get_admin_index_context():
    """Dashboard stats with a small number of queries."""
    order_stats = Order.objects.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        processing=Count('id', filter=Q(status='processing')),
        delivered=Count('id', filter=Q(status='delivered')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    )
    revenue = (
        Order.objects.filter(status__in=['delivered', 'shipped', 'processing'])
        .aggregate(total=Sum('total'))['total']
        or 0
    )
    partner_stats = Partner.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(is_active=True)),
    )
    total_orders = order_stats['total'] or 0

    return {
        'total_products': Product.objects.count(),
        'total_orders': total_orders,
        'total_categories': Category.objects.count(),
        'total_partners': partner_stats['total'] or 0,
        'active_partners': partner_stats['active'] or 0,
        'latest_orders': list(Order.objects.order_by('-created_at')[:6]),
        'latest_products': list(Product.objects.order_by('-created_at')[:6]),
        'pending_orders': order_stats['pending'] or 0,
        'processing_orders': order_stats['processing'] or 0,
        'delivered_orders': order_stats['delivered'] or 0,
        'cancelled_orders': order_stats['cancelled'] or 0,
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'total_revenue': f'{revenue:.0f}',
        'orders_denom': max(total_orders, 1),
        'currency': get_store_currency(),
    }
