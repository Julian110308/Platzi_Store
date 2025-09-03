from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('buscar/', views.buscar_producto_view, name='buscar_producto'),
    path('crear/', views.crear_producto_view, name='crear_producto'),
]
