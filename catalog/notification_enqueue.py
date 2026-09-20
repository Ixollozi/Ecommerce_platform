"""
Enqueue Telegram notification events into the transactional outbox and schedule Celery.
"""

import logging

from django.db.transaction import on_commit

from .models import NotificationOutbox, TelegramNotificationSettings
from .platform.context import get_current_site

logger = logging.getLogger(__name__)


def _site_payload(extra: dict | None = None) -> dict:
    payload = dict(extra or {})
    site = get_current_site()
    if site is not None:
        payload.setdefault('site_slug', site.slug)
    return payload


def _schedule_outbox(outbox_id: int, site_slug: str | None) -> None:
    from .tasks import process_notification_outbox

    on_commit(lambda: process_notification_outbox.delay(outbox_id, site_slug=site_slug))


def enqueue_order_placed(order_id: int) -> NotificationOutbox | None:
    cfg = TelegramNotificationSettings.get_active()
    if not cfg or not cfg.is_active or not cfg.notify_new_orders:
        return None
    site = get_current_site()
    site_slug = site.slug if site else None
    row = NotificationOutbox.objects.create(
        event_type=NotificationOutbox.EventType.ORDER_PLACED,
        payload=_site_payload({'order_id': order_id}),
        status=NotificationOutbox.Status.PENDING,
    )
    _schedule_outbox(row.id, site_slug)
    logger.debug('Enqueued order_placed outbox_id=%s order_id=%s site=%s', row.id, order_id, site_slug)
    return row


def enqueue_order_status_changed(order_id: int, old_status: str) -> NotificationOutbox | None:
    cfg = TelegramNotificationSettings.get_active()
    if not cfg or not cfg.is_active or not cfg.notify_status_changes:
        return None
    site = get_current_site()
    site_slug = site.slug if site else None
    row = NotificationOutbox.objects.create(
        event_type=NotificationOutbox.EventType.ORDER_STATUS_CHANGED,
        payload=_site_payload({'order_id': order_id, 'old_status': old_status}),
        status=NotificationOutbox.Status.PENDING,
    )
    _schedule_outbox(row.id, site_slug)
    return row


def enqueue_contact_message(contact_message_id: int) -> NotificationOutbox | None:
    cfg = TelegramNotificationSettings.get_active()
    if not cfg or not cfg.is_active or not cfg.notify_contact_messages:
        return None
    site = get_current_site()
    site_slug = site.slug if site else None
    row = NotificationOutbox.objects.create(
        event_type=NotificationOutbox.EventType.CONTACT_MESSAGE,
        payload=_site_payload({'contact_message_id': contact_message_id}),
        status=NotificationOutbox.Status.PENDING,
    )
    _schedule_outbox(row.id, site_slug)
    return row
