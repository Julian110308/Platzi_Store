from django import forms

class BuscarProductoForm(forms.Form):
    product_id = forms.IntegerField(label='ID del Producto', required=True)

class CrearProductoForm(forms.Form):
    title = forms.CharField(label='Título', max_length=100, required=True)
    price = forms.DecimalField(label='Precio', max_digits=10, decimal_places=2, required=True)
    description = forms.CharField(label='Descripción', widget=forms.Textarea, required=True)
    # Cambiado: usar category como texto, no category_id como entero
    category = forms.ChoiceField(
        label='Categoría',
        choices=[
            ('', 'Selecciona una categoría'),
            ('electronics', 'Electrónicos'),
            ('jewelery', 'Joyería'),
            ("men's clothing", 'Ropa de Hombre'),
            ("women's clothing", 'Ropa de Mujer'),
        ],
        required=True
    )
    # Cambiado: usar image como URL única, no images múltiples
    image = forms.URLField(label='URL de la Imagen', required=True)