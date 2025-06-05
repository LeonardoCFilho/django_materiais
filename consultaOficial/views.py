from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.http import Http404
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET
from django.utils import timezone
from datetime import datetime
import logging
logger = logging.getLogger("consulta")



def index(request):
    return render(request, "index_consultaOficial.html")

#
## Consulta de materiais
### Funções para padronização da saída
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
                'tipoValor': strParaDatetime,
            },
            {
                'nomeColuna': "prazoPassadoLinha",
                'tipoValor': int,
            },
        ],

        # Lista para a consulta do uso medio de materiais
        "consultaUsoMedioMateriais":[
            {
                'nomeColuna': "codigo",
                'tipoValor': str,
            },
            {
                'nomeColuna': "qtdRequisitada",
                'tipoValor': int,
            },
            {
                'nomeColuna': "dataRequisicao",
                'tipoValor': strParaDatetime,
            },
            {
                'nomeColuna': "prazoPassadoLinha",
                'tipoValor': int,
            },
        ],                
    }

    if key not in dictGeral:
        raise KeyError(f"Chave requisitada {key} não existe no dicionario de referencia")
    return dictGeral[key]


def SQLparaList(data, paramList:list[dict]) -> list[dict]|None:
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
### Funções para padronização da saída - END


### Funções para filtrar
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
                case "prazoPassadoLinha":
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
        "prazoPassadoLinha": tiposFiltros.get('prazoPassadoLinha'),
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


def strParaDatetime(data:str) -> datetime:
    """
    Converts a GMT datetime string to the local timezone defined in Django's settings.

    :param data: The datetime string in GMT, e.g., "Wed, 26 Mar 2025 15:48:14 GMT"
    :return: A timezone-aware datetime object in the local timezone
    """
    from datetime import timezone as datetime_timezone
    # Convert the string to a naive datetime object (no timezone)
    date_obj = datetime.strptime(data, "%a, %d %b %Y %H:%M:%S GMT")
    
    # Make the datetime aware by setting it to UTC (since it's GMT)
    date_obj = timezone.make_aware(date_obj, datetime_timezone.utc)
    
    # Convert the UTC datetime to the local timezone
    local_time = date_obj.astimezone(timezone.get_current_timezone())
    
    return local_time
### Funções para filtrar - END
## Consulta de materiais - END
#


# 
## Funções gerais 
def lidarErrosGenericos(erro:Exception, mensagemCustomizada:str = None) -> str:
    from requests.exceptions import Timeout, RequestException

    # Fazer log e qualquer outra operação
    logger.error([type(erro),erro]) 

    # Retornar as mensagens
    if mensagemCustomizada:
        return mensagemCustomizada
    
    match erro:
        case ValueError():
            mensagem_erro = "O código de materiais deve começar com '30'."
        case Http404():
            mensagem_erro = "Erro na busca de materiais"
        case Timeout():
            mensagem_erro = "Timeout tentando conectar com o banco de dados\nTente novamente em breve."
        case RequestException():
            mensagem_erro = "Não foi possível estabelecer uma conexão com o servidor. Verifique a conexão."
        case _:
            mensagem_erro = f"Erro ao carregar o banco de dados.\nErro inesperado: {str(erro)}."
    return mensagem_erro


def determinarRenderDjango(request) -> bool:
    """
    Retorna True se o site está sendo executado pelo Django ou 
    Retorna False se o site está sendo executado pelo React
    """
    wants_json = "application/json" in request.headers.get("Accept", "")
    if wants_json or request.path.startswith("/api/"):
        return False
    return True
## Funções gerais - END
#


#
## API de acesso ao banco de dados Oracle
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


