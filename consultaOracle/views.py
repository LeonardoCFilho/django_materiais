from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Material, ConsumoMaterial
from .serializers import MaterialSerializer
from django.db.models import OuterRef, Subquery, F, ExpressionWrapper, fields
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["codigo", "descricao"]
    ordering_fields = ["codigo", "descricao", "saldo"]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.request

        # Filtros
        codigo = request.query_params.get("codigo")
        descricao = request.query_params.get("descricao")
        saldo_filter = request.query_params.get("saldo_filter")
        saldo = request.query_params.get("saldo")
        saldo_max = request.query_params.get("saldo_between_end")

        if codigo:
            queryset = queryset.filter(codigo__startswith=codigo)
        if descricao:
            queryset = queryset.filter(descricao__icontains=descricao)
        if saldo_filter and saldo:
            if saldo_filter == "menorq":
                queryset = queryset.filter(saldo__lt=saldo)
            elif saldo_filter == "igual":
                queryset = queryset.filter(saldo=saldo)
            elif saldo_filter == "maiorq":
                queryset = queryset.filter(saldo__gt=saldo)
            elif saldo_filter == "entre" and saldo_max:
                queryset = queryset.filter(saldo__gte=saldo, saldo__lte=saldo_max)

        return queryset

    @action(detail=False, methods=["get"])
    def filtros(self, request):
        return Response(
            {
                "saldo_filter_options": [
                    {"value": "menorq", "label": "Menor que"},
                    {"value": "igual", "label": "Igual a"},
                    {"value": "maiorq", "label": "Maior que"},
                    {"value": "entre", "label": "Entre"},
                ],
            }
        )


class IndexView(APIView):
    def get(self, request):
        return Response({"message": "API de Materiais JF"}, status=status.HTTP_200_OK)
