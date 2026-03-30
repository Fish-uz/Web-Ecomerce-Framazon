from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import JsonResponse
from django.db.models import Q
from django.utils.text import slugify
from .models import Category, Product, Order, OrderItem
from .forms import OrderCreateForm, ProductForm, CartAddProductForm
from .cart import Cart
from django.contrib import messages

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'shop/product/list.html', {
        'category': category, 
        'categories': categories, 
        'products': products, 
        'search_query': search_query
    })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    cart_product_form = CartAddProductForm()
    return render(request, 'shop/product/detail.html', {
        'product': product, 
        'cart_product_form': cart_product_form
    })

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                 quantity=cd['quantity'],
                 override_quantity=cd['override'])
    
    # Esto te devuelve a la página donde estabas (la lista o el detalle)
    return redirect(request.META.get('HTTP_REFERER', 'shop:product_list'))

def cart_detail(request):
    cart = Cart(request)
    # CORRECCIÓN: Ruta con prefijo shop/
    return render(request, 'shop/cart/detail.html', {'cart': cart})

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:cart_detail')

@login_required
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'])
            cart.clear()
            # CORRECCIÓN: Ruta con prefijo shop/
            return render(request, 'shop/order/created.html', {'order': order})
    else:
        form = OrderCreateForm()
    # CORRECCIÓN: Ruta con prefijo shop/
    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    # CORRECCIÓN: Ruta con prefijo shop/
    return render(request, 'shop/order/my_orders.html', {'orders': orders})

@login_required
def user_profile(request):
    # Pedidos que NO han sido entregados ni cancelados (están en camino)
    active_orders = Order.objects.filter(user=request.user).exclude(status__in=['delivered', 'canceled'])
    
    # Todo el historial (para el contador y la pestaña de historial)
    order_history = Order.objects.filter(user=request.user)
    
    # PRODUCTOS PUBLICADOS (Tus ventas)
    my_products = Product.objects.filter(vendedor=request.user) 
    
    context = {
        'active_orders': active_orders,
        'order_history': order_history,
        'my_products': my_products,
    }
    return render(request, 'shop/user/profile.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo_producto = form.save(commit=False)
            nuevo_producto.vendedor = request.user
            nuevo_producto.save()
            
            # Mensaje de éxito
            messages.success(request, '¡Producto publicado con éxito!')
            
            # Redirigimos al perfil añadiendo un parámetro en la URL para activar la pestaña
            return redirect('/profile/?tab=ventas') 
        else:
            messages.error(request, 'Hubo un error al cargar el producto. Revisa los datos.')
    else:
        form = ProductForm()
    
    return render(request, 'shop/product/create.html', {'form': form})

def register(request):
    # SI EL USUARIO YA ESTÁ LOGUEADO, LO MANDAMOS A LA LISTA DE PRODUCTOS
    if request.user.is_authenticated:
        return redirect('shop:product_list')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('shop:product_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        # Actualizamos los datos básicos del modelo User de Django
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.save()
        messages.success(request, '¡Perfil actualizado con éxito!')
        return redirect('shop:user_profile')
    
    return render(request, 'shop/user/edit_profile.html')