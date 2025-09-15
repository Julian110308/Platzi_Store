import requests
import json
from django.shortcuts import render, redirect
from .forms import BuscarProductoForm, CrearProductoForm
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def inicio(request):
    base_url = 'https://api.escuelajs.co/api/v1/products'
    products_data = []

    try:
        response = requests.get(base_url)
        response.raise_for_status()

        data = response.json()
        if isinstance(data, list):
            products_data = data
        else:
            products_data = [data]

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


def get_categories():
    """Obtener categorías desde la API"""
    url = "https://api.escuelajs.co/api/v1/categories"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [(str(cat["id"]), cat["name"]) for cat in data]
    except requests.exceptions.RequestException:
        return []


def crear_producto_view(request):
    message = None
    categories = get_categories()

    if request.method == 'POST':
        form = CrearProductoForm(request.POST)
        form.fields['category'].choices = categories  # asignar dinámicamente
        if form.is_valid():
            data = form.cleaned_data.copy()

            payload = {
                'title': data['title'],
                'price': float(data['price']),
                'description': data['description'],
                'categoryId': int(data['category']),
                'images': [data['image']]
            }

            base_url = 'https://api.escuelajs.co/api/v1/products'
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(base_url, json=payload, headers=headers)

                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")

                if response.status_code == 201:
                    new_product = response.json()
                    message = f'¡Producto "{new_product.get("title", "")}" creado con éxito!'
                    form = CrearProductoForm()
                    form.fields['category'].choices = categories
                else:
                    try:
                        error_data = response.json()
                        message = f'Error de la API: {error_data}'
                    except:
                        message = f'Error HTTP {response.status_code}: {response.text}'
            except requests.exceptions.RequestException as e:
                message = f'Error de conexión: {e}'
            except Exception as e:
                message = f'Error inesperado: {e}'
    else:
        form = CrearProductoForm()
        form.fields['category'].choices = categories

    context = {
        'form': form,
        'message': message,
        'edit_mode': False,
    }
    return render(request, 'crear_producto.html', context)


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
    categories = get_categories()

    if request.method == 'POST':
        form = CrearProductoForm(request.POST)
        form.fields['category'].choices = categories
        if form.is_valid():
            data = form.cleaned_data.copy()

            payload = {
                'title': data['title'],
                'price': float(data['price']),
                'description': data['description'],
                'categoryId': int(data['category']),
                'images': [data['image']]
            }

            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.put(base_url, json=payload, headers=headers, timeout=10)

                print(f"PUT Payload: {payload}")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")

                if response.status_code in [200, 201]:
                    response_data = response.json()
                    message = f'¡Producto actualizado con éxito! ID: {response_data.get("id", product_id)}'
                else:
                    try:
                        error_data = response.json()
                        message = f'Error de la API: {error_data}'
                    except:
                        message = f'Error HTTP {response.status_code}: {response.text}'

            except requests.exceptions.Timeout:
                message = 'Error: Tiempo de espera agotado. Inténtalo de nuevo.'
            except requests.exceptions.ConnectionError:
                message = 'Error: No se pudo conectar con la API. Verifica tu conexión.'
            except requests.exceptions.RequestException as e:
                message = f'Error de conexión: {e}'

    else:
        try:
            response = requests.get(base_url, timeout=10)

            if response.status_code == 200:
                product_data = response.json()

                initial_data = {
                    'title': product_data.get('title', ''),
                    'price': str(product_data.get('price', '')),
                    'description': product_data.get('description', ''),
                    'category': str(product_data.get('category', {}).get('id', '')),
                    'image': product_data.get('images', [''])[0] if product_data.get('images') else ''
                }

                form = CrearProductoForm(initial=initial_data)
                form.fields['category'].choices = categories
            else:
                return HttpResponse(f'Error al obtener el producto: Status {response.status_code}', status=400)

        except requests.exceptions.RequestException as e:
            return HttpResponse(f'Error al obtener los datos del producto: {e}', status=500)

    context = {
        'form': form,
        'product_id': product_id,
        'edit_mode': True,
        'message': message,
    }

    return render(request, 'crear_producto.html', context)