from rest_framework import serializers
from .models import Material


class MaterialSerializer(serializers.ModelSerializer):
    ultimo_uso_meses = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = ["codigo", "descricao", "saldo", "ultimo_uso_meses"]

    def get_ultimo_uso_meses(self, obj):
        if hasattr(obj, "ultimoUso_meses"):
            return obj.ultimoUso_meses
        return None
