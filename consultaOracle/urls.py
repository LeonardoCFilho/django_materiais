from django.contrib import admin
from django.urls import path, include
from . import views

app_name = 'consultaOracle'  

urlpatterns = [
    path('', views.index, name='index_consultaOracle'),
    path('materiaisPesquisa/', views.material_pesquisa, name='material_pesquisa'),
]
