from django.utils import timezone
from django.contrib import messages
from pyexpat.errors import messages
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, path
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import HistoricoStatus, User, Empresa, Cliente, Equipamento, OrdemServico
from .forms import (
    EmpresaRegistrationForm, EmpresaUpdateForm, TecnicoOrdemServicoUpdateForm, TecnicoRegistrationForm, ClienteForm, 
    EquipamentoForm, OrdemServicoForm, OrdemServicoUpdateForm,
    ObservacaoRetiradaForm

)

# Empresa Views
def empresa_registration(request):
    if request.method == 'POST':
        form = EmpresaRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = EmpresaRegistrationForm()
    return render(request, 'empresa/cadastro.html', {'form': form})

@login_required
def empresa_dashboard(request):
    if not request.user.is_empresa:
        return redirect('login')
    
    empresa = request.user.empresa_user
    clientes = Cliente.objects.filter(empresa=empresa).count()
    ordens = OrdemServico.objects.filter(empresa=empresa).count()
    
    context = {
        'empresa': empresa,
        'clientes_count': clientes,
        'ordens_count': ordens,
    }
    return render(request, 'empresa/dashboard.html', context)

@login_required
def editar_empresa(request):
    if not request.user.is_empresa:
        return redirect('login')
    
    empresa = request.user.empresa_user
    
    if request.method == 'POST':
        form = EmpresaUpdateForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dados da empresa atualizados com sucesso!')
            return redirect('empresa_dashboard')
    else:
        form = EmpresaUpdateForm(instance=empresa)
    
    return render(request, 'empresa/editar.html', {'form': form})

@login_required
def cadastrar_tecnico(request):
    if not request.user.is_empresa:
        return redirect('login')
    
    empresa = request.user.empresa_user
    
    if request.method == 'POST':
        form = TecnicoRegistrationForm(request.POST, empresa=empresa)
        if form.is_valid():
            form.save()
            return redirect('empresa_dashboard')
    else:
        form = TecnicoRegistrationForm(empresa=empresa)
    
    return render(request, 'registration/cadastro_tecnico.html', {'form': form})

@login_required
def atualizar_observacao(request):
    if not request.user.is_empresa:
        return redirect('login')
    
    empresa = request.user.empresa_user
    
    if request.method == 'POST':
        form = ObservacaoRetiradaForm(request.POST, instance=empresa)
        if form.is_valid():
            form.save()
            return redirect('empresa_dashboard')
    else:
        form = ObservacaoRetiradaForm(instance=empresa)
    
    return render(request, 'empresa/atualizar_observacao.html', {'form': form})

# Cliente Views
class ClienteListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Cliente
    template_name = 'cliente/lista.html'
    context_object_name = 'clientes'
    
    def test_func(self):
        return self.request.user.is_empresa or self.request.user.is_tecnico
    
    def get_queryset(self):
        if self.request.user.is_empresa:
            return Cliente.objects.filter(empresa=self.request.user.empresa_user)
        elif self.request.user.is_tecnico:
            return Cliente.objects.filter(empresa=self.request.user.empresa)
        return Cliente.objects.none()

class ClienteCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'cliente/cadastro.html'
    success_url = reverse_lazy('cliente_list')
    
    def test_func(self):
        return self.request.user.is_empresa
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa_user
        return super().form_valid(form)
    
class ClienteUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'cliente/editar.html'
    success_url = reverse_lazy('cliente_list')
    
    def test_func(self):
        cliente = self.get_object()
        if self.request.user.is_empresa:
            return cliente.empresa == self.request.user.empresa_user
        return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.request.user.empresa_user
        return kwargs

# Equipamento Views
class EquipamentoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Equipamento
    form_class = EquipamentoForm
    template_name = 'equipamento/cadastro.html'
    
    def test_func(self):
        return self.request.user.is_empresa or self.request.user.is_tecnico
    
    def get_success_url(self):
        return reverse_lazy('cliente_detail', kwargs={'pk': self.kwargs['cliente_id']})
    
    def form_valid(self, form):
        cliente = get_object_or_404(Cliente, pk=self.kwargs['cliente_id'])
        form.instance.cliente = cliente
        return super().form_valid(form)

# Ordem de Serviço Views
class OrdemServicoListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = OrdemServico
    template_name = 'ordem_servico/lista.html'
    context_object_name = 'ordens'
    
    def test_func(self):
        return self.request.user.is_empresa or self.request.user.is_tecnico
    
    def get_queryset(self):
        if self.request.user.is_empresa:
            return OrdemServico.objects.filter(empresa=self.request.user.empresa_user)
        elif self.request.user.is_tecnico:
            return OrdemServico.objects.filter(empresa=self.request.user.empresa)
        return OrdemServico.objects.none()

class OrdemServicoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = OrdemServico
    form_class = OrdemServicoForm
    template_name = 'ordem_servico/cadastro.html'
    
    def get_success_url(self):
        return reverse_lazy('ordem_servico_imprimir', kwargs={'pk': self.object.pk})
    
    def test_func(self):
        return self.request.user.is_empresa
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = self.request.user.empresa_user
        return kwargs
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa_user
        
        # Se marcado para criar novo equipamento
        if form.cleaned_data.get('criar_novo_equipamento'):
            equipamento = Equipamento(
                cliente=form.cleaned_data['cliente'],
                tipo=form.cleaned_data['tipo_equipamento'],
                marca=form.cleaned_data['marca_equipamento'],
                modelo=form.cleaned_data['modelo_equipamento'],
                numero_serie=form.cleaned_data['numero_serie_equipamento']
            )
            equipamento.save()
            form.instance.equipamento = equipamento
        
        return super().form_valid(form)




class OrdemServicoDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = OrdemServico
    template_name = 'ordem_servico/detalhe.html'
    context_object_name = 'ordem'  # Adicione esta linha para nomear o objeto no template
    
    def test_func(self):
        ordem = self.get_object()
        return (self.request.user.is_empresa and ordem.empresa == self.request.user.empresa_user) or \
               (self.request.user.is_tecnico and ordem.empresa == self.request.user.empresa)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pode_imprimir'] = True
        
        # Adicione verificação de debug
        if settings.DEBUG:
            context['debug_ordem'] = self.get_object()  # Para verificar o objeto no template
            
        return context

def ordem_servico_imprimir(request, pk):
    ordem = get_object_or_404(OrdemServico, pk=pk)
    
    if not (request.user.is_empresa and ordem.empresa == request.user.empresa_user):
        return redirect('login')
    
    html_string = render_to_string('ordem_servico/impressao.html', {'ordem': ordem})
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename=ordem_servico_{ordem.id}.pdf'
    return response
def get_equipamentos(request, cliente_id):
    equipamentos = Equipamento.objects.filter(cliente_id=cliente_id)
    options = '<option value="">---------</option>'
    for equipamento in equipamentos:
        options += f'<option value="{equipamento.id}">{equipamento.modelo} - {equipamento.numero_serie}</option>'
    return JsonResponse({'options': options})

class OrdemServicoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = OrdemServico
    template_name = 'ordem_servico/editar.html'
    success_url = reverse_lazy('ordem_servico_list')

    def test_func(self):
        ordem = self.get_object()
        return (
            (self.request.user.is_empresa and ordem.empresa == self.request.user.empresa_user) or
            (self.request.user.is_tecnico and ordem.empresa == self.request.user.empresa)
        )

    def get_template_names(self):
        if self.request.user.is_tecnico:
            return ['ordem_servico/editar_tecnico.html']
        return ['ordem_servico/editar_empresa.html']
    
    def get_form_class(self):
        if self.request.user.is_tecnico:
            return TecnicoOrdemServicoUpdateForm
        return OrdemServicoUpdateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.user.is_tecnico:
            kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        ordem = form.instance
        novo_status = form.cleaned_data.get('status')
        
        if not ordem.pode_mudar_status(novo_status, self.request.user):
            form.add_error('status', 'Transição de status não permitida para seu perfil')
            return self.form_invalid(form)
        
        # Registra no histórico se o status mudou
        if 'status' in form.changed_data:
            HistoricoStatus.objects.create(
                ordem=ordem,
                status_anterior=ordem.status,
                status_novo=novo_status,
                usuario=self.request.user,
                observacao=form.cleaned_data.get('observacao', '')
            )
        
        # Atualiza datas automáticas baseadas no status
        if novo_status == 'APROVADO':
            ordem.data_aprovacao = timezone.now().date()
        elif novo_status == 'RECUSADO':
            ordem.data_recusa = timezone.now().date()
        elif novo_status == 'ENTREGUE':
            ordem.data_entrega = timezone.now().date()
            # Gera o recibo PDF
            return self.gerar_recibo(ordem)
        
        # Atualiza quem modificou
        ordem.usuario_alteracao = self.request.user
        ordem.save()
        
        return super().form_valid(form)

    def gerar_recibo(self, ordem):
        # Renderiza o template do recibo
        html_string = render_to_string('ordem_servico/recibo.html', {
            'ordem': ordem,
            'empresa': ordem.empresa
        })
        
        # Cria o PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        # Salva o recibo no sistema (opcional)
        from django.core.files.base import ContentFile
        from datetime import datetime
        nome_arquivo = f"recibo_entrega_{ordem.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        ordem.recibo_entrega.save(nome_arquivo, ContentFile(pdf), save=True)
        
        # Cria a resposta para download
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={nome_arquivo}'
        return response