def acessarDatabaseOracle(paramGeral: dict, tipoAcesso:str, useExtraSQL:bool = False) -> list[dict]:
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
                    "prazoPassadoLinha": "ROUND(MATERIAL_VALIDADE.SIMA_DT_VALIDADE - SYSDATE)",                
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
                dictFiltros = { 
                    "codigo": "MOVIMENTO_SAIDA_DEFINITIVO.CO_MAT",
                    "prazoPassadoLinha": "ROUND(MOVIMENTO_SAIDA_DEFINITIVO.DT_BAIXA_REQ - SYSDATE)",               
                }
                queryInicialDB = """
SELECT 
    MOVIMENTO_SAIDA_DEFINITIVO.CO_MAT,
    MOVIMENTO_SAIDA_DEFINITIVO.NU_REQ,
    MOVIMENTO_SAIDA_DEFINITIVO.DT_BAIXA_REQ,
    ROUND(MOVIMENTO_SAIDA_DEFINITIVO.DT_BAIXA_REQ - SYSDATE) AS dias_diff
FROM 
    SICAM.MOVIMENTO_SAIDA_DEFINITIVO
WHERE 
    TO_CHAR(MOVIMENTO_SAIDA_DEFINITIVO.CO_MAT) LIKE '30%'
"""

            case _:
               raise KeyError("tipoAcesso invalido")
        
        # Criar a query SQL
        SQL_filtros_order = criarFiltrosSQL(paramGeral, dictFiltros)
        query = str(queryInicialDB + SQL_filtros_order[0] + SQL_filtros_order[1])
        if useExtraSQL:
            query += " FETCH FIRST 1 ROWS ONLY"

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
## API de acesso ao banco de dados Oracle - END
#


#
## Consulta geral de materiais
@require_GET
def material_pesquisa2(request):
    """
    Returns:
        list de dict, padrão dict:
        {
            'codigo': str, 
            'descricao': str, 
            'saldo': int
        }
        Ex.:
        {
            'codigo': '3010006034', 
            'descricao': 'ABAIXADOR DE LÍNGUA, DE MADEIRA, PACOTE COM 100 UNIDADES', 
            'saldo': 0
        }
    """

    # Logica de login


    # Detectar se é django ou react
    flagRenderDjango = determinarRenderDjango(request)
    ## Se flagRenderDjango for True então vai ser o .html do Django
    ## Se não então será enviado o json para o react
    
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
            "usoDesuso": request.GET.get("usoDesuso", "uso") or "",
            # Ordenação
            "ordemOrdenacao": request.GET.get("ordemOrdenacao", "c") or "c",
            "campoOrdenacao": request.GET.get("campoOrdenacao", "descricao") or "descricao",
        }

        # Acessando o banco de dados
        queryset = acessarDatabaseOracle(param, "consultaGeralMateriais")

        # Caso de erro
        if queryset is None:
            raise Http404("Erro ao buscar o material")

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
                "results": list(page_obj.object_list),  # Apenas os resultados da página atual
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
## Consulta geral de materiais - END
#


#
## Consulta de validade de materiais
@require_GET
def consultaValidadeMateriais(request):
    """
    Returns:
        list de dict, padrão dict:
        {
            'codigo': str, 
            'descricao': str, 
            'saldo': int, 
            'dataValidade': datetime.datetime,
            'prazoPassadoLinha': int
        }
        Ex.:
        {
            'codigo': '3024045079', 
            'descricao': 'TINTA ACRÍLICA PREMIUM...', 
            'saldo': 4, 
            'dataValidade': datetime.datetime(2026, 2, 28, 21, 0, tzinfo=zoneinfo.ZoneInfo(key='America/Sao_Paulo')),
            'prazoPassadoLinha': 270
        }
    """

    # Logica de login


    # Detectar se é django ou react
    flagRenderDjango = determinarRenderDjango(request)
    ## Se flagRenderDjango for True então vai ser o .html do Django
    ## Se não então será enviado o json para o react
    
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
            "prazoPassadoLinha": request.GET.get("prazoValidade", "") or "",
            # Ordenar do que tem mais prazo ate vencer
            "ordemOrdenacao": request.GET.get("ordemOrdenacao", "d"),
            "campoOrdenacao": request.GET.get("campoOrdenacao", "prazoPassadoLinha"),
        }

        queryset = acessarDatabaseOracle(param, "consultaValidadeMateriais")
        
        # Caso de erro
        if queryset is None:
            raise Http404("Erro ao buscar o material")

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
                "results": list(page_obj.object_list),  # Apenas os resultados da página atual
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
## Consulta de validade de materiais - END
#


