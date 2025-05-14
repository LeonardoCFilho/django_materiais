from django.shortcuts import render

def index(request):
    return render(request, 'index_consultaOficial.html')

# View to fetch data from the external API
def fetch_data(filters = None, order_by = None, flag_TestarConexaoDatabase = False):
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
    url = 'http://172.22.3.197:5011/api/query'
    headers = {'Content-Type': 'application/json'}

    # Adicionando a condicional para ou filtrar ou so testar a conexao
    if not flag_TestarConexaoDatabase:
        # Nova consulta SQL
        query = f"""
        SELECT CO_MAT,
               DE_MAT,
               QT_SALDO_ATU
        FROM SICAM.MATERIAL
        WHERE TO_CHAR(CO_MAT) LIKE '30%' 
        """
        if filters and len(filters) > 0: # Filters vai ser uma string com todos os filtros (vai concatenar no WHERE)
            query += filters

        if order_by: # Por segurança
            query += order_by

        query += " FETCH FIRST 1000 ROWS ONLY" # temp

    else:
        # So testar a conexao
        query = "SELECT USER FROM DUAL;"
    #print(query) # debug

    # Corpo da requisição
    payload = {
        'db_user': db_user,
        'db_password': db_password,
        'sql_query': query
    }

    # Envio da requisição
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            #print(data)
            return data
        else:
            error_data = response.json()
            #print(f"Erro: {error_data.get('error', 'Erro ao executar a consulta.')}")
            return f"Erro: {error_data.get('error', 'Erro ao executar a consulta.')}"
    except Exception as e:
        print(f"Erro: {str(e)}")
        return e

def SQLparaList(data):
    # Salvar o erro
    if 'error' in data or isinstance(data, Exception) or 'rows' not in data:
        from datetime import datetime
        with open("ErrosBD.txt",'a',encoding='UTF-8') as file:
            file.write(f"""f{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{data['error']}\n\n""")
        return None 

    novaListDict = []

    for linha in data['rows']: # Aparentemente esse é o nome retornado, teria que confimar
        novaListDict.append({
            'codigo': str(linha[0]),
            'descricao': linha[1],
            'saldo': int(linha[2]),
        })

    return novaListDict

# Temp para testar o frontEnd
def criaListaTeste():
    import random
    lista = []
    sujeitos = ["O cachorro", "A garota", "O professor", "A mãe", "O carro", "O cientista", "O político", "A estrela"]
    verbos = ["corre", "estuda", "fala", "viaja", "compreende", "brinca", "diz", "ajuda"]
    objetos = ["na rua", "com os amigos", "no trabalho", "na escola", "para casa", "no parque", "para o futuro", "ao mundo"]
    for _ in range(100):
        lista.append({
            'codigo': str(random.randint(int(3e9), int(3.1e9))),
            'descricao': random.choice(sujeitos) +' '+ random.choice(verbos) +' '+ random.choice(objetos),
            'saldo': random.randint(1, 100),
        })
    return lista

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

    # Fazer a logica de login => Não está loggado -> redirect para outra página
    # <login>

    # Fazer a logica de permissões
    # <permissões>
    
    # temp
    #if not request.session.get('flagUltimoUso', None):
    #    request.session['flagUltimoUso'] = request.GET.get('flagUltimoUso', 'false').lower() == 'true' 

    # Leitura do html
    codigo = request.GET.get('codigo')
    descricao = request.GET.get('descricao')
    saldo_filter = request.GET.get('saldo_filter')
    saldo = request.GET.get('saldo')
    saldoMax = request.GET.get('saldo_between_end')
    # Ordenação padrão vai ser por código (crescente)
    ordemOrdenacao = request.GET.get('ordemOrdenacao', 'c')
    campoOrdenacao = request.GET.get('campoOrdenacao', 'codigo')

    # para teste do frontend
    #materials = criaListaTeste()

    # Acesso ao banco de dados oficial
    materials = fetch_data(flag_TestarConexaoDatabase=True)
    filters = ''

    if materials:
        # Filtros
        ## Filtro por codigo (numerico)
        if codigo:
            # Garantir que codigo começa com 30 é que é valido (int)
            if codigo.startswith('30') and intValido(codigo):
                filters += f" AND TO_CHAR(CO_MAT) LIKE '{codigo}%'"
            else:
                messages.error(request, "O código de materiais deve começar com '30'.")
        ## Filtro por descrição (string)
        if descricao:
            descricao = sanitize_input(descricao)
            # INSTR
            filters += f" AND INSTR(NLSSORT(DE_MAT, 'NLS_SORT = BINARY_AI'), NLSSORT('{descricao}', 'NLS_SORT = BINARY_AI')) > 0"
        ## Filtro por saldo (qtd)
        if saldo_filter and saldo and intValido(saldo):
            saldo = int(saldo)
            match saldo_filter:
                case 'menorq': # <
                    filters += f" AND QT_SALDO_ATU < {saldo}"
                case 'igual': # =
                    filters += f" AND QT_SALDO_ATU = {saldo}"
                case 'maiorq': # >
                    filters += f" AND QT_SALDO_ATU > {saldo}"
                case 'entre':
                    if saldoMax and intValido(saldoMax):
                        filters += f" AND column_name BETWEEN {saldo} AND {int(saldoMax)}"

        # Ordenação
        order_by = " ORDER BY DE_MAT ASC " 
        if campoOrdenacao and ordemOrdenacao:
            ordemOrdenacao = "ASC" if ordemOrdenacao == 'c' else "DESC"
            colunasDatabase = {
                'codigo': 'CO_MAT',
                'descricao': 'DE_MAT',
                'saldo': 'QT_SALDO_ATU',
            }
            if campoOrdenacao in colunasDatabase:
                order_by = f" ORDER BY {colunasDatabase[campoOrdenacao]} {ordemOrdenacao} "
        
        # Filters pode ou não ser '' e order_by pode ou não ser None
        # fetch_data está preparada para os dois
        materials = SQLparaList(fetch_data(filters, order_by))
    else:
        return messages.error(request, "Erro ao carregar o banco de dados")
    
    # Paginação
    paginator = Paginator(materials, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'material_pesquisa.html', {'page_obj': page_obj})
### lista com filtro FIM
