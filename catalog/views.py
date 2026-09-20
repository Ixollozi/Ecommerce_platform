from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from .models import Category, Product, Cart, CartItem, Order, ContactMessage
from .serializers import (
    CategorySerializer, ProductSerializer, CartSerializer,
    CartItemSerializer, OrderSerializer, CreateOrderSerializer
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        
        # Фильтрация по категории
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Фильтрация по цене
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Поиск
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Сортировка
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        return queryset

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Популярные товары"""
        products = self.get_queryset().order_by('-rating', '-reviews_count')[:8]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        return Cart.objects.filter(session_key=session_key)

    def cleanup_old_carts(self):
        """
        Удаляет корзины, которые не обновлялись более 30 дней.
        Проверка выполняется не чаще раза в час для оптимизации.
        """
        cache_key = 'cart_cleanup_last_run'
        last_run = cache.get(cache_key)
        
        # Проверяем, не выполнялась ли очистка в последний час
        if last_run is not None:
            return
        
        # Устанавливаем флаг, что очистка выполняется (на 1 час)
        cache.set(cache_key, timezone.now(), 3600)
        
        try:
            # Вычисляем дату, до которой корзины считаются устаревшими (30 дней)
            cutoff_date = timezone.now() - timedelta(days=30)
            
            # Находим все корзины, которые не обновлялись более 30 дней
            old_carts = Cart.objects.filter(updated_at__lt=cutoff_date)
            
            # Удаляем корзины (CartItem удалятся автоматически благодаря CASCADE)
            deleted_count = old_carts.count()
            if deleted_count > 0:
                old_carts.delete()
                # Логируем в консоль (в продакшене можно использовать logger)
                print(f"Очищено {deleted_count} старых корзин (старше 30 дней)")
        except Exception as e:
            # В случае ошибки сбрасываем флаг, чтобы попробовать снова
            cache.delete(cache_key)
            print(f"Ошибка при очистке старых корзин: {e}")

    def get_or_create_cart(self):
        # Автоматически очищаем старые корзины при каждом запросе (с ограничением частоты)
        self.cleanup_old_carts()
        
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.create()
            session_key = self.request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Получить текущую корзину"""
        cart = self.get_or_create_cart()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Добавить товар в корзину"""
        try:
            cart = self.get_or_create_cart()
            product_id = request.data.get('product_id')
            
            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                product_id = int(product_id)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'product_id must be a valid integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            quantity = int(request.data.get('quantity', 1))
            size = request.data.get('size', '')
            color = request.data.get('color', '')

            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response(
                    {'error': f'Product with id {product_id} not found or is inactive'},
                    status=status.HTTP_404_NOT_FOUND
                )

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                size=size,
                color=color,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            serializer = CartItemSerializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['put'])
    def update_item(self, request):
        """Обновить количество товара в корзине"""
        cart = self.get_or_create_cart()
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))

        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.quantity = quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        """Удалить товар из корзины"""
        cart = self.get_or_create_cart()
        item_id = request.query_params.get('item_id')

        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Очистить корзину"""
        cart = self.get_or_create_cart()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        session_key = self.request.session.session_key
        if not session_key:
            return Order.objects.none()
        return Order.objects.filter(session_key=session_key)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateOrderSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Очистка корзины после создания заказа
        session_key = request.session.session_key
        if session_key:
            try:
                cart = Cart.objects.get(session_key=session_key)
                cart.items.all().delete()
            except Cart.DoesNotExist:
                pass
        
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_contact_message(request):
    """API endpoint для отправки сообщений из формы контактов"""
    try:
        name = request.data.get('name')
        email = request.data.get('email')
        phone = request.data.get('phone', '')
        subject = request.data.get('subject')
        message = request.data.get('message')

        # Валидация обязательных полей
        if not name or not email or not subject or not message:
            return Response(
                {'error': 'Все обязательные поля должны быть заполнены'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Создание сообщения
        contact_message = ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )

        # Отправка уведомления в Telegram
        try:
            from .notification_enqueue import enqueue_contact_message

            enqueue_contact_message(contact_message.id)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Ошибка постановки уведомления о сообщении из контактов в очередь: {e}')

        return Response(
            {'success': True, 'message': 'Сообщение успешно отправлено'},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

