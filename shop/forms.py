from django import forms
from django.forms import inlineformset_factory
from .models import Order, Product, ProductImage
from .models import Review

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'postal_code','country', 'city']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'stock']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# --- ESTA ES LA CLASE QUE FALTABA PARA EVITAR EL ERROR DE IMPORTACIÓN ---
class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']
# -----------------------------------------------------------------------

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]

class CartAddProductForm(forms.Form):
   quantity = forms.IntegerField(min_value=1, label='Cantidad')
   override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)

# Adaptamos el FormSet para que use la clase recién creada
ProductImageFormSet = inlineformset_factory(
    Product, 
    ProductImage, 
    form=ProductImageForm, # <--- Ahora la vista lo encontrará sin problemas
    fields=['image'], 
    extra=6,
    can_delete=True # <--- Cambiado a True para que el botón de basura en tu edit.html funcione
)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} Estrellas') for i in range(5, 0, -1)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Cuéntanos tu experiencia...'}),
        }