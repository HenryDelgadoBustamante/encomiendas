from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Encomienda, Empleado
from .forms import EncomiendaForm, CambioEstadoForm
from config.choices import EstadoEnvio

from django.db.models import Q

@login_required
def encomienda_list(request):
    encomiendas = Encomienda.objects.select_related('remitente', 'destinatario', 'ruta').all()
    
    # Filtros
    estado = request.GET.get('estado')
    q = request.GET.get('q')
    
    if estado:
        encomiendas = encomiendas.filter(estado=estado)
    if q:
        encomiendas = encomiendas.filter(
            Q(codigo__icontains=q) |
            Q(remitente__nombres__icontains=q) |
            Q(remitente__apellidos__icontains=q) |
            Q(remitente__nro_doc__icontains=q) |
            Q(destinatario__nombres__icontains=q) |
            Q(destinatario__apellidos__icontains=q) |
            Q(destinatario__nro_doc__icontains=q)
        )
        
    # Paginación
    paginator = Paginator(encomiendas, 10)  # 10 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estados': EstadoEnvio.choices,
    }
    return render(request, 'envios/lista.html', context)

@login_required
def encomienda_create(request):
    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            encomienda = form.save(commit=False)
            
            # Obtener empleado logueado o el primero como fallback (para demostración)
            empleado = Empleado.objects.filter(email=request.user.email).first()
            if not empleado:
                empleado = Empleado.objects.first()
            
            encomienda.empleado_registro = empleado
            
            # Generar código, calcular costo y fecha estimada
            encomienda = Encomienda.crear_con_costo_calculado(
                descripcion=encomienda.descripcion,
                peso_kg=encomienda.peso_kg,
                volumen_cm3=encomienda.volumen_cm3,
                remitente=encomienda.remitente,
                destinatario=encomienda.destinatario,
                ruta=encomienda.ruta,
                observaciones=encomienda.observaciones,
                empleado_registro=empleado
            )
            
            messages.success(request, 'Encomienda creada exitosamente.')
            return redirect('envios:detalle', pk=encomienda.pk)
    else:
        form = EncomiendaForm()
        
    return render(request, 'envios/form.html', {'form': form, 'titulo': 'Crear Encomienda'})

@login_required
def encomienda_update(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    
    if request.method == 'POST':
        form = EncomiendaForm(request.POST, instance=encomienda)
        if form.is_valid():
            encomienda = form.save(commit=False)
            encomienda.calcular_costo()  # Recalcular si cambia el peso o ruta
            encomienda.save()
            messages.success(request, 'Encomienda actualizada exitosamente.')
            return redirect('envios:lista')
    else:
        form = EncomiendaForm(instance=encomienda)
        
    return render(request, 'envios/form.html', {'form': form, 'titulo': 'Editar Encomienda', 'encomienda': encomienda})

@login_required
def encomienda_delete(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    
    # Verificar si el estado permite la eliminación
    if encomienda.estado != EstadoEnvio.PENDIENTE:
        messages.error(request, 'No se puede eliminar una encomienda que no esté en estado Pendiente.')
        return redirect('envios:detalle', pk=encomienda.pk)
    
    if request.method == 'POST':
        encomienda.delete()
        messages.success(request, 'Encomienda eliminada exitosamente.')
        return redirect('envios:lista')
        
    return render(request, 'envios/eliminar.html', {'encomienda': encomienda})

@login_required
def dashboard_view(request):
    total = Encomienda.objects.count()
    pendientes = Encomienda.objects.filter(estado=EstadoEnvio.PENDIENTE).count()
    en_transito = Encomienda.objects.filter(estado=EstadoEnvio.EN_TRANSITO).count()
    entregados = Encomienda.objects.filter(estado=EstadoEnvio.ENTREGADO).count()
    
    ultimas = Encomienda.objects.all()[:5]
    
    context = {
        'total': total,
        'pendientes': pendientes,
        'en_transito': en_transito,
        'entregados': entregados,
        'ultimas': ultimas,
    }
    return render(request, 'envios/dashboard.html', context)

@login_required
def encomienda_detail(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    historial = encomienda.historial_estados.all().order_by('-fecha_cambio')
    
    context = {
        'encomienda': encomienda,
        'historial': historial,
    }
    return render(request, 'envios/detalle.html', context)

@login_required
def encomienda_cambiar_estado(request, pk):
    encomienda = get_object_or_404(Encomienda, pk=pk)
    
    if request.method == 'POST':
        form = CambioEstadoForm(request.POST)
        if form.is_valid():
            nuevo_estado = form.cleaned_data['estado']
            observacion = form.cleaned_data['observacion']
            
            # Obtener empleado logueado
            empleado = Empleado.objects.filter(email=request.user.email).first()
            if not empleado:
                empleado = Empleado.objects.first()
                
            encomienda.cambiar_estado(nuevo_estado, empleado, observacion)
            
            messages.success(request, 'Estado actualizado exitosamente.')
            return redirect('envios:detalle', pk=encomienda.pk)
    else:
        form = CambioEstadoForm(initial={'estado': encomienda.estado})
        
    context = {
        'form': form,
        'encomienda': encomienda,
        'titulo': f'Cambiar Estado - {encomienda.codigo}'
    }
    return render(request, 'envios/cambiar_estado.html', context)

