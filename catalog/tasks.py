"""
Celery tasks: drain notification outbox and send to Telegram Bot API.
"""

from __future__ import annotations

import logging

import telebot
from celery import shared_task
from django.db import transaction

from .models import ContactMessage, NotificationOutbox, Order, TelegramNotificationSettings, TelegramSubscriber
from .platform.context import site_context
from .platform.registry import get_site
from .telegram_messages import (
    format_contact_message,
    format_new_order_message,
    format_status_change_message,
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 8


def _reschedule(outbox_id: int, attempts: int, site_slug: str | None) -> None:
    delay = min(300, 10 * (2 ** min(attempts, 5)))
    process_notification_outbox.apply_async(args=[outbox_id], kwargs={'site_slug': site_slug}, countdown=delay)


def _build_message(row: NotificationOutbox) -> tuple[str, bool]:
    if row.event_type == NotificationOutbox.EventType.ORDER_PLACED:
        order = Order.objects.prefetch_related('items__product').get(pk=row.payload.get('order_id'))
        return format_new_order_message(order), True

    if row.event_type == NotificationOutbox.EventType.ORDER_STATUS_CHANGED:
        order = Order.objects.prefetch_related('items__product').get(pk=row.payload.get('order_id'))
        return format_status_change_message(order, row.payload.get('old_status')), True

    if row.event_type == NotificationOutbox.EventType.CONTACT_MESSAGE:
        contact = ContactMessage.objects.get(pk=row.payload.get('contact_message_id'))
        return format_contact_message(contact), True

    return '', False


def _process_notification_outbox(outbox_id: int) -> None:
    try:
        with transaction.atomic():
            row = NotificationOutbox.objects.select_for_update().get(pk=outbox_id)
            if row.status != NotificationOutbox.Status.PENDING:
                return
            row.status = NotificationOutbox.Status.PROCESSING
            row.save(update_fields=['status', 'updated_at'])
    except NotificationOutbox.DoesNotExist:
        logger.warning('Outbox row missing id=%s', outbox_id)
        return

    cfg = TelegramNotificationSettings.get_active()
    token = cfg.resolved_bot_token() if cfg else ''

    def _fail_or_retry(msg: str) -> None:
        with transaction.atomic():
            row = NotificationOutbox.objects.select_for_update().get(pk=outbox_id)
            row.attempts += 1
            row.last_error = msg[:2000]
            if row.attempts >= MAX_ATTEMPTS:
                row.status = NotificationOutbox.Status.FAILED
            else:
                row.status = NotificationOutbox.Status.PENDING
            row.save(update_fields=['attempts', 'last_error', 'status', 'updated_at'])
            attempts = row.attempts
            is_failed = row.status == NotificationOutbox.Status.FAILED
            site_slug = row.payload.get('site_slug')
        if not is_failed:
            _reschedule(outbox_id, attempts, site_slug)
        else:
            logger.error('Outbox id=%s failed permanently: %s', outbox_id, msg)

    def _mark_sent(note: str = '') -> None:
        NotificationOutbox.objects.filter(pk=outbox_id).update(
            status=NotificationOutbox.Status.SENT,
            last_error=note[:2000],
        )

    if not cfg or not cfg.is_active:
        _mark_sent('skipped: channel inactive')
        return

    if not token:
        _fail_or_retry('Нет токена бота: укажите токен в админке или TELEGRAM_BOT_TOKEN.')
        return

    subscribers = list(TelegramSubscriber.objects.filter(is_active=True))
    if not subscribers:
        _mark_sent('skipped: no active subscribers')
        return

    try:
        text, allowed = _build_message(row)
    except Exception as exc:
        logger.exception('Outbox id=%s build message error', outbox_id)
        _fail_or_retry(f'build: {exc}')
        return

    if not allowed:
        _mark_sent('skipped: notification type disabled')
        return

    bot = telebot.TeleBot(token)
    try:
        for sub in subscribers:
            bot.send_message(chat_id=sub.telegram_chat_id, text=text, parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as exc:
        logger.warning('Telegram API error outbox=%s: %s', outbox_id, exc)
        _fail_or_retry(f'telegram: {exc}')
        return
    except Exception as exc:
        logger.exception('Unexpected send error outbox=%s', outbox_id)
        _fail_or_retry(f'send: {exc}')
        return

    _mark_sent('')
    logger.info('Outbox id=%s delivered to %s chats', outbox_id, len(subscribers))


@shared_task
def process_notification_outbox(outbox_id: int, site_slug: str | None = None) -> None:
    site = get_site(site_slug) if site_slug else None
    if site is not None:
        with site_context(site):
            _process_notification_outbox(outbox_id)
        return
    _process_notification_outbox(outbox_id)
