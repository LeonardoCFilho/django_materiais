from django.shortcuts import render, redirect

### index 
def index(request):
    return render(request, 'index_consultaOracle.html')
### index FIM

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
        codigoMaterial = random.randint(1, 100)  # material aleatroio
        dataAleatoria = timezone.now() - timedelta(days=random.randint(1, 30))
        ConsumoMaterial.objects.create(
            materialUsado = Material.objects.get(id=codigoMaterial),
            dataConsumo = dataAleatoria,
        )
        print(f"consumo de : {Material.objects.get(id=codigoMaterial)}") 

#criar_material(100)
#criar_consumo_material(100)
### inserindo objetos na database FIM

### temp lista tudo
def material_list(request):
    from django.shortcuts import render
    from django.core.paginator import Paginator
    from .models import Material

    # Get all materials from the database
    materials = Material.objects.all()

    # Create a Paginator object to paginate the results
    paginator = Paginator(materials, 20)  # Show 20 materials per page

    # Get the page number from the URL parameters (default to 1 if not provided)
    page_number = request.GET.get('page', 1)
    
    # Get the materials for the current page
    page_obj = paginator.get_page(page_number)

    # Pass the materials to the template
    return render(request, 'material_list.html', {'page_obj': page_obj})
### temp lista tudo FIM

### lista com filtro 
def material_pesquisa(request):
    from django.shortcuts import render
    from django.core.paginator import Paginator
    from .models import Material

    # Extract filter parameters
    codigo = request.GET.get('codigo')
    descricao = request.GET.get('descricao')
    saldo_filter = request.GET.get('saldo_filter')
    saldo = request.GET.get('saldo')

    # Start with all materials
    materials = Material.objects.all()

    # Filter by codigo (if provided)
    if codigo:
        materials = materials.filter(codigo__startswith=codigo)

    # Filter by descricao (if provided)
    if descricao:
        materials = materials.filter(descricao__icontains=descricao)

    # Filter by saldo (if provided)
    if saldo_filter and saldo:
        if saldo_filter == 'lt':  # Less Than
            materials = materials.filter(saldo__lt=saldo)
        elif saldo_filter == 'eq':  # Equals
            materials = materials.filter(saldo=saldo)
        elif saldo_filter == 'gt':  # More Than
            materials = materials.filter(saldo__gt=saldo)

    # Pagination
    paginator = Paginator(materials, 20)  # Show 20 materials per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'material_pesquisa.html', {'page_obj': page_obj})
### lista com filtro FIM