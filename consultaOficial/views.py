from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET
import logging
logger = logging.getLogger("consulta")



def index(request):
    return render(request, "index_consultaOficial.html")

#
### Consulta de materiais
def SQLparaList(data, paramList:list[dict] = None) -> list[dict]|None:
    # Caso de erro
    if not data or "error" in data or "rows" not in data:
        logger.error(data)
        return None

    # Criar lista com novas chaves
    novaListDict = []
    for linha in data['rows']:
        # Criar dict equivalente a linha do json recebido
        dictNovaLinha = {}
        for i, param in enumerate(paramList):
            dictNovaLinha[param['nomeColuna']] = param['tipoValor'](linha[i])
        novaListDict.append(dictNovaLinha)

    return novaListDict


def criarFiltrosSQL(param: dict, tiposFiltros:dict) -> list[str]:
    ## Filtros
    listaFiltros = []
    for key, value in param.items():
        if key in tiposFiltros:
            ## Filtro por codigo (numerico)
            match key:
                case "codigo":
                    if value:
                        # Garantir que codigo começa com 30 é que é valido (int)
                        if intValido(value) and str(value).startswith('30'):
                            listaFiltros.append(f"TO_CHAR(CO_MAT) LIKE '{value}%'")
                        else:
                            raise ValueError("O código de materiais deve começar com '30'.")
            
                ## Filtro por descrição (string)
                case "descricao":
                    if value:
                        listaFiltros.append(f"""INSTR(
                            UPPER(TRANSLATE(DE_MAT,
                                'ÇÇççÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÃÕ',
                                'CCCCAEIOUAEIOUAEIOUAO')),
                            UPPER(TRANSLATE('{sanitize_input(value)}',
                                'ÇÇççÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÃÕ',
                                'CCCCAEIOUAEIOUAEIOUAO'))
                            ) > 0
                            """)
                
                ## Filtro por saldo (int)
                case "saldo":
                    if param.get("saldo_filter") and value:
                        if param.get("saldo_filter") == "menorq": # < x
                            listaFiltros.append(f"QT_SALDO_ATU < {value}")
                        elif param.get("saldo_filter") == "maiorq": # x >
                            listaFiltros.append(f"QT_SALDO_ATU > {value}")
                        elif param.get("saldo_filter") == "igual": # x ==
                            listaFiltros.append(f"QT_SALDO_ATU = {value}")
                        elif param.get("saldo_filter") == "entre" and param.get("saldoMax"): # < x < 
                            listaFiltros.append(f"QT_SALDO_ATU BETWEEN {value} AND {param.get('saldoMax')}")
    
                ## Filtro por uso
                case "usoDesuso":
                    match value:
                        case "uso":
                            listaFiltros.append("FG_DESUSO IS NULL")
                        case "desuso":
                            listaFiltros.append("FG_DESUSO IS NOT NULL")
                        # Se não => Não fazer nada

                ## Filtro por validade
                # ...
            
    # Unir os filtros
    filters = ''
    if listaFiltros:
        filters = " AND " + " AND ".join(listaFiltros)

    ## Ordenação
    order_by = '' # Por segurança
    if not param.get('campoOrdenacao') or not param.get("ordemOrdenacao"):
        param['campoOrdenacao'] = "descricao"
        param['ordemOrdenacao'] = "ASC"
    
    # Com certeza existem os atributos de ordenação
    ordemOrdenacao = "ASC" if param.get("ordemOrdenacao") == "c" else "DESC"
    colunasDatabase = {
        "codigo": "CO_MAT",
        "descricao": "NLSSORT(REGEXP_REPLACE(DE_MAT, '^[[:space:]]+', ''), 'NLS_SORT=WEST_EUROPEAN_AI')",
        "saldo": "QT_SALDO_ATU",
        # Prazo de validade
    }
    
    if param.get("campoOrdenacao") in colunasDatabase:
        order_by = f" ORDER BY {colunasDatabase[param.get('campoOrdenacao')]} {ordemOrdenacao} "

    return [filters, order_by]


