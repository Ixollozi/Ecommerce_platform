from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from catalog.models import Cart, CartItem


class Command(BaseCommand):
    help = 'Удаляет корзины, которые не обновлялись более 30 дней, и их элементы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Количество дней, после которых корзина считается устаревшей (по умолчанию: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, что будет удалено, без фактического удаления',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Вычисляем дату, до которой корзины считаются устаревшими
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Находим все корзины, которые не обновлялись более указанного количества дней
        old_carts = Cart.objects.filter(updated_at__lt=cutoff_date)
        
        cart_count = old_carts.count()
        
        if cart_count == 0:
            self.stdout.write(
                self.style.SUCCESS(f'Нет корзин старше {days} дней для удаления.')
            )
            return
        
        # Подсчитываем количество элементов корзины, которые будут удалены
        cart_items_count = CartItem.objects.filter(cart__in=old_carts).count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'РЕЖИМ ПРОВЕРКИ: Найдено {cart_count} корзин и {cart_items_count} элементов корзины '
                    f'старше {days} дней, которые будут удалены.'
                )
            )
            # Показываем примеры
            for cart in old_carts[:5]:
                items_in_cart = cart.items.count()
                self.stdout.write(
                    f'  - Корзина {cart.session_key} (обновлена: {cart.updated_at.strftime("%Y-%m-%d %H:%M")}), '
                    f'элементов: {items_in_cart}'
                )
            if cart_count > 5:
                self.stdout.write(f'  ... и еще {cart_count - 5} корзин')
            return
        
        # Удаляем корзины (CartItem удалятся автоматически благодаря CASCADE)
        deleted_carts = 0
        deleted_items = 0
        
        for cart in old_carts:
            items_count = cart.items.count()
            deleted_items += items_count
            cart.delete()  # Это также удалит все связанные CartItem благодаря CASCADE
            deleted_carts += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно удалено {deleted_carts} корзин и {deleted_items} элементов корзины '
                f'старше {days} дней.'
            )
        )
