from django.shortcuts import render, redirect

### index 
def index(request):
    request.session.pop('flagUltimoUso', None)
    return render(request, 'index_consultaOracle.html')
### index FIM

### Calcular periodo entre duas datas
# Ideia: Retorna a qtd de dias entre duas datas, ref para data nova é o dia atual
from django.utils import timezone
def calculaPeriodo(dataAntiga, dataNova = timezone.now(), escala = 'm', precisao = 0):
    from datetime import timedelta
    import math
    # Evitar erros
    if not dataAntiga:
        return None  
    # Lidar com timezone
    if dataAntiga and dataAntiga.tzinfo is None:
        dataAntiga = timezone.make_aware(dataAntiga)
    if dataNova.tzinfo is None:
        dataNova = timezone.make_aware(dataNova)
    # Calcular periodo
    delta = dataNova - dataAntiga
    match escala:
        case 'd':
            return delta.days
        case 'm':
            return round((delta.days/30),precisao)
        case 'a':
            return round((delta.days/365),precisao)
### Calcular periodo entre duas datas FIM

### lista com filtro 
def material_pesquisa(request):
    from django.shortcuts import render
    from django.core.paginator import Paginator
    from .models import Material, ConsumoMaterial
    from django.db.models import OuterRef, Subquery, F
    from django.utils import timezone
    from django.db.models import ExpressionWrapper, fields

    # Fazer a logica de login => Não está loggado -> redirect para outra página
    # <login>

    # Fazer a logica de permissões
    # <permissões>
    
    # temp
    if not request.session.get('flagUltimoUso', None):
        request.session['flagUltimoUso'] = request.GET.get('flagUltimoUso', 'false').lower() == 'true' 

    # Leitura do html
    codigo = request.GET.get('codigo')
    descricao = request.GET.get('descricao')
    saldo_filter = request.GET.get('saldo_filter')
    saldo = request.GET.get('saldo')
    saldoMax = request.GET.get('saldo_between_end')
    ultimoUso_filter = request.GET.get('ultimoUso_filter')
    ultimoUso = request.GET.get('ultimoUso')
    ultimoUsoMax = request.GET.get('ultimoUso_between_end')
    # Ordenação padrão vai ser por código (crescente)
    ordemOrdenacao = request.GET.get('ordemOrdenacao', 'c')
    campoOrdenacao = request.GET.get('campoOrdenacao', 'codigo')

    materials = Material.objects.all()

    # Filtros
    ## Filtro por codigo (numerico)
    if codigo:
        materials = materials.filter(codigo__startswith=codigo)
    ## Filtro por descrição (string)
    if descricao:
        materials = materials.filter(descricao__icontains=descricao)
    ## Filtro por saldo (qtd)
    if saldo_filter and saldo:
        match saldo_filter:
            case 'menorq': # <
                materials = materials.filter(saldo__lt=saldo)
            case 'igual': # =
                materials = materials.filter(saldo=saldo)
            case 'maiorq': # >
                materials = materials.filter(saldo__gt=saldo)
            case 'entre':
                materials = materials.filter(saldo__gte=saldo, saldo__lte=saldoMax)

    # Ultima requisição/uso
    if request.session.get('flagUltimoUso', False):
        # criar query para o subquery
        ultimoConsumo = ConsumoMaterial.objects.filter(materialUsado=OuterRef('pk')).order_by('-dataConsumo').values('dataConsumo')[:1]
        # Concatenar
        materials = materials.annotate(ultimoUso_data=Subquery(ultimoConsumo)).annotate(
            ultimoUso_meses=ExpressionWrapper(timezone.now() - F('ultimoUso_data'),output_field=fields.DurationField())
        )
        # Converter de dia para mes
        materials = materials.annotate( 
            ultimoUso_meses=ExpressionWrapper(F('ultimoUso_meses') / timezone.timedelta(days=30), output_field=fields.IntegerField())
        )
        materials = materials.annotate( # arrendondar
            ultimoUso_meses_int=ExpressionWrapper(F('ultimoUso_meses'), output_field=fields.IntegerField())
        )
        ## Filtro por último uso (meses)
        if ultimoUso_filter and ultimoUso:
            match ultimoUso_filter:
                case 'menorq':  # <
                    materials = materials.filter(ultimoUso_meses__lt=int(ultimoUso))
                case 'igual':  # =
                    materials = materials.filter(ultimoUso_meses=int(ultimoUso))
                case 'maiorq':  # >
                    materials = materials.filter(ultimoUso_meses__gt=int(ultimoUso))
                case 'entre':  # entre...
                    if ultimoUsoMax:
                        materials = materials.filter(ultimoUso_meses__gte=int(ultimoUso), ultimoUso_meses__lte=int(ultimoUsoMax))

    # Ordenação
    if campoOrdenacao and ordemOrdenacao:
        if ordemOrdenacao == 'd':
            campoOrdenacao = '-'+campoOrdenacao
        materials = materials.order_by(campoOrdenacao)

    # Paginação
    paginator = Paginator(materials, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'material_pesquisa.html', {'page_obj': page_obj, 'flagUltimoUso': request.session.get('flagUltimoUso', False)})
### lista com filtro FIM

### inserindo objetos na database
# Teoricamente materias podem codigos iguais, so é incrivelmente improvável
def criar_material(n=10):
    from .models import Material
    import random
    
    sujeitos = ["O cachorro", "A garota", "O professor", "A mãe", "O carro", "O cientista", "O político", "A estrela"]
    verbos = ["corre", "estuda", "fala", "viaja", "compreende", "brinca", "diz", "ajuda"]
    objetos = ["na rua", "com os amigos", "no trabalho", "na escola", "para casa", "no parque", "para o futuro", "ao mundo"]
    for _ in range(n):
        codigo = random.randint(1000000000, 9999999999) 
        descricao = random.choice(sujeitos) +' '+ random.choice(verbos) +' '+ random.choice(objetos)
        saldo = random.randint(1, 100)  
        Material.objects.create(
            codigo=codigo,
            descricao=descricao,
            saldo=saldo
        )
        print(f"material: {codigo} - {descricao[:50]}..") 


def criar_consumo_material(n=10):
    from .models import ConsumoMaterial
    from .models import Material
    import random
    from datetime import timedelta
    from django.utils import timezone
    for _ in range(n):
        codigoMaterial = random.randint(1, len(Material.objects.all()))  # material aleatroio
        dataAleatoria = timezone.now() - timedelta(days=random.randint(1, 900))
        ConsumoMaterial.objects.create(
            materialUsado = Material.objects.get(id=codigoMaterial),
            dataConsumo = dataAleatoria,
        )
        print(f"consumo de : {Material.objects.get(id=codigoMaterial)}") 

#criar_material(100)
#criar_consumo_material(100)
### inserindo objetos na database FIM