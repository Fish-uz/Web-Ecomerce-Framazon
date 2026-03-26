from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product
from django.views.decorators.http import require_POST
from .cart import Cart
from .forms import OrderCreateForm
from .models import OrderItem
from django.utils.text import slugify
from .forms import OrderCreateForm, ProductForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.all()
    
    # LÓGICA DE BÚSQUEDA (NUEVO)
    search_query = request.GET.get('search')
    if search_query:
        # Filtramos productos cuyo nombre O descripción contengan la búsqueda
        products = products.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    context = {
        'category': category,
        'categories': categories,
        'products': products,
        'search_query': search_query, # Pasamos la búsqueda al template
    }
    return render(request, 'shop/product/list.html', context)

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    return render(request, 'shop/product/detail.html', {'product': product})

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=product, quantity=quantity)
    return redirect('shop:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'shop/cart/detail.html', {'cart': cart})

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('shop:cart_detail')

def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in cart:
                OrderItem.objects.create(order=order,
                                        product=item['product'],
                                        price=item['price'],
                                        quantity=item['quantity'])
            cart.clear()
            return render(request, 'shop/order/created.html', {'order': order})
    else:
        form = OrderCreateForm()
    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})

@login_required
def product_create(request):
    if request.method == 'POST':
        # Pasamos request.POST para los datos y request.FILES para la imagen
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # Creamos el objeto pero no lo guardamos en la BD todavía (commit=False)
            product = form.save(commit=False)
            # ASIGNAR AUTOMÁTICAMENTE EL VENDEDOR (request.user)
            product.vendedor = request.user 
            # Crear el slug automático a partir del nombre
            product.slug = slugify(product.name)
            # Guardar el producto definitivamente
            product.save()
            return redirect('shop:product_list')
    else:
        # Si es un método GET, mostramos el formulario vacío
        form = ProductForm()
    return render(request, 'shop/product/create.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Lo logueamos automáticamente
            return redirect('shop:product_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})