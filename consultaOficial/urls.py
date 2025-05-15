# django_materiais/consultaOficial/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.http import require_GET
from . import views

app_name = "consultaOficial"

urlpatterns = [
    path("", views.index, name="index_consultaOficial"),
    path("api/materiais/", require_GET(views.material_pesquisa2), name="material_api"),
    path("materiaisPesquisa/", views.material_pesquisa, name="material_pesquisa"),
]
