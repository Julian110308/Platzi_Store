from django import forms
from django.core.validators import URLValidator, MinValueValidator
from django.core.exceptions import ValidationError
import re

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
        choices=[],   # <-- ya no ponemos categorías fijas
        required=True,
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    image = forms.URLField(
        label='URL de la Imagen', 
        required=True,
        validators=[URLValidator(message="Ingresa una URL válida")],
        widget=forms.URLInput(attrs={
            'placeholder': 'https://ejemplo.com/imagen.jpg',
            'class': 'form-input',
            'id': 'image-url-input'  # Para JavaScript
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
            # Validación básica de formato de imagen
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
            
            # Extraer extensión de la URL (sin parámetros)
            clean_url = image_url.split('?')[0].lower()
            
            # Verificar si tiene una extensión de imagen válida
            has_valid_extension = any(clean_url.endswith(ext) for ext in valid_extensions)
            
            # Verificar patrones comunes de servicios de imágenes
            image_services = [
                'images.unsplash.com',
                'cdn.pixabay.com',
                'images.pexels.com',
                'i.imgur.com',
                'picsum.photos',
                'via.placeholder.com',
                'placehold.it',
                'source.unsplash.com',
                'firebasestorage.googleapis.com',
                'amazonaws.com',
                'cloudinary.com'
            ]
            
            is_image_service = any(service in image_url.lower() for service in image_services)
            
            # Si no tiene extensión válida ni es de un servicio conocido, dar advertencia
            if not has_valid_extension and not is_image_service:
                # No bloquear, solo advertir (esto se podría manejar en el frontend)
                pass
                
        return image_url