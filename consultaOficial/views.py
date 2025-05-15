from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET
from django.db.models import Q
from .models import DatabaseTeste
from datetime import datetime  # Corrige o erro do datetime
from django.http import HttpResponse  # Para tipagem correta
import re


def index(request):
    return render(request, "index_consultaOficial.html")


def criaQueryDatabase(filters=None, order_by=None):
    if DatabaseTeste:
        database = "consultaOficial_databaseteste"
    else:
        database = "SICAM.MATERIAL"
    query = f"""
    SELECT CO_MAT,
           DE_MAT,
           QT_SALDO_ATU
    FROM {database}
    """

    if DatabaseTeste:
        query += "WHERE CAST(CO_MAT AS TEXT) LIKE '30%'"
    else:
        query += "WHERE TO_CHAR(CO_MAT) LIKE '30%'"

    if (
        filters and len(filters) > 0
    ):  # Filters vai ser uma string com todos os filtros (vai concatenar no WHERE)
        query += filters

    if order_by:  # Por segurança
        query += order_by

    # query += " FETCH FIRST 1000 ROWS ONLY" # temp
    return query


# View to fetch data from the external API
def fetch_data(queryCriada, flag_TestarConexaoDatabase=False):
    if DatabaseTeste:
        temp = {}
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(queryCriada)
            temp["rows"] = cursor.fetchall()  # Fetch all rows
        return temp
    else:
        import requests
        import json
        import os
        from dotenv import load_dotenv

        # Carrega variáveis do .env
        load_dotenv()

        # Lê usuário e senha do banco
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")

        if not db_user or not db_password:
            raise ValueError(
                "As variáveis DB_USER e DB_PASSWORD devem estar definidas no arquivo .env"
            )

        # Configurações da requisição
        url = "http://172.22.3.197:5011/api/query"
        headers = {"Content-Type": "application/json"}

        # Adicionando a condicional para ou filtrar ou so testar a conexao
        if not flag_TestarConexaoDatabase:
            # Nova consulta SQL
            query = queryCriada
        else:
            # So testar a conexao
            query = "SELECT USER FROM DUAL;"
        # print(query) # debug

        # Corpo da requisição
        payload = {"db_user": db_user, "db_password": db_password, "sql_query": query}

        # Envio da requisição
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                data = response.json()
                # print(data)
                return data
            else:
                error_data = response.json()
                # print(f"Erro: {error_data.get('error', 'Erro ao executar a consulta.')}")
                return (
                    f"Erro: {error_data.get('error', 'Erro ao executar a consulta.')}"
                )
        except Exception as e:
            print(f"Erro: {str(e)}")
            return e


def SQLparaList(data):
    if data is None or isinstance(data, Exception) or "rows" not in data:
        error_msg = (
            str(data.get("error", "Erro desconhecido"))
            if isinstance(data, dict)
            else str(data)
        )
        with open("ErrosBD.txt", "a", encoding="UTF-8") as file:
            file.write(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{error_msg}\n\n"
            )
        return None


def sanitize_input(input_str):
    import re

    """Sanitize input to prevent SQL injection (basic sanitization)."""
    if input_str:
        # Remove any potentially harmful characters (e.g., semicolons, quotes, etc.)
        sanitized = re.sub(r"[;'\"]", "", input_str)  # remove semicolons and quotes
        return sanitized
    return input_str


def intValido(valor) -> bool:
    try:
        int(valor)
        return True
    except Exception:
        return False