def returnListParametrosSQL(key:str) -> list[dict]:
    dictGeral = {
        # Lista para a tela de consulta materiais
        'consultaGeralMateriais': [
            {
                'nomeColuna': "codigo",
                'tipoValor': str
            },
            {
                'nomeColuna': "descricao",
                'tipoValor': str
            },
            {
                'nomeColuna': "saldo",
                'tipoValor': int
            },
        ],

        # Lista para a consulta da validade de materiais
        "consultaValidadeMateriais": [
            {
                'nomeColuna': "codigo",
                'tipoValor': str
            },
        ],

        # Lista para a consulta do uso medio de materiais
        "consultaUsoMedioMateriais":[
            {
                'nomeColuna': "codigo",
                'tipoValor': str
            },
        ],                
    }
    return dictGeral.get(key, None)


def sanitize_input(input_str:str) -> str:
    """Sanitize input to prevent SQL injection (basic sanitization)."""
    import re
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
### Consulta de materiais - END
#


#
### API de acesso ao banco de dados Oracle
def fetch_data(queryCriada:str, flag_TestarConexaoDatabase:bool=False) -> dict:
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
        raise ValueError("As variáveis DB_USER e DB_PASSWORD devem estar definidas no arquivo .env")

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
            #print(data)
            return data
        else:
            error_data = response.json()
            logger.debug(error_data) # Extra informação no log
            raise requests.exceptions.HTTPError(f"Request falhou, codigo: {response.status_code}")
    except Exception as e:
        raise e


def acessarDatabaseOracle(paramGeral: dict, tipoAcesso:str = "consultaGeralMateriais") -> list[dict]:
    """
    Faz uma query para o banco de dados oracle de acordo com os parametros de entra

    Returns:
        list[dict]: De acordo com a query criada internamente (pode ser vazia)
    """
    try: 
        # Determinar qual será a pesquisa
        match tipoAcesso:
            case "consultaGeralMateriais":
                # Esse dict será usada para transformar os GETs em colunas do BD
                dictFiltros = { 
                    "codigo": "CO_MAT",
                    "descricao": "DE_MAT",
                    "saldo": "QT_SALDO_ATU",
                    "usoDesuso": "FG_DESUSO",                
                }
                queryInicialDB = """
SELECT  CO_MAT,
        DE_MAT,
        QT_SALDO_ATU
FROM SICAM.MATERIAL
WHERE TO_CHAR(CO_MAT) LIKE '30%'
    AND DE_MAT IS NOT NULL
    AND REGEXP_LIKE(TRIM(DE_MAT)  -- tira espaços iniciais
        , '^[[:alnum:]]'  -- 1.ª posição é letra/díg.
    )
"""

            case "consultaValidadeMateriais":
                ...

            case "consultaUsoMedioMateriais":
                ...

            case _:
               raise KeyError("tipoAcesso invalido")
        
        # Criar a query SQL
        SQL_filtros_order = criarFiltrosSQL(paramGeral, dictFiltros)
        query = str(queryInicialDB + SQL_filtros_order[0] + SQL_filtros_order[1])

        # Solicitar ao banco de dados (read-only)
        try:
            materials = fetch_data(query)
            return SQLparaList(materials, returnListParametrosSQL(tipoAcesso)) # Pode retornar uma lista vazia
        
        except Exception as e:
            logger.error(e) # Registrar erro        
            raise e
    
    except Exception as e:
       logger.error(e)
       raise e
### API de acesso ao banco de dados Oracle - END
#


#
### Prototipo backend para consulta de materiais
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
        "usoDesuso": request.GET.get("usoDesuso", "uso"), # Padrão ser materiais em uso
        "ordemOrdenacao": request.GET.get("ordemOrdenacao", "c"),
        "campoOrdenacao": request.GET.get("campoOrdenacao", "descricao"),
    }

    try:
        materials = None
        materials = acessarDatabaseOracle(param)
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

#
### Frontend, consulta de materiais
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
        queryset = acessarDatabaseOracle(param)

        # Se não houver resultados ou ocorrer erro, retornar lista vazia
        if not queryset:
            queryset = []

        # Paginação
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page_number)

        # Serializar dados  modificado para lidar com diferentes formatos de dados
        results = []
        for item in page_obj:
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
### Frontend, consulta de materiais - END
#