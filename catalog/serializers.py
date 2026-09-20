from rest_framework import serializers
from .models import Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, ContactMessage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'description']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    images = ProductImageSerializer(many=True, read_only=True)
    discount_percent = serializers.SerializerMethodField()
    image_display = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'old_price',
            'category', 'category_id', 'image', 'image_url', 'image_display',
            'available_colors', 'stock', 'is_active',
            'rating', 'reviews_count', 'images', 'discount_percent', 'created_at'
        ]

    def get_discount_percent(self, obj):
        if obj.old_price and obj.old_price > obj.price:
            discount = ((obj.old_price - obj.price) / obj.old_price) * 100
            return round(discount, 0)
        return 0

    def get_image_display(self, obj):
        """Uploaded primary → external URL → first gallery image."""
        from .media_urls import product_display_image_url

        url = product_display_image_url(obj)
        if not url:
            return None
        request = self.context.get('request')
        if request and url.startswith('/'):
            return request.build_absolute_uri(url)
        return url


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    total = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_id', 'quantity', 'color', 'total'
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    items_count = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'session_key', 'items', 'total', 'items_count', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'color', 'total']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'session_key', 'first_name', 'last_name', 'email', 'phone',
            'address', 'city', 'postal_code', 'total', 'status', 'status_display',
            'payment_method', 'payment_method_display', 'notes', 'items',
            'created_at', 'updated_at'
        ]


class CreateOrderSerializer(serializers.ModelSerializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )

    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'address',
            'city', 'postal_code', 'payment_method', 'notes', 'items'
        ]
        extra_kwargs = {
            'last_name': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True},
            'postal_code': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        
        if not items_data:
            raise serializers.ValidationError({'items': 'Корзина пуста. Невозможно создать заказ без товаров.'})
        
        # Устанавливаем значения по умолчанию для необязательных полей
        if not validated_data.get('last_name'):
            validated_data['last_name'] = ''

        if not validated_data.get('email') or validated_data.get('email') == '':
            validated_data['email'] = 'no-email@example.com'  # Временный email, так как поле обязательное в модели
        
        if not validated_data.get('payment_method') or validated_data.get('payment_method') == '':
            validated_data['payment_method'] = 'cash'  # По умолчанию наличные
        
        session_key = self.context['request'].session.session_key
        
        if not session_key:
            self.context['request'].session.create()
            session_key = self.context['request'].session.session_key

        validated_data['session_key'] = session_key
        
        # Подсчет общей суммы
        total = 0
        for item_data in items_data:
            product_id = item_data.get('product_id')
            if not product_id:
                raise serializers.ValidationError({'items': 'Не указан ID товара'})
            
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                raise serializers.ValidationError({'items': f'Товар с ID {product_id} не найден или неактивен'})
            
            quantity = item_data.get('quantity', 1)
            if quantity <= 0:
                raise serializers.ValidationError({'items': 'Количество товара должно быть больше 0'})
            
            total += product.price * quantity

        validated_data['total'] = total
        order = Order.objects.create(**validated_data)

        # Создание элементов заказа
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                price=product.price,
                size=item_data.get('size', ''),
                color=item_data.get('color', '')
            )
        
        # Обновляем заказ из БД, чтобы убедиться, что товары связаны
        order.refresh_from_db()
        try:
            from .notification_enqueue import enqueue_order_placed

            enqueue_order_placed(order.id)
        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                'Ошибка постановки уведомления о заказе #%s в очередь: %s',
                order.id,
                e,
                exc_info=True,
            )

        return order


class ContactMessageSerializer(serializers.ModelSerializer):
    subject_display = serializers.CharField(source='get_subject_display', read_only=True)

    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'subject_display', 'message', 'is_read', 'created_at', 'updated_at']
        read_only_fields = ['is_read', 'created_at', 'updated_at']

