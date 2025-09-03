from django import forms

class BuscarProductoForm(forms.Form):
    product_id = forms.IntegerField(label='ID del Producto', required=True)

class CrearProductoForm(forms.Form):
    title = forms.CharField(label='Título', max_length=100, required=True)
    price = forms.DecimalField(label='Precio', max_digits=10, decimal_places=2, required=True)
    description = forms.CharField(label='Descripción', widget=forms.Textarea, required=True)
    category_id = forms.IntegerField(label='ID de Categoría', required=True)
    images = forms.CharField(label='URLs de Imágenes (separadas por comas)', widget=forms.Textarea, required=False)