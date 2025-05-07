from django.shortcuts import render

def index(request):
    return render(request, 'index_consultaOficial.html')

# View to fetch data from the external API
def fetch_data(argsQuery):
    import requests
    import json
    from django.conf import settings
    from django.http import JsonResponse
    from dotenv import load_dotenv

    load_dotenv()  
    # Get DB credentials from environment variables
    db_user = settings.DB_USER
    db_password = settings.DB_PASSWORD

    if not db_user or not db_password:
        return JsonResponse({"error": "Database credentials are missing."}, status=400)

    # External API endpoint and headers
    url = 'http://172.22.3.31:5011/api/query'
    headers = {'Content-Type': 'application/json'}

    # The SQL query to be sent to the API
    query = f"""
    SELECT CO_MAT,
           DE_MAT,
           QT_SALDO_ATU
    FROM SICAM.MATERIAL
    WHERE TO_CHAR(CO_MAT) LIKE '30%'
      AND QT_SALDO_ATU > 0
    ORDER BY DE_MAT
    FETCH FIRST {argsQuery['numLinhas']} ROWS ONLY
    """

    # Prepare the request payload
    payload = {
        'db_user': db_user,
        'db_password': db_password,
        'sql_query': query
    }

    try:
        # Send the request to the external API
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # If the request is successful
        if response.status_code == 200:
            data = response.json()

            return JsonResponse(data, safe=False)
        else:
            # If there's an error, return an error message
            error_data = response.json()
            return JsonResponse({"error": error_data.get('error', 'Failed to fetch data.')}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def SQLparaList(data):
    # Salvar o erro
    if 'error' in data:
        from datetime import datetime
        with open("ErrosBD.txt",'a',encoding='UTF-8') as file:
            file.write(f"""f{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{data['error']}\n\n""")
        return None 


    novaListDict = []

    for linha in data['rows']: # Aparentemente esse é o nome retornado, teria que confimar
        novaListDict.append({
            'codigo': linha[0],
            'descricao': linha[1],
            'saldo': linha[2],
        })

    return novaListDict

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

    argsQuery = {
        'codigo': None,
        'descricao': None,
        'saldo': None,
        'numLinhas': 100,
    }
    materials = SQLparaList(fetch_data(argsQuery))

    if materials:
        # Filtros
        ## Filtro por codigo (numerico)
        if codigo:
            if codigo and codigo.startswith('30'):
                materials = list(filter(lambda material: material['codigo'].startswith(codigo), materials))
            else:
                messages.error(request, "O código de materiais deve começar com '30'.")
        ## Filtro por descrição (string)
        if descricao:
            materials = list(filter(lambda material: descricao.lower() in material['descricao'].lower(), materials))
        ## Filtro por saldo (qtd)
        if saldo_filter and saldo:
            match saldo_filter:
                case 'menorq': # <
                    materials = list(filter(lambda material: material['saldo'] < saldo, materials))
                case 'igual': # =
                    materials = list(filter(lambda material: material['saldo'] == saldo, materials))
                case 'maiorq': # >
                    materials = list(filter(lambda material: material['saldo'] > saldo, materials))
                case 'entre':
                    materials = list(filter(lambda material: saldo <= material['saldo'] <= saldoMax, materials))

        # Ordenação
        if campoOrdenacao and ordemOrdenacao:
            ordemList = False
            if ordemOrdenacao == 'd':
                ordemList = True
            materials.sort(key=lambda material: material[campoOrdenacao], reverse = ordemList)

    else:
        return messages.error(request, "Erro ao carregar o banco de dados")
    
    # Paginação
    paginator = Paginator(materials, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'material_pesquisa.html', {'page_obj': page_obj})
### lista com filtro FIM
