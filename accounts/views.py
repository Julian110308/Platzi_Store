import requests
import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.http import JsonResponse  # ← NUEVO IMPORT
from .forms import UserRegistrationForm, UserLoginForm

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer
)
# Configurar logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# URL base de tu API (configurable desde settings)
API_BASE_URL = "http://127.0.0.1:8000/api/"

@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    """
    Vista API para el registro de nuevos usuarios.
    
    Endpoint: POST /api/register/
    
    Parámetros esperados:
    - username: nombre de usuario único
    - email: correo electrónico válido
    - password: contraseña (mínimo 8 caracteres)
    - password2: confirmación de contraseña
    - first_name: nombre (opcional)
    - last_name: apellido (opcional)
    
    Respuestas:
    - 201: Usuario creado exitosamente
    - 400: Error en validación de datos
    """
    if request.method == 'POST':
        # Creamos el serializer con los datos recibidos
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            # Guardamos el nuevo usuario
            user = serializer.save()
            
            # Creamos o obtenemos el token de autenticación para el usuario
            token, created = Token.objects.get_or_create(user=user)
            
            # Preparamos la respuesta con los datos del usuario y su token
            response_data = {
                'success': True,
                'message': 'Usuario registrado satisfactoriamente',
                'user': UserSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        # Si hay errores de validación, los devolvemos
        return Response({
            'success': False,
            'message': 'Error en el registro',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    """
    Vista API para el inicio de sesión de usuarios.
    
    Endpoint: POST /api/login/
    
    Parámetros esperados:
    - username: nombre de usuario
    - password: contraseña
    
    Respuestas:
    - 200: Autenticación exitosa
    - 400: Error en credenciales
    """
    if request.method == 'POST':
        # Creamos el serializer con los datos de login
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Obtenemos el usuario validado
            user = serializer.validated_data['user']
            
            # Iniciamos sesión en Django (opcional, para mantener sesión)
            login(request, user)
            
            # Creamos o obtenemos el token de autenticación
            token, created = Token.objects.get_or_create(user=user)
            
            # Preparamos la respuesta exitosa
            response_data = {
                'success': True,
                'message': 'Autenticación satisfactoria',
                'user': UserSerializer(user).data,
                'token': token.key
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        # Si hay errores de autenticación
        return Response({
            'success': False,
            'message': 'Error en la autenticación',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    Vista API para cerrar sesión.
    
    Endpoint: POST /api/logout/
    Requiere: Token de autenticación en headers
    
    Respuestas:
    - 200: Sesión cerrada exitosamente
    - 401: No autorizado (sin token válido)
    """
    if request.method == 'POST':
        try:
            # Eliminamos el token del usuario
            request.user.auth_token.delete()
            
            # Cerramos la sesión de Django
            logout(request)
            
            return Response({
                'success': True,
                'message': 'Sesión cerrada exitosamente'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error al cerrar sesión',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    """
    Vista API para obtener el perfil del usuario actual.
    
    Endpoint: GET /api/profile/
    Requiere: Token de autenticación en headers
    
    Respuestas:
    - 200: Datos del usuario
    - 401: No autorizado (sin token válido)
    """
    if request.method == 'GET':
        # Devolvemos los datos del usuario autenticado
        serializer = UserSerializer(request.user)
        
        return Response({
            'success': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_username_api(request):
    """
    Vista API para verificar disponibilidad de nombre de usuario.
    
    Endpoint: GET /api/check-username/?username=nombreusuario
    
    Parámetros de query:
    - username: nombre de usuario a verificar
    
    Respuestas:
    - 200: Información sobre disponibilidad
    """
    username = request.GET.get('username', '')
    
    if not username:
        return Response({
            'success': False,
            'message': 'Debe proporcionar un nombre de usuario'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verificamos si el username existe
    exists = User.objects.filter(username=username).exists()
    
    return Response({
        'success': True,
        'available': not exists,
        'message': 'Nombre de usuario no disponible' if exists else 'Nombre de usuario disponible'
    }, status=status.HTTP_200_OK)

@csrf_protect
@never_cache
def register_view(request):
    """
    Vista para el registro de usuarios que se comunica con la API.
    Mejorada para mejor manejo de respuestas y feedback al usuario.
    """
    if request.user.is_authenticated:
        messages.info(request, 'Ya tienes una sesión activa.')
        return redirect('products:product_list')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        logger.debug(f"Form data: {request.POST}")
        logger.debug(f"Form is valid: {form.is_valid()}")
        logger.debug(f"Form errors: {form.errors}")
        
        if form.is_valid():
            # Datos para enviar a la API
            user_data = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'password': form.cleaned_data['password1'],
                'password2': form.cleaned_data['password2'],
            }
            
            logger.debug(f"Data to send to API: {user_data}")
            
            try:
                # Llamada a la API de registro
                response = requests.post(
                    f"{API_BASE_URL}register/",
                    json=user_data,
                    headers={
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                logger.debug(f"API Response status: {response.status_code}")
                logger.debug(f"API Response content: {response.text}")
                
                if response.status_code == 201:
                    # El registro fue exitoso
                    try:
                        response_data = response.json()
                        user_info = response_data.get('user', {})
                        
                        # Mensaje de éxito más detallado
                        success_message = f'¡Registro exitoso! Bienvenido {user_info.get("first_name", user_data["username"])}. Tu cuenta ha sido creada correctamente.'
                        messages.success(request, success_message)
                        
                        logger.info(f"User registered successfully: {user_data['username']}")
                        
                        # Para requests AJAX, devolvemos JSON
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                            return JsonResponse({
                                'success': True,
                                'message': success_message,
                                'redirect_url': reverse('accounts:login'),
                                'user_data': user_info
                            })
                        
                        # Para requests normales, redirigir al login
                        return redirect('accounts:login')
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error in success response: {e}")
                        # Si no podemos parsear la respuesta pero el status es 201, aún es éxito
                        messages.success(
                            request, 
                            '¡Registro exitoso! Tu cuenta ha sido creada. Ahora puedes iniciar sesión.'
                        )
                        return redirect('accounts:login')
                        
                elif response.status_code == 400:
                    # La API devolvió errores de validación
                    try:
                        error_data = response.json().get('errors', {})
                        logger.debug(f"API Error data: {error_data}")
                        
                        # Mapeo de errores de la API a campos del formulario
                        error_mapping = {
                            'username': 'username',
                            'email': 'email', 
                            'password': 'password1',
                            'password2': 'password2',
                            'first_name': 'first_name',
                            'last_name': 'last_name'
                        }
                        
                        # Agregar errores específicos a los campos correspondientes
                        for api_field, form_field in error_mapping.items():
                            if api_field in error_data:
                                errors = error_data[api_field]
                                if isinstance(errors, list):
                                    for error in errors:
                                        form.add_error(form_field, error)
                                else:
                                    form.add_error(form_field, errors)
                        
                        # Agregar errores no específicos de campo
                        if 'non_field_errors' in error_data:
                            for error in error_data['non_field_errors']:
                                form.add_error(None, error)
                        
                        # Si no hay errores específicos pero hay un mensaje general
                        if not error_data and 'message' in response.json():
                            form.add_error(None, response.json()['message'])
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error(f"JSON decode error in API error response: {e}")
                        form.add_error(None, 'Error en el registro. Por favor, verifica tus datos e inténtalo nuevamente.')
                
                elif response.status_code == 409:
                    # Conflicto - usuario ya existe
                    form.add_error('username', 'Este nombre de usuario ya está en uso.')
                    form.add_error('email', 'Este correo electrónico ya está registrado.')
                    
                elif response.status_code >= 500:
                    # Error del servidor
                    logger.error(f"Server error: {response.status_code} - {response.text}")
                    form.add_error(None, 'Error interno del servidor. Por favor, inténtalo más tarde.')
                    
                else:
                    # Cualquier otro error HTTP
                    logger.error(f"Unexpected HTTP status: {response.status_code} - {response.text}")
                    form.add_error(None, f'Error inesperado del servidor. Código: {response.status_code}')
                    
            except requests.exceptions.Timeout:
                # Error de timeout específico
                logger.error("Request timeout in register_view")
                form.add_error(None, 'La petición tardó demasiado tiempo. Verifica tu conexión e inténtalo nuevamente.')
                
            except requests.exceptions.ConnectionError:
                # Error de conexión específico
                logger.error("Connection error in register_view")
                form.add_error(None, 'No se pudo conectar con el servidor. Verifica tu conexión a internet.')
                
            except requests.exceptions.RequestException as e:
                # Cualquier otro error de requests
                logger.error(f"Request exception in register_view: {str(e)}")
                form.add_error(None, 'Error de conexión con el servidor. Por favor, inténtalo más tarde.')
                
            except Exception as e:
                # Error inesperado
                logger.error(f"Unexpected error in register_view: {str(e)}")
                form.add_error(None, 'Ocurrió un error inesperado. Por favor, inténtalo más tarde.')
        
        else:
            # El formulario no es válido
            logger.debug(f"Form validation errors: {form.errors}")
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
            
        # Para requests AJAX con errores, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            errors_dict = {}
            for field, errors in form.errors.items():
                errors_dict[field] = [str(error) for error in errors]
                
            return JsonResponse({
                'success': False,
                'message': 'Error en el registro',
                'errors': errors_dict,
                'form_errors': dict(form.errors)
            }, status=400)
                
    else:
        # GET request - mostrar formulario vacío
        form = UserRegistrationForm()
    
    return render(request, 'register.html', {
        'form': form,
        'title': 'Registro de Usuario'
    })

@csrf_protect
@never_cache
def login_view(request):
    """
    Vista para el login de usuarios
    """
    if request.user.is_authenticated:
        messages.info(request, 'Ya tienes una sesión activa.')
        return redirect('products:product_list')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            login_data = {
                'username': username,
                'password': password,
            }
            
            try:
                response = requests.post(
                    f"{API_BASE_URL}login/",
                    json=login_data,
                    headers={
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    user = authenticate(request, username=username, password=password)
                    
                    if user and user.is_active:
                        login(request, user)
                        messages.success(
                            request, 
                            f'¡Bienvenido de nuevo, {user.first_name or user.username}!'
                        )
                        
                        # Guardar token en sesión
                        if 'token' in response_data:
                            request.session['api_token'] = response_data['token']
                        
                        next_url = request.GET.get('next', 'products:product_list')
                        return redirect(next_url)
                    else:
                        # Si el usuario no existe localmente, se asume que se registró en otro lado.
                        # Mejorar la lógica para crear el usuario localmente si es necesario.
                        user_info = response_data.get('user', {})
                        try:
                            user = User.objects.create_user(
                                username=username,
                                email=user_info.get('email', ''),
                                first_name=user_info.get('first_name', ''),
                                last_name=user_info.get('last_name', ''),
                                password=password # El método create_user hashea la contraseña
                            )
                            
                            user = authenticate(request, username=username, password=password)
                            if user and user.is_active:
                                login(request, user)
                                messages.success(
                                    request, 
                                    f'¡Bienvenido, {user.first_name or user.username}! Tu cuenta ha sido sincronizada.'
                                )
                                if 'token' in response_data:
                                    request.session['api_token'] = response_data['token']
                                
                                next_url = request.GET.get('next', 'products:product_list')
                                return redirect(next_url)
                            else:
                                messages.error(request, 'Error al autenticar al usuario sincronizado. Intenta iniciar sesión nuevamente.')
                        
                        except Exception as e:
                            messages.error(request, 'Error al sincronizar usuario. Contacta al administrador.')
                            
                elif response.status_code == 400:
                    try:
                        error_data = response.json().get('errors', {})
                        if error_data.get('non_field_errors'):
                             form.add_error(None, error_data['non_field_errors'][0])
                        else:
                            form.add_error(None, 'Credenciales inválidas. Verifica tu usuario y contraseña.')
                    except:
                        form.add_error(None, 'Credenciales inválidas. Verifica tu usuario y contraseña.')
                else:
                    form.add_error(None, f'Error del servidor: {response.status_code}')
                        
            except requests.RequestException:
                form.add_error(None, 'Error de conexión con el servidor. Verifica tu conexión a internet.')
                
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """
    Vista para cerrar sesión
    """
    username = request.user.username if request.user.is_authenticated else None
    
    # Opcional: llamar al endpoint de logout de la API
    if 'api_token' in request.session:
        try:
            requests.post(
                f"{API_BASE_URL}logout/",
                json={'refresh_token': request.session.get('refresh_token', '')},
                headers={
                    'Authorization': f'Bearer {request.session["api_token"]}',
                    'Content-Type': 'application/json'
                },
                timeout=5
            )
        except:
            pass  # Si falla, continuar con el logout local
        
        # Limpiar tokens de la sesión
        del request.session['api_token']
        if 'refresh_token' in request.session:
            del request.session['refresh_token']
    
    # Cerrar sesión en Django
    logout(request)
    
    if username:
        messages.success(request, f'Has cerrado sesión exitosamente, {username}. ¡Hasta pronto!')
    else:
        messages.success(request, 'Has cerrado sesión exitosamente.')
    
    return redirect('accounts:login')