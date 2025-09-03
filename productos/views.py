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
            except requests.exceptions.RequestException as e:
                product_data = {'error': f'Error al obtener el producto: {e}'}
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
            tittle = form.cleaned_data['title']
            price = form.cleaned_data['price']
            description = form.cleaned_data['description']
            category_id = form.cleaned_data['category_id']
            images = [url.strip() for url in form.cleaned_data['images'].split(',')]
            
            base_url = 'https://api.escuelajs.co/api/v1/products/'
            product_data = {
                'title': tittle,
                'price': float(price),
                'description': description,
                'categoryId': category_id,
                'images': images
            }
            headers = {
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.post(base_url, data=json.dumps(product_data), headers=headers)
                response.raise_for_status()
                message = 'Producto creado exitosamente.'
                form = CrearProductoForm()
            
            except requests.exceptions.RequestException as e:
                message = f'Error al crear el producto: {e}'
            except json.JSONDecodeError:
                message = 'Error al decodificar la respuesta de la API.'
    
    context = {
        'form': form,
        'message': message,
    }
    return render(request, 'crear_producto.html', context)