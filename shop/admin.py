from django.contrib import admin
from .models import Category, Product, Order, OrderItem, ProductImage

# --- INLINES ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3 # Permite subir 3 fotos de golpe

# --- REGISTROS ---

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)} # Esto escribe el slug solo mientras escribes el nombre

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'stock', 'available', 'vendedor', 'created']
    list_filter = ['available', 'created', 'vendedor'] # Unificado
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline] # Añadidas las fotos adicionales aquí

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email',
                    'address', 'postal_code', 'city', 'country', 'paid',
                    'created', 'updated']
    list_filter = ['paid', 'created', 'updated']
    inlines = [OrderItemInline] # Aquí metemos los productos de la orden