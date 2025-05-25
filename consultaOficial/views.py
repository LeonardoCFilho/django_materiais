from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET
from datetime import datetime  # Corrige o erro do datetime


def index(request):
    return render(request, "index_consultaOficial.html")

##
### API de acesso ao banco de dados Oracle
def criaQueryDatabase(filters=None, order_by=None, flagDatabaseTeste=False):
    if flagDatabaseTeste:
        database = "consultaOficial_databaseteste"
    else:
        database = "SICAM.MATERIAL"
    query = f"""
    SELECT CO_MAT,
           DE_MAT,
           QT_SALDO_ATU
    FROM {database}
    """

    if flagDatabaseTeste:
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
def fetch_data(queryCriada, flag_TestarConexaoDatabase=False, flagDatabaseTeste = False):
    if flagDatabaseTeste:
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
    # Salvar o erro
    if "error" in data or isinstance(data, Exception) or "rows" not in data:
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

    novaListDict = []

    for linha in data[
        "rows"
    ]:  # Aparentemente esse é o nome retornado, teria que confimar
        novaListDict.append(
            {
                "codigo": str(linha[0]),
                "descricao": linha[1],
                "saldo": int(linha[2]),
            }
        )

    return novaListDict


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


def criarFiltros(param: dict, flagDatabaseTeste:bool):
    # Filtros
    filters = ''
    ## Filtro por codigo (numerico)
    if param.get("codigo"):
        codigo = param.get("codigo")
        # Garantir que codigo começa com 30 é que é valido (int)
        if codigo.startswith('30') and intValido(codigo):
            if flagDatabaseTeste:
                filters += f" AND CAST(CO_MAT AS TEXT) LIKE '{codigo}%'"
            else:
                filters += f" AND TO_CHAR(CO_MAT) LIKE '{codigo}%'"
        else:
            raise ValueError("O código de materiais deve começar com '30'.")
    ## Filtro por descrição (string)
    if param.get("descricao"):
        descricao = param.get("descricao")
        descricao = sanitize_input(descricao)
        if flagDatabaseTeste:
            filters += f" AND DE_MAT COLLATE NOCASE LIKE '%{descricao}%' "
        else:
            # INSTR
            filters += f""" AND INSTR(
    UPPER(TRANSLATE(DE_MAT,
          'ÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÃÕ',
          'AEIOUAEIOUAEIOUAO')),
    UPPER(TRANSLATE('{descricao}',
          'ÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÃÕ',
          'AEIOUAEIOUAEIOUAO'))
) > 0
"""
    ## Filtro por saldo (int)
    if param.get("saldo_filter") and param.get("saldo"):
        if param.get("saldo_filter") == "menorq": # < x
            filters += f" AND QT_SALDO_ATU < {param.get('saldo')}"
        elif param.get("saldo_filter") == "maiorq": # x >
            filters += f" AND QT_SALDO_ATU > {param.get('saldo')}"
        elif param.get("saldo_filter") == "igual": # x ==
            filters += f" AND QT_SALDO_ATU = {param.get('saldo')}"
        elif param.get("saldo_filter") == "entre" and param.get("saldoMax"): # < x < 
            filters += f" AND QT_SALDO_ATU BETWEEN {param.get('saldo')} AND {param.get('saldoMax')}"

    # Ordenação
    order_by = " ORDER BY CO_MAT ASC "  # Por segurança, para ser mais obvio que tem um erro
    if param.get("campoOrdenacao") and param.get("ordemOrdenacao"):
        ordemOrdenacao = "ASC" if param.get("ordemOrdenacao") == "c" else "DESC"
        colunasDatabase = {
            "codigo": "CO_MAT",
            "descricao": "DE_MAT" if flagDatabaseTeste else f"NLSSORT(DE_MAT, 'NLS_SORT=PORTUGUESE')",
            "saldo": "QT_SALDO_ATU",
        }
        if param.get("campoOrdenacao") in colunasDatabase:
            order_by = f" ORDER BY {colunasDatabase[param.get('campoOrdenacao')]} {ordemOrdenacao} "
    # ORDER BY NLSSORT(name, 'NLS_SORT=PORTUGUESE');
    # ORDER BY NLSSORT(name, 'NLS_SORT=XPORTUGUESE');

    return [filters, order_by]


