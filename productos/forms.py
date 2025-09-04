from django import forms
from django.core.validators import URLValidator, MinValueValidator
from django.core.exceptions import ValidationError
import requests

class BuscarProductoForm(forms.Form):
    product_id = forms.IntegerField(
        label='ID del Producto', 
        required=True,
        validators=[MinValueValidator(1, message="El ID debe ser mayor a 0")]
    )

class CrearProductoForm(forms.Form):
    title = forms.CharField(
        label='Título', 
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: iPhone 14 Pro Max',
            'class': 'form-input'
        })
    )
    
    price = forms.DecimalField(
        label='Precio', 
        max_digits=10, 
        decimal_places=2, 
        required=True,
        validators=[MinValueValidator(0.01, message="El precio debe ser mayor a 0")],
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'placeholder': '29.99',
            'class': 'form-input'
        })
    )
    
    description = forms.CharField(
        label='Descripción', 
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Describe las características y beneficios de tu producto...',
            'class': 'form-input'
        })
    )
    
    category = forms.ChoiceField(
        label='Categoría',
        choices=[
            ('', 'Selecciona una categoría'),
            ('electronics', 'Electrónicos'),
            ('jewelery', 'Joyería'),
            ("men's clothing", 'Ropa de Hombre'),
            ("women's clothing", 'Ropa de Mujer'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    image = forms.URLField(
        label='URL de la Imagen', 
        required=True,
        validators=[URLValidator(message="Ingresa una URL válida")],
        widget=forms.URLInput(attrs={
            'placeholder': 'https://ejemplo.com/imagen.jpg',
            'class': 'form-input'
        })
    )

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            title = title.strip()
            if len(title) < 3:
                raise ValidationError("El título debe tener al menos 3 caracteres.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description:
            description = description.strip()
            if len(description) < 10:
                raise ValidationError("La descripción debe tener al menos 10 caracteres.")
        return description

    def clean_image(self):
        image_url = self.cleaned_data.get('image')
        if image_url:
            # Verificar que la URL es accesible (opcional, puede ser lento)
            try:
                response = requests.head(image_url, timeout=5)
                if response.status_code >= 400:
                    raise ValidationError("La URL de la imagen no es accesible.")
            except requests.RequestException:
                # Si no se puede verificar, permitir que pase
                # (la API se encargará de validar)
                pass
        return image_url