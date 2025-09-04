import requests
import json
from django.shortcuts import render, redirect
from .forms import BuscarProductoForm, CrearProductoForm
from django.http import HttpResponse
from django.contrib import messages

def inicio(request):
    base_url = 'https://api.escuelajs.co/api/v1/products'
    products_data = []
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        
        # Asegurar que data siempre sea una lista
        data = response.json()
        if isinstance(data, list):
            products_data = data
        else:
            products_data = [data]

        # Filtrar solo productos con 'id' válido
        products_data = [p for p in products_data if 'id' in p and p['id'] is not None]
        
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
                
                if product_data.get('statusCode') == 404:
                    product_data = {'error': 'Producto no encontrado.'}

            except requests.exceptions.RequestException as e:
                product_data = {'error': f'Error al conectar con la API: {e}'}

    context = {
        'form': form,
        'product_data': product_data
    }
    return render(request, 'buscar_producto.html', context)

def crear_producto_view(request):
    message = None
    form = CrearProductoForm()
    
    if request.method == 'POST':
        form = CrearProductoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            
            # Preparar datos para la API
            payload = {
                'title': data['title'],
                'price': float(data['price']),  # Asegurar que sea número
                'description': data['description'],
                'categoryId': get_category_id(data['category']),  # Usar ID numérico
                'images': [data['image']]  # Array de imágenes
            }
            
            base_url = 'https://api.escuelajs.co/api/v1/products'
            
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(base_url, json=payload, headers=headers)
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code == 201:  # Creado exitosamente
                    new_product = response.json()
                    message = f'¡Producto "{new_product.get("title", "")}" creado con éxito!'
                    form = CrearProductoForm()  # Limpiar formulario
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.HTTPError as e:
                try:
                    error_data = response.json()
                    message = f'Error de la API: {error_data.get("message", str(e))}'
                except:
                    message = f'Error HTTP {response.status_code}: {response.text}'
            except requests.exceptions.RequestException as e:
                message = f'Error de conexión: {e}'
            except Exception as e:
                message = f'Error inesperado: {e}'
    
    context = {
        'form': form,
        'message': message,
        'edit_mode': False,
    }
    return render(request, 'crear_producto.html', context)

def get_category_id(category_name):
    """Convertir nombre de categoría a ID numérico según la API"""
    category_mapping = {
        'electronics': 2,
        'jewelery': 3,
        "men's clothing": 4,
        "women's clothing": 5,
    }
    return category_mapping.get(category_name, 1)  # Default a 1 si no encuentra

def eliminar_producto_view(request, product_id):
    if request.method == 'POST':
        base_url = f'https://api.escuelajs.co/api/v1/products/{product_id}'
        
        try:
            response = requests.delete(base_url)
            response.raise_for_status()
            messages.success(request, 'Producto eliminado exitosamente')
            
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error al eliminar: {e}')
            return render(request, 'error.html', {'error_message': f'Error al eliminar: {e}'})
    
    return redirect('productos:inicio')

def editar_producto_view(request, product_id):
    base_url = f'https://api.escuelajs.co/api/v1/products/{product_id}'
    message = None
    
    if request.method == 'POST':
        form = CrearProductoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            
            # Preparar datos para la API
            payload = {
                'title': data['title'],
                'price': float(data['price']),
                'description': data['description'],
                'categoryId': get_category_id(data['category']),
                'images': [data['image']]
            }
            
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.put(base_url, json=payload, headers=headers)
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code == 200:
                    updated_product = response.json()
                    message = f'¡Producto "{updated_product.get("title", "")}" actualizado con éxito!'
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.HTTPError as e:
                try:
                    error_data = response.json()
                    message = f'Error de la API: {error_data.get("message", str(e))}'
                except:
                    message = f'Error HTTP {response.status_code}: {response.text}'
            except requests.exceptions.RequestException as e:
                message = f'Error de conexión: {e}'
    
    else:
        try:
            response = requests.get(base_url)
            response.raise_for_status()
            product_data = response.json()
            
            # Adaptar datos del producto al formulario
            initial_data = {
                'title': product_data.get('title', ''),
                'price': product_data.get('price', ''),
                'description': product_data.get('description', ''),
                'category': get_category_name_from_data(product_data),
                'image': product_data.get('images', [''])[0] if product_data.get('images') else ''
            }
            
            form = CrearProductoForm(initial=initial_data)
        
        except requests.exceptions.RequestException as e:
            return HttpResponse(f'Error al obtener los datos del producto: {e}', status=500)
    
    context = {
        'form': form,
        'product_id': product_id,
        'edit_mode': True,
        'message': message,
    }
    
    return render(request, 'crear_producto.html', context)

def get_category_name_from_data(product_data):
    """Extraer nombre de categoría de los datos del producto"""
    if isinstance(product_data.get('category'), dict):
        return product_data['category'].get('name', '')
    return product_data.get('category', '')