from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import (

    RecibosListView, visualizar_recibo, ClienteListView, ClienteCreateView, ClienteUpdateView, 
    EquipamentoCreateView, OrdemServicoListView,
    OrdemServicoCreateView, OrdemServicoUpdateView,TecnicoListView, OrdemServicoDetailView,
)

urlpatterns = [
        # URLs de autenticação
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Empresa URLs
    path('tecnicos/', TecnicoListView.as_view(), name='listar_tecnicos'),
    path('empresa/editar/', views.editar_empresa, name='editar_empresa'),
    path('empresa/cadastro/', views.empresa_registration, name='empresa_registration'),
    path('empresa/dashboard/', views.empresa_dashboard, name='empresa_dashboard'),
    path('empresa/tecnico/cadastro/', views.cadastrar_tecnico, name='cadastrar_tecnico'),
    path('empresa/observacao/', views.atualizar_observacao, name='atualizar_observacao'),
    path('tecnicos/editar/<int:pk>/', views.editar_tecnico, name='editar_tecnico'),
    path('recibos/', RecibosListView.as_view(), name='recibos_list'),
    path('recibo/<int:pk>/', visualizar_recibo, name='visualizar_recibo'),
    
    # Cliente URLs
    path('cliente/', ClienteListView.as_view(), name='cliente_list'),
    path('cliente/cadastro/', ClienteCreateView.as_view(), name='cliente_create'),
    path('cliente/<int:pk>/editar/', ClienteUpdateView.as_view(), name='cliente_update'),
    
    # Equipamento URLs
    path('cliente/<int:cliente_id>/equipamento/cadastro/', EquipamentoCreateView.as_view(), name='equipamento_create'),
    path('get_equipamentos/<int:cliente_id>/', views.get_equipamentos, name='get_equipamentos'),
    
    # Ordem de Serviço URLs
    path('ordem-servico/', OrdemServicoListView.as_view(), name='ordem_servico_list'),
    path('ordem-servico/cadastro/', views.OrdemServicoCreateView.as_view(), name='ordem_servico_create'),
    path('get_equipamentos/<int:cliente_id>/', views.get_equipamentos, name='get_equipamentos'),
    path('ordem-servico/<int:pk>/editar/', OrdemServicoUpdateView.as_view(), name='ordem_servico_update'),

    path('ordem-servico/<int:pk>/', OrdemServicoDetailView.as_view(), name='ordem_servico_detail'),
    path('ordem-servico/<int:pk>/imprimir/', views.ordem_servico_imprimir, name='ordem_servico_imprimir'),
    path('ordem-servico/<int:pk>/imprimir/', views.ordem_servico_imprimir, name='ordem_servico_imprimir'),
    path('ordem-servico/<int:pk>/', views.OrdemServicoDetailView.as_view(), name='ordem_servico_detalhe'),
]