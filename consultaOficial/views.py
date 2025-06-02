from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET
import logging
logger = logging.getLogger("consulta")



def index(request):
    return render(request, "index_consultaOficial.html")

#
### Consulta de materiais
def returnListParametrosSQL(key:str) -> list[dict]:
    dictGeral = {
        # Lista para a tela de consulta materiais
        'consultaGeralMateriais': [
            {
                'nomeColuna': "codigo",
                'tipoValor': str,
            },
            {
                'nomeColuna': "descricao",
                'tipoValor': str,
            },
            {
                'nomeColuna': "saldo",
                'tipoValor': int,
            },
        ],

        # Lista para a consulta da validade de materiais
        "consultaValidadeMateriais": [
            {
                'nomeColuna': "codigo",
                'tipoValor': str,
            },
            {
                'nomeColuna': "descricao",
                'tipoValor': str,
            },
            {
                'nomeColuna': "saldo",
                'tipoValor': int,
            },
            {
                'nomeColuna': "dataValidade",
                'tipoValor': str,
            },
            {
                'nomeColuna': "prazoValidade",
                'tipoValor': int,
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
    #print(param) # debug
    listaFiltros = []
    for key, value in param.items():
        if key in tiposFiltros:
            ## Filtro por codigo (numerico)
            match key:
                case "codigo":
                    if value:
                        # Garantir que codigo começa com 30 é que é valido (int)
                        if intValido(value) and str(value).startswith('30'):
                            listaFiltros.append(f"TO_CHAR({tiposFiltros[key]}) LIKE '{value}%'")
                        else:
                            raise ValueError("O código de materiais deve começar com '30'.")
            
                ## Filtro por descrição (string)
                case "descricao":
                    if value:
                        listaFiltros.append(f"""INSTR(
                            UPPER(TRANSLATE({tiposFiltros[key]},
                                'ÇÇççÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÃÕ,.:;',
                                'CCCCAEIOUAEIOUAEIOUAO    ')),
                            UPPER(TRANSLATE('{sanitize_input(value)}',
                                'ÇÇççÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÃÕ,.:;',
                                'CCCCAEIOUAEIOUAEIOUAO    '))
                            ) > 0
                            """)
                
                ## Filtro por saldo (int)
                case "saldo":
                    if param.get("saldo_filter") and value:
                        if param.get("saldo_filter") == "menorq": # < x
                            listaFiltros.append(f"{tiposFiltros[key]} < {value}")
                        elif param.get("saldo_filter") == "maiorq": # x >
                            listaFiltros.append(f"{tiposFiltros[key]} > {value}")
                        elif param.get("saldo_filter") == "igual": # x ==
                            listaFiltros.append(f"{tiposFiltros[key]} = {value}")
                        elif param.get("saldo_filter") == "entre" and param.get("saldoMax"): # < x < 
                            listaFiltros.append(f"{tiposFiltros[key]} BETWEEN {value} AND {param.get('saldoMax')}")
    
                ## Filtro por uso
                case "usoDesuso":
                    match value:
                        case "uso":
                            listaFiltros.append(f"{tiposFiltros[key]} IS NULL")
                        case "desuso":
                            listaFiltros.append(f"{tiposFiltros[key]} IS NOT NULL")
                        # Se não => Não fazer nada

                ## Filtro por validade
                case "prazoValidade":
                    if value:
                        listaFiltros.append(f"{tiposFiltros[key]} > {min(0,(-1)*int(value))}")
                
                ## Filtros futuros
                # case "":
            
    # Unir os filtros
    filters = ''
    if listaFiltros:
        filters = " AND " + " AND ".join(listaFiltros)
    #print(filters)

    ## Ordenação
    order_by = '' # Por segurança
    
    # Com certeza existem os atributos de ordenação
    ordemOrdenacao = "ASC" if param.get("ordemOrdenacao") == "c" else "DESC"
    colunasDatabase = {
        "codigo": tiposFiltros.get('codigo'),
        "descricao": f"NLSSORT(REGEXP_REPLACE({tiposFiltros.get('descricao')}, '^[[:space:]]+', ''), 'NLS_SORT=WEST_EUROPEAN_AI')",
        "saldo": tiposFiltros.get('saldo'),
        "prazoValidade": tiposFiltros.get('prazoValidade'),
        # Prazo de validade
    }
    
    
    if param.get("campoOrdenacao") in colunasDatabase and tiposFiltros.get(param.get("campoOrdenacao")) is not None:
        order_by = f" ORDER BY {colunasDatabase[param.get('campoOrdenacao')]} {ordemOrdenacao} "
    
    return [filters, order_by]


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


def lidarErrosGenericos(erro:Exception) -> str:
    from requests.exceptions import Timeout, RequestException
    logger.error([type(erro),erro])
    match erro:
        case ValueError():
            mensagem_erro = "O código de materiais deve começar com '30'."
        case Timeout():
            mensagem_erro = "Timeout tentando conectar com o banco de dados\nTente novamente em breve."
        case RequestException():
            mensagem_erro = "Não foi possível estabelecer uma conexão com o servidor. Verifique a conexão."
        case _:
            mensagem_erro = "Erro ao carregar o banco de dados."
    return mensagem_erro
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
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
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
SELECT  
    CO_MAT,
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
                dictFiltros = { 
                    "codigo": "MATERIAL.CO_MAT",
                    "descricao": "MATERIAL.DE_MAT",
                    "saldo": "MATERIAL.QT_SALDO_ATU",
                    "prazoValidade": "ROUND(MATERIAL_VALIDADE.SIMA_DT_VALIDADE - SYSDATE)",                
                }
                queryInicialDB = """
SELECT 
    MATERIAL.CO_MAT,
    MATERIAL.DE_MAT,
    MATERIAL.QT_SALDO_ATU,
    MATERIAL_VALIDADE.SIMA_DT_VALIDADE,
    ROUND(MATERIAL_VALIDADE.SIMA_DT_VALIDADE - SYSDATE) AS dias_diff
FROM 
    SICAM.MATERIAL
INNER JOIN 
    SICAM.MATERIAL_VALIDADE
ON 
    MATERIAL.CO_MAT = MATERIAL_VALIDADE.SIMA_CO_MAT
WHERE 
    TO_CHAR(MATERIAL.CO_MAT) LIKE '30%'
"""

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
            logger.error([type(e),e]) # Registrar erro        
            raise e
    
    except Exception as e:
       logger.error([type(e),e])
       raise e
### API de acesso ao banco de dados Oracle - END
#


#
### Consulta geral de materiais
@require_GET
def material_pesquisa2(request):

    # Logica de login


    # Detectar se é django ou react
    wants_json = request.headers.get("Accept") == "application/json" or request.path.startswith("/api/")
    flagRenderDjango = not wants_json or request.path == "/materiaisPesquisa/"
    # Se flagRenderDjango for True então vai ser o .html do Django
    # Se não então será enviado o json para o react
    flagExceptionAchada = False

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
            "usoDesuso": request.GET.get("usoDesuso", "uso") or ""
        }

        # Acessando o banco de dados
        queryset = acessarDatabaseOracle(param, "consultaGeralMateriais")

        # Se não houver resultados ou ocorrer erro, retornar lista vazia
        if not queryset:
            queryset = []

        # Paginação
        paginator = Paginator(queryset, page_size)
        ## Removendo um caso de erro
        if page_number > paginator.num_pages:
            page_number = 1 
        page_obj = paginator.get_page(page_number) 

        # Se for django => render a pagina
        if flagRenderDjango:
            return render(request, "material_pesquisa.html", {"page_obj": page_obj,})
        # Se não => json para o react
        return JsonResponse(
            {
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "results": queryset,
                "current_page": page_obj.number,
            }
        )

    except Exception as e: # Dependendo especificar mais
        mensagem_erro = lidarErrosGenericos(e)
        messages.error(request, mensagem_erro)
        flagExceptionAchada = True

    # Deu erro => renderizar especial
    if flagExceptionAchada:
        if flagRenderDjango:
            return render(request, "material_pesquisa.html", {"page_obj": []})
        return JsonResponse({"error": str(mensagem_erro)}, status=500)
### Consulta geral de materiais - END
#


#
### Consulta de validade de materiais
@require_GET
def consultaValidadeMateriais(request):

    # Logica de login


    # Detectar se é django ou react
    wants_json = request.headers.get("Accept") == "application/json" or request.path.startswith("/api/")
    flagRenderDjango = not wants_json or request.path == "/materiaisValidade/"
    # Se flagRenderDjango for True então vai ser o .html do Django
    # Se não então será enviado o json para o react
    flagExceptionAchada = False

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
            "prazoValidade": request.GET.get("prazoValidade", "") or "",
            # Ordenar do que tem mais prazo ate vencer
            "ordemOrdenacao": request.GET.get("ordemOrdenacao", "d"),
            "campoOrdenacao": request.GET.get("campoOrdenacao", "prazoValidade"),
        }

        queryset = acessarDatabaseOracle(param, "consultaValidadeMateriais")
        if not queryset:
            queryset = []

        # Paginação
        paginator = Paginator(queryset, page_size)
        ## Removendo um caso de erro
        if page_number > paginator.num_pages:
            page_number = 1 
        page_obj = paginator.get_page(page_number) 

        # Se for django => render a pagina
        if flagRenderDjango:
            return render(request, "material_validade.html", {"page_obj": page_obj,})
        # Se não => json para o react
        return JsonResponse(
            {
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "results": queryset,
                "current_page": page_obj.number,
            }
        )

    except Exception as e: # Dependendo especificar mais
        mensagem_erro = lidarErrosGenericos(e)
        messages.error(request, mensagem_erro)
        flagExceptionAchada = True

    # Deu erro => renderizar especial
    if flagExceptionAchada:
        if flagRenderDjango:
            return render(request, "material_validade.html", {"page_obj": []})
        return JsonResponse({"error": str(mensagem_erro)}, status=500)

### Consulta de validade de materiais - END
#