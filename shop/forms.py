from django import forms
from .models import Order, Product

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
        fields = ['category', 'name', 'image', 'description', 'price', 'stock']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

# shop/forms.py

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]

class CartAddProductForm(forms.Form):
   quantity = forms.IntegerField(min_value=1, label='Cantidad')
   override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)