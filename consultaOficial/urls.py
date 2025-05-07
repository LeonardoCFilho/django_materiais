from django.contrib import admin
from django.urls import path, include
from . import views

app_name = 'consultaOficial'  

urlpatterns = [
    path('', views.index, name='index_consultaOficial'),
    path('materiaisPesquisa/', views.material_pesquisa, name='material_pesquisa'),
]
