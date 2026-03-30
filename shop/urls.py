from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('register/', views.register, name='register'),
    
    # CARRITO
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    
    # PERFIL Y ÓRDENES
    path('order/create/', views.order_create, name='order_create'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('vender/', views.product_create, name='product_create'),
    path('edit/<int:id>/', views.product_edit, name='product_edit'),
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('order/<int:order_id>/confirm-info/', views.confirm_info, name='confirm_info'),
    path('order/<int:order_id>/finalize/', views.finalize_order, name='finalize_order'),
    path('order/<int:order_id>/decline/', views.decline_info, name='decline_info'),

    # DINÁMICAS
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    # Esta ruta debe coincidir exactamente con los argumentos de get_absolute_url
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
]