### lista com filtro
def material_pesquisa(request):
    from django.core.paginator import Paginator
    from django.contrib import messages

    # Leitura dos parâmetros de filtro
    codigo = request.GET.get("codigo")
    descricao = request.GET.get("descricao")
    saldo_filter = request.GET.get("saldo_filter")
    saldo = request.GET.get("saldo")
    saldoMax = request.GET.get("saldo_between_end")

    # Construa a query com filtros
    filters = ""
    if codigo:
        filters += f" AND CO_MAT LIKE '{codigo}%'"
    if descricao:
        filters += f" AND DE_MAT LIKE '%{descricao}%'"
    if saldo_filter and saldo:
        if saldo_filter == "menorq":
            filters += f" AND QT_SALDO_ATU < {saldo}"
        elif saldo_filter == "maiorq":
            filters += f" AND QT_SALDO_ATU > {saldo}"
        elif saldo_filter == "igual":
            filters += f" AND QT_SALDO_ATU = {saldo}"
        elif saldo_filter == "entre" and saldoMax:
            filters += f" AND QT_SALDO_ATU BETWEEN {saldo} AND {saldoMax}"

    # Acesso ao banco de dados
    query = criaQueryDatabase(filters)
    materials = fetch_data(query)

    # Verifique se materials é None antes de continuar
    if materials is None:
        messages.error(request, "Erro ao carregar o banco de dados")
        return render(request, "material_pesquisa.html", {"page_obj": []})

    # Converta os dados para o formato esperado pelo template
    converted_data = []
    if isinstance(materials, dict) and "rows" in materials:
        for row in materials["rows"]:
            converted_data.append(
                {
                    "codigo": str(row[0]),  # CO_MAT
                    "descricao": row[1],  # DE_MAT
                    "saldo": row[2],  # QT_SALDO_ATU
                }
            )

    # Paginação
    try:
        paginator = Paginator(converted_data, 20)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(
            request,
            "material_pesquisa.html",
            {"page_obj": page_obj, "flagUltimoUso": False},
        )
    except Exception as e:
        messages.error(request, f"Erro na paginação: {str(e)}")
        return render(request, "material_pesquisa.html", {"page_obj": []})


### lista com filtro FIM
@require_GET
def material_pesquisa2(request):
    try:
        # Parâmetros de paginação
        page_number = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        # Construir query com ORM
        queryset = DatabaseTeste.objects.all()

        # Aplicar filtros
        cod_filter = request.GET.get("codigo", "")
        desc_filter = request.GET.get("descricao", "")
        saldo_filter = request.GET.get("saldo_filter", "")
        saldo_value = request.GET.get("saldo", "")
        saldo_end = request.GET.get("saldo_between_end", "")

        if cod_filter:
            queryset = queryset.filter(CO_MAT__startswith=cod_filter)

        if desc_filter:
            queryset = queryset.filter(DE_MAT__icontains=desc_filter)

        if saldo_filter and saldo_value:
            saldo_value = int(saldo_value)
            if saldo_filter == "menorq":
                queryset = queryset.filter(QT_SALDO_ATU__lt=saldo_value)
            elif saldo_filter == "maiorq":
                queryset = queryset.filter(QT_SALDO_ATU__gt=saldo_value)
            elif saldo_filter == "igual":
                queryset = queryset.filter(QT_SALDO_ATU=saldo_value)
            elif saldo_filter == "entre" and saldo_end:
                queryset = queryset.filter(
                    QT_SALDO_ATU__range=(saldo_value, int(saldo_end))
                )

        # Paginação
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page_number)

        # Serializar dados
        results = [
            {
                "codigo": str(item.CO_MAT),
                "descricao": item.DE_MAT,
                "saldo": item.QT_SALDO_ATU,
            }
            for item in page_obj
        ]

        if request.path == "/materiaisPesquisa/":
            return render(
                request,
                "material_pesquisa.html",
                {
                    "page_obj": page_obj,
                    "flagUltimoUso": False,  # Ou True, conforme necessário
                },
            )

        return JsonResponse(
            {
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "results": results,
                "current_page": page_obj.number,
            }
        )

    except Exception as e:
        if request.path == "/materiaisPesquisa/":
            return render(request, "material_pesquisa.html", {"error": str(e)})
        return JsonResponse({"error": str(e)}, status=500)
