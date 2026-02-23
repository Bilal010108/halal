from django.db import transaction
from .models import Order, OrderItem
from django.core.exceptions import ValidationError

@transaction.atomic
def create_order_from_cart(user, phone_number, address):
    if not user.is_authenticated:
        raise ValidationError("Необходимо авторизоваться")

    cart = user.cart

    if not cart.items.exists():
        raise ValidationError("Корзина пуста")

    order = Order.objects.create(
        user=user,
        phone_number=phone_number,
        address=address
    )

    for item in cart.items.select_related('product'):
        OrderItem.objects.create(
            order=order,
            product=item.product,
            price=item.product.get_actual_price(),
            quantity=item.quantity
        )

    order.calculate_total()
    cart.items.all().delete()

    return order