# Universalizando o uso da API
def acessarDatabaseOracle(paramGeral: dict, flagDatabaseTeste = False):
    try: 
        SQL_parcial = criarFiltros(paramGeral, flagDatabaseTeste=flagDatabaseTeste)
        query = criaQueryDatabase(SQL_parcial[0], SQL_parcial[1], flagDatabaseTeste=flagDatabaseTeste)
        materials = fetch_data(query, flagDatabaseTeste=flagDatabaseTeste)
        return SQLparaList(materials)
    except Exception as e:
        raise e
### API de acesso ao banco de dados Oracle - END
##


#
### Prova de conceito de pesquisa de materiais
def material_pesquisa(request):
    from django.core.paginator import Paginator
    from django.contrib import messages

    # Leitura dos parâmetros de filtro
    param = {
        "codigo": request.GET.get("codigo"),
        "descricao": request.GET.get("descricao"),
        "saldo_filter": request.GET.get("saldo_filter"),
        "saldo": request.GET.get("saldo"),
        "saldoMax": request.GET.get("saldo_between_end"),
        "ordemOrdenacao": request.GET.get("ordemOrdenacao", "c"),
        "campoOrdenacao": request.GET.get("campoOrdenacao", "descricao"),
    }

    # Acesso ao banco de dados
    sufixo_url = request.path  
    sufixo_url = str(sufixo_url).split("/materiaisPesquisa/")[-1]
    flagDatabaseTeste = "TESTE" in sufixo_url
    #print(flagDatabaseTeste)
    try:
        materials = None
        materials = acessarDatabaseOracle(param, flagDatabaseTeste)
    except ValueError as e:
        messages.error(request, "O código de materiais deve começar com '30'.")
    # ...

    # Verifique se materials é None antes de continuar
    if materials is None:
        messages.error(request, "Erro ao carregar o banco de dados")
        return render(request, "material_pesquisa.html", {"page_obj": []})

    # materials existe => renderizar a pagina com a lista
    # Paginação
    try:
        paginator = Paginator(materials, 20)
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


### Prova de conceito de pesquisa de materiais - END
#


### lista com filtro FIM
@require_GET
def material_pesquisa2(request):
    try:
        # Parâmetros de paginação
        page_number = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        # Aplicar filtros com valores padrão seguros
        param = {
            "codigo": request.GET.get("codigo", "") or "",
            "descricao": request.GET.get("descricao", "") or "",
            "saldo_filter": request.GET.get("saldo_filter", "") or "",
            "saldo": request.GET.get("saldo", "") or "",
            "saldoMax": request.GET.get("saldo_between_end", "") or "",
            "ordemOrdenacao": request.GET.get("ordemOrdenacao", "c") or "c",
            "campoOrdenacao": request.GET.get("campoOrdenacao", "descricao") or "descricao",
        }

        # Acessando o banco de dados
        flagDatabaseTeste = True
        queryset = acessarDatabaseOracle(param, flagDatabaseTeste)

        # Se não houver resultados ou ocorrer erro, retornar lista vazia
        if not queryset:
            queryset = []

        # Paginação
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page_number)

        # Serializar dados  modificado para lidar com diferentes formatos de dados
        results = []
        for item in page_obj:
            # Verifica se é um objeto DatabaseTeste ou um dicionário
            if hasattr(item, "CO_MAT"):
                results.append(
                    {
                        "codigo": str(item.CO_MAT),
                        "descricao": item.DE_MAT,
                        "saldo": item.QT_SALDO_ATU,
                    }
                )
            elif isinstance(item, dict):
                results.append(
                    {
                        "codigo": str(item.get("codigo", "")),
                        "descricao": item.get("descricao", ""),
                        "saldo": item.get("saldo", 0),
                    }
                )

        if request.path == "/materiaisPesquisa/":
            return render(
                request,
                "material_pesquisa.html",
                {
                    "page_obj": page_obj,
                    "flagUltimoUso": False,
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
            return render(
                request, "material_pesquisa.html", {"error": str(e), "page_obj": []}
            )
        return JsonResponse({"error": str(e)}, status=500)