#
## Consulta consumo medio
@require_GET
def consultaConsumoMedioMateriais(request):
    """
    Returns:
        dict data com valor da media (data['mediaConsumo']) & list de dict, padrão dict:
        {
            'codigo': str, 
            'qtdRequisitada': int, 
            'dataRequisicao': datetime.datetime, 
            'prazoPassadoLinha': int
        }
        Ex.:
        {
            'codigo': '3016007002', 
            'qtdRequisitada': 60, 
            'dataRequisicao': datetime.datetime(2025, 3, 26, 12, 48, 14, tzinfo=zoneinfo.ZoneInfo(key='America/Sao_Paulo')), 
            'prazoPassadoLinha': -69
        }
    """

    # Logica de login


    # Detectar se é django ou react
    flagRenderDjango = determinarRenderDjango(request)
    ## Se flagRenderDjango for True então vai ser o .html do Django
    ## Se não então será enviado o json para o react
    
    flagExceptionAchada = False

    try:
        # Parâmetros de paginação
        page_number = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        # Aplicar filtros com valores padrão seguros
        param = {
            "codigo": request.GET.get("codigo", "") or "",
            "prazoPassadoLinha": request.GET.get("periodoMedia", "1") or "1", # Converter para mês comercial dps
            # Ordenação
            "ordemOrdenacao": request.GET.get("ordemOrdenacao", "d"),
            "campoOrdenacao": request.GET.get("campoOrdenacao", "prazoPassadoLinha"),
        }

        if param['codigo'] and len(param['codigo']) == 10:
            # Garantir que existe na tabela
            testeParam = dict(param)
            testeParam['prazoPassadoLinha'] = 50*12*30
            testeQueryset = acessarDatabaseOracle(testeParam, "consultaUsoMedioMateriais", True)
            if len(testeQueryset) == 1:
                param['prazoPassadoLinha'] = int(param['prazoPassadoLinha'])*30 # Conversao mencionada
                queryset = acessarDatabaseOracle(param, "consultaUsoMedioMateriais")
            else:
                mensagem_erro = lidarErrosGenericos(ValueError("Produto não existe na tabela"), "O codigo fornecido não está presente na tabela!")
                messages.error(request, mensagem_erro)
                flagExceptionAchada = True
                queryset = []
        else:
            mensagem_erro = lidarErrosGenericos(ValueError("Codigo do produto não foi fornecido"), "O codigo completo do produto deve ser fornecido!")
            messages.error(request, mensagem_erro)
            flagExceptionAchada = True
            queryset = []
        

        # Calcular a media
        somaParaMedia = 0
        for elemento in queryset:
            somaParaMedia += elemento['qtdRequisitada']
        average_camp = round(somaParaMedia / (int(param['prazoPassadoLinha'])/30),2)
        data = {
            'mediaConsumo': average_camp,
        }
        
        # Caso de erro
        if queryset is None:
            raise Http404("Erro ao buscar o material")

        # Paginação
        paginator = Paginator(queryset, page_size)
        ## Removendo um caso de erro
        if page_number > paginator.num_pages:
            page_number = 1 
        page_obj = paginator.get_page(page_number) 

        # Se for django => render a pagina
        if flagRenderDjango:
            return render(request, "material_consumo_medio.html", {"data": data, "page_obj": page_obj,})
        # Se não => json para o react
        return JsonResponse(
            {
                "count": paginator.count,
                "total_pages": paginator.num_pages,
                "results": list(page_obj.object_list),  # Apenas os resultados da página atual
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
            return render(request, "material_consumo_medio.html", {"page_obj": []})
        return JsonResponse({"error": str(mensagem_erro)}, status=500)
## Consulta consumo medio - END
#