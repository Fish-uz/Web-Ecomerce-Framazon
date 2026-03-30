from .cart import Cart

def cart(request):
    cart_obj = Cart(request)
    # Calculamos el total de items para el badge del navbar
    total_qty = sum(item['quantity'] for item in cart_obj)
    return {
        'cart': cart_obj,
        'cart_total_count': total_qty
    }