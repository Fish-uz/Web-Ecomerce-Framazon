from .cart import Cart

def cart(request):
    cart_obj = Cart(request)
    # Sumamos las cantidades de cada item en el carrito
    total_qty = sum(item['quantity'] for item in cart_obj)
    return {
        'cart': cart_obj,
        'cart_total_count': total_qty
    }