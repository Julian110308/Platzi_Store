import requests
import json
from django.shortcuts import render, redirect
from .forms import BuscarProductoForm, CrearProductoForm
from django.http import HttpResponse

def inicio(request):
    base_url = 'https://api.escuelajs.co/api/v1/products'
    products_data = []
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        
        # Agregamos esta lógica para asegurar que `data` siempre sea una lista
        data = response.json()
        if isinstance(data, list):
            products_data = data
        else:
            # Si no es una lista, asumimos que es un solo objeto y lo convertimos a una lista
            products_data = [data]

        # Filtramos solo los productos que tienen un 'id' válido
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
            data = form.cleaned_data
            # Corregido: usar 'image' en lugar de 'images'
            data['images'] = [data['image']]  # La API espera un array de imágenes
            del data['image']  # Eliminar el campo 'image' original
            
            base_url = 'https://api.escuelajs.co/api/v1/products'
            
            try:
                response = requests.post(base_url, json=data)
                response.raise_for_status()
                
                new_product = response.json()
                message = f'¡Producto "{new_product["title"]}" creado con éxito!'
            except requests.exceptions.RequestException as e:
                message = f'Error al crear el producto: {e}'
    
    context = {
        'form': form,
        'message': message,
        'edit_mode': False,  # Añadido para distinguir modo
    }
    return render(request, 'crear_producto.html', context)

def eliminar_producto_view(request, product_id):
    if request.method == 'POST':
        base_url = f'https://api.escuelajs.co/api/v1/products/{product_id}'
        
        try:
            response = requests.delete(base_url)
            response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            return render(request, 'error.html', {'error_message': f'Error al eliminar: {e}'})
    
    return redirect('productos:inicio')

def editar_producto_view(request, product_id):
    base_url = f'https://api.escuelajs.co/api/v1/products/{product_id}'
    message = None
    
    if request.method == 'POST':
        form = CrearProductoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Corregido: usar 'image' en lugar de 'images'
            data['images'] = [data['image']]  # La API espera un array de imágenes
            del data['image']  # Eliminar el campo 'image' original
            
            try:
                response = requests.put(base_url, json=data)
                response.raise_for_status()
                
                updated_product = response.json()
                message = f'¡Producto "{updated_product["title"]}" actualizado con éxito!'
                # No redirigir inmediatamente para mostrar el mensaje
                
            except requests.exceptions.RequestException as e:
                message = f'Error al actualizar el producto: {e}'
    
    else:
        try:
            response = requests.get(base_url)
            response.raise_for_status()
            product_data = response.json()
            
            # Corregido: adaptar los datos del producto al formulario
            initial_data = {
                'title': product_data.get('title', ''),
                'price': product_data.get('price', ''),
                'description': product_data.get('description', ''),
                'category': product_data.get('category', ''),
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