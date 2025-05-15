from django.db import models


class DatabaseTeste(models.Model):
    CO_MAT = models.DecimalField(
        max_digits=10, decimal_places=0
    )  # CO_MAT as a numeric field with 10 digits
    DE_MAT = models.CharField(
        max_length=4000
    )  # DE_MAT as a varchar with a maximum length of 4000 characters
    QT_SALDO_ATU = models.IntegerField()  # QT_SALDO_ATU as an integer field

    def __str__(self):
        return f"{self.CO_MAT} - {self.DE_MAT[:50]}"

    class Meta:
        db_table = "consultaOficial_databaseteste"  # Confirme o nome da tabela
