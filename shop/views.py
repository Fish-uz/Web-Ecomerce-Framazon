from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import JsonResponse
from django.db.models import Q
from django.utils.text import slugify
from .models import Category, Product, Order, OrderItem, ProductImage, Review
from .forms import OrderCreateForm, ProductForm, CartAddProductForm, ProductImageFormSet, ProductImageForm
from .cart import Cart
from django.contrib import messages
from django.forms import inlineformset_factory
from .forms import ReviewForm

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    
    search_query = request.GET.get('q') 
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
    reviews = product.reviews.all()
    cart_product_form = CartAddProductForm()
    
    can_review = False
    already_reviewed = False
    
    if request.user.is_authenticated:
        already_reviewed = Review.objects.filter(product=product, user=request.user).exists()
        is_vendedor = product.vendedor == request.user
        has_received_product = OrderItem.objects.filter(
            order__user=request.user, 
            product=product,
            order__status='delivered'
        ).exists()
        
        if has_received_product and not is_vendedor and not already_reviewed:
            can_review = True
            
    return render(request, 'shop/product/detail.html', {
        'product': product,
        'reviews': reviews,
        'cart_product_form': cart_product_form,
        'can_review': can_review
    })

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    
    if form.is_valid():
        cd = form.cleaned_data
        if cd['quantity'] > product.stock:
            messages.error(request, f'Lo sentimos, solo hay {product.stock} unidades disponibles.')
            return redirect('shop:product_detail', id=product.id, slug=product.slug)
        
        cart.add(product=product,
                 quantity=cd['quantity'],
                 override_quantity=cd['override'])
    
    return redirect('shop:cart_detail')

def cart_detail(request):
    cart = Cart(request)
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
            # Validación extra de stock al momento de crear la orden
            for item in cart:
                if item['quantity'] > item['product'].stock:
                    messages.error(request, f"El producto {item['product'].name} ya no tiene stock suficiente.")
                    return redirect('shop:cart_detail')

            order = form.save(commit=False)
            order.user = request.user
            order.save()
            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'], price=item['price'], quantity=item['quantity'])
                # Descontar stock
                item['product'].stock -= item['quantity']
                item['product'].save()
                
            cart.clear()
            return render(request, 'shop/order/created.html', {'order': order})
    else:
        form = OrderCreateForm()
    return render(request, 'shop/order/create.html', {'cart': cart, 'form': form})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/order/my_orders.html', {'orders': orders})

@login_required
def user_profile(request):
    active_orders = Order.objects.filter(user=request.user).exclude(status__in=['delivered', 'canceled', 'completed'])
    order_history = Order.objects.filter(user=request.user)
    my_products = Product.objects.filter(vendedor=request.user) 
    mis_ventas = OrderItem.objects.filter(product__vendedor=request.user).order_by('-id')
    
    status_filter = request.GET.get('status')
    orders_filtered = Order.objects.filter(items__product__vendedor=request.user).distinct()
    
    if status_filter:
        orders_filtered = orders_filtered.filter(status=status_filter)
    
    context = {
        'active_orders': active_orders,
        'order_history': order_history,
        'my_products': my_products,
        'mis_ventas': mis_ventas,
        'orders': orders_filtered,
        'status_choices': Order.STATUS_CHOICES
    }
    return render(request, 'shop/user/profile.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        formset = ProductImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            product = form.save(commit=False)
            product.vendedor = request.user
            product.save() 
            
            instances = formset.save(commit=False)
            for i, instance in enumerate(instances):
                instance.product = product
                instance.save()
                if i == 0:
                    product.image = instance.image
                    product.save()
            
            return redirect('shop:product_list')
    else:
        form = ProductForm()
        formset = ProductImageFormSet()
    
    return render(request, 'shop/product/create.html', {'form': form, 'formset': formset})

def register(request):
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
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.email = request.POST.get('email')
        request.user.save()
        messages.success(request, '¡Perfil actualizado con éxito!')
        return redirect('shop:user_profile')
    return render(request, 'shop/user/edit_profile.html')

@login_required
def product_edit(request, id):
    product = get_object_or_404(Product, id=id, vendedor=request.user)
    existing_images_count = product.images.count()
    available_extra = max(0, 6 - existing_images_count)

    DynamicImageFormSet = inlineformset_factory(
        Product, ProductImage, 
        form=ProductImageForm, 
        extra=available_extra, 
        can_delete=True, 
        max_num=6
    )

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        formset = DynamicImageFormSet(request.POST, request.FILES, instance=product)
        
        if form.is_valid() and formset.is_valid():
            product = form.save()
            formset.save()
            
            # Actualizar imagen principal si existe al menos una
            first_img = product.images.first()
            if first_img:
                product.image = first_img.image
                product.save()

            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('/profile/#mis-publicaciones')
    else:
        form = ProductForm(instance=product)
        formset = DynamicImageFormSet(instance=product)
    
    return render(request, 'shop/product/edit.html', {
        'form': form,
        'formset': formset,
        'product': product
    })

@login_required
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    is_vendedor = OrderItem.objects.filter(order=order, product__vendedor=request.user).exists()
    
    if not is_vendedor:
        messages.error(request, "No tienes permiso para gestionar este pedido.")
        return redirect('shop:user_profile')

    # BLOQUEO: Solo permitir edición si NO está enviado O si fue rechazado
    if order.status == 'shipped':
        messages.warning(request, "Los detalles ya han sido enviados. Solo podrá editar si el cliente declina la información.")
        return redirect('/profile/#gestionar-ventas')
    
    new_status = request.POST.get('status')
    if new_status == 'shipped':
        order.status = 'shipped'
        order.courier_name = request.POST.get('courier_name')
        order.tracking_number = request.POST.get('tracking_number')
        order.courier_contact = request.POST.get('courier_contact')
        
        if 'shipping_proof' in request.FILES:
            order.shipping_proof = request.FILES['shipping_proof']
            
        order.save()
        messages.success(request, "Información de envío guardada y bloqueada.")
    else:
        order.status = new_status
        order.save()
    
    return redirect('/profile/#gestionar-ventas')

@login_required
@require_POST
def confirm_info(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.buyer_confirmed_info = True
    # Si el cliente confirma la info, podrías querer pasar el estado a 'delivered' automáticamente o esperar al finalize
    order.save()
    messages.success(request, "Has confirmado que recibiste la información de envío.")
    return redirect('shop:user_profile')

@login_required
@require_POST
def decline_info(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    reason = request.POST.get('rejection_reason')
    if reason:
        order.status = 'info_rejected'
        order.rejection_reason = reason
        order.buyer_confirmed_info = False
        order.save()
        messages.warning(request, "Has declinado la información. El vendedor ha sido notificado.")
    return redirect('shop:user_profile')

@login_required
def finalize_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, user=request.user)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        for item in order.items.all():
            Review.objects.get_or_create(
                product=item.product,
                user=request.user,
                defaults={'rating': rating, 'comment': comment}
            )

        order.status = 'delivered' # O 'completed' según tus STATUS_CHOICES
        order.save()
        messages.success(request, "¡Pedido finalizado con éxito!")
    return redirect('shop:user_profile')