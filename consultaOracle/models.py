from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Material(models.Model):
    codigo = models.DecimalField(max_digits=10, decimal_places=0, validators=[MinValueValidator(0)], null=False, blank=False, verbose_name="Código númerico do produto")
    descricao = models.CharField(max_length=4000, null=False, blank=True, verbose_name="Descrição/nome do material")
    saldo = models.IntegerField(null=False, blank=False, verbose_name="Quantidade do material em estoque")
    def __str__(self):
        return str(self.codigo) + self.descricao
    class Meta:
        ordering = ['codigo', 'descricao','saldo']

class ConsumoMaterial(models.Model):
    materialUsado = models.ForeignKey(Material, on_delete=models.CASCADE)
    dataConsumo = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Consumo of {self.materialUsado} at {self.dataConsumo}"