from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, null=True) 
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=10)
    available = models.BooleanField(default=True)
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productos_del_vendedor')
    created = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente de Pago'),
        ('paid', 'Pagado / Procesando'),
        ('shipped', 'Enviado (Por confirmar)'),
        ('info_rejected', 'Info. Rechazada por Comprador'),
        ('delivered', 'Entregado / Finalizado'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Venezuela')
    city = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de guía")
    courier_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Empresa de envío")
    courier_contact = models.CharField(max_length=100, blank=True, null=True, verbose_name="Teléfono del courier")
    shipping_proof = models.ImageField(upload_to='orders/proofs/', blank=True, null=True, verbose_name="Comprobante de envío")
    buyer_confirmed_info = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Motivo de rechazo")
    
    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['-created']),]

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def save(self, *args, **kwargs):
        if self.pk:
            # Obtenemos el objeto actual de la base de datos para comparar
            original = Order.objects.get(pk=self.pk)
            
            # 1. Impedir retroceso de estatus
            status_order = ['pending', 'paid', 'shipped', 'info_rejected', 'delivered']
            if status_order.index(self.status) < status_order.index(original.status):
                # Excepción: permitir pasar de 'shipped' a 'info_rejected'
                if not (original.status == 'shipped' and self.status == 'info_rejected'):
                    raise ValidationError("No se puede retroceder el estado del pedido.")

            # 2. Si el estatus es Shipped, validar que existan datos de envío
            if self.status == 'shipped':
                if not self.courier_name or not self.tracking_number:
                    raise ValidationError("Debe ingresar Empresa y Nro. Guía para marcar como enviado.")

            # 3. Bloquear edición si ya fue aceptado
            if original.status == 'shipped' and self.status == 'shipped' and original.buyer_confirmed_info:
                raise ValidationError("La información de envío ya fue aceptada y no puede modificarse.")

        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', related_name='items_vendidos', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def vendedor(self):
        return self.product.vendedor

    def __str__(self):
        return f'Item {self.id} de la orden {self.order.id}'

    def get_cost(self):
        return self.price * self.quantity

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/%Y/%m/%d')
    alt_text = models.CharField(max_length=200, blank=True, help_text="Descripción de la imagen")

    def __str__(self):
        return f"Imagen para {self.product.name}"
    
class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.product.name} ({self.rating} stars)'