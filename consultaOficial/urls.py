# django_materiais/consultaOficial/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.http import require_GET
from . import views

app_name = "consultaOficial"

urlpatterns = [
    path("", views.index, name="index_consultaOficial"),
    
    # Consulta geral de materiais
    ## Prototipo backend
    path("materiaisPesquisa/", require_GET(views.material_pesquisa2), name="material_pesquisa"),
    ## Versão oficial (react)
    path("api/materiais/", require_GET(views.material_pesquisa2), name="material_pesquisa_api"),

    # Consulta de validade
    ## Prototipo backend
    path("materiaisValidade/", require_GET(views.consultaValidadeMateriais), name="material_validade"),
    ## Versão oficial (react)
    path("api/materiaisValidade/", require_GET(views.consultaValidadeMateriais), name="material_validade_api"),

    # Consulta de consumo medio
    ## Prototipo backend
    path("materiaisConsumoMedio/", require_GET(views.consultaConsumoMedioMateriais), name="material_consumo_medio"),
    ## Versão oficial (react)
    path("api/materiaisConsumoMedio/", require_GET(views.consultaConsumoMedioMateriais), name="material_consumo_medio_api"),
]
