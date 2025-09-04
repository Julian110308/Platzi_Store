# productos/views.py

import requests
import json
from django.shortcuts import render, redirect
from .forms import BuscarProductoForm, CrearProductoForm

def inicio(request):
    base_url = 'https://api.escuelajs.co/api/v1/products'
    products_data = []
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        products_data = response.json()
        
    except requests.exceptions.RequestException as e:
        print(f'Error al conectar con la API: {e}')
        
    context = {
        'products': products_data,
    }
    return render(request, 'inicio.html', context)
    
def buscar_producto_view(request):
    product_data = None
    form = BuscarProductoForm()

    if request.method == 'POST':
        form = BuscarProductoForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product_id']
            base_url = f'https://api.escuelajs.co/api/v1/products/{product_id}'

            try:
                response = requests.get(base_url)
                response.raise_for_status()
                product_data = response.json()
                
                # Verificar si la respuesta contiene un error (producto no encontrado)
                if 'message' in product_data and product_data.get('statusCode') == 404:
                    product_data = {'error': f'Producto con ID {product_id} no encontrado.'}
                    
            except requests.exceptions.HTTPError as e:
                if response.status_code == 404:
                    product_data = {'error': f'Producto con ID {product_id} no encontrado.'}
                else:
                    product_data = {'error': f'Error HTTP: {e}'}
            except requests.exceptions.RequestException as e:
                product_data = {'error': f'Error al conectar con la API: {e}'}
            except ValueError:
                product_data = {'error': 'Respuesta de la API no válida.'}

    context = {
        'form': form,
        'product_data': product_data,
    }
    return render(request, 'buscar_producto.html', context)

def crear_producto_view(request):
    form = CrearProductoForm()
    message = None
    
    if request.method == 'POST':
        form = CrearProductoForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data['title']
            price = form.cleaned_data['price']
            description = form.cleaned_data['description']
            category = form.cleaned_data['category']  # Ahora es texto, no ID
            image = form.cleaned_data['image']  # Ahora es una sola imagen
            
            # Mapear categorías a sus IDs correspondientes en la API
            category_mapping = {
                'electronics': 2,
                'jewelery': 3,
                "men's clothing": 4,
                "women's clothing": 5,
            }
            
            category_id = category_mapping.get(category, 1)  # Default a 1 si no encuentra
            
            base_url = 'https://api.escuelajs.co/api/v1/products/'
            product_data = {
                'title': title,
                'price': float(price),
                'description': description,
                'categoryId': category_id,
                'images': [image]  # La API espera un array de imágenes
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            try:
                print(f"Enviando datos: {product_data}")  # Para debug
                
                response = requests.post(base_url, data=json.dumps(product_data), headers=headers)
                response.raise_for_status()
                created_product = response.json()
                
                print(f"Respuesta de la API: {created_product}")  # Para debug
                
                message = f'¡Producto creado exitosamente! ID: {created_product.get("id", "N/A")}'
                # Limpiar el formulario después de crear exitosamente
                form = CrearProductoForm()
            
            except requests.exceptions.RequestException as e:
                print(f"Error de requests: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_data = e.response.json()
                        message = f'Error al crear el producto: {error_data}'
                    except:
                        message = f'Error al crear el producto: {e.response.text}'
                else:
                    message = f'Error al crear el producto: {e}'
            except json.JSONDecodeError as e:
                message = f'Error al decodificar la respuesta de la API: {e}'
            except Exception as e:
                message = f'Error inesperado: {e}'
    
    context = {
        'form': form,
        'message': message,
    }
    return render(request, 'crear_producto.html', context)