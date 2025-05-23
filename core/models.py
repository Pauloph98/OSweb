import re
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils import timezone

class User(AbstractUser):
    is_empresa = models.BooleanField(default=False)
    is_tecnico = models.BooleanField(default=False)
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, null=True, blank=True)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    endereco = models.CharField(max_length=200, blank=True, null=True)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Sincroniza com a empresa se for o caso
        if hasattr(self, 'empresa_user'):
            self.empresa_user.save()  # Isso vai acionar o save da empresa   

class Empresa(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='empresa_user')
    nome_fantasia = models.CharField(max_length=100)
    razao_social = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=18, unique=True)
    nome_representante = models.CharField(max_length=100)
    observacao_retirada = models.TextField(
        default="Retirada de produto tem que ser feita até 90 dias após feita aprovação do orçamento ou recusa do orçamento"
    )
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Sincroniza telefone e endereço com o usuário
        if not self.usuario.telefone and hasattr(self, 'telefone'):
            self.usuario.telefone = self.telefone
        if not self.usuario.endereco and hasattr(self, 'endereco'):
            self.usuario.endereco = self.endereco
        self.usuario.save()
    
    
    def __str__(self):
        return self.nome_fantasia
    @property
    def cnpj_formatado(self):
        if self.cnpj and len(self.cnpj) == 14:
            return f"{self.cnpj[:2]}.{self.cnpj[2:5]}.{self.cnpj[5:8]}/{self.cnpj[8:12]}-{self.cnpj[12:14]}"
        return self.cnpj
    
    def save(self, *args, **kwargs):
        # Remove formatação do CNPJ antes de salvar
        if self.cnpj:
            self.cnpj = re.sub(r'[^0-9]', '', self.cnpj)
        super().save(*args, **kwargs)
    
    @property
    def telefone(self):
        return self.usuario.telefone
    
    @property
    def email(self):
        return self.usuario.email
    
    @property
    def endereco(self):
        return self.usuario.endereco

class Cliente(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=50)
    sobrenome = models.CharField(max_length=100)
    endereco = models.CharField(max_length=200)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    celular = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)        # opcional
    cpf_cnpj = models.CharField(max_length=18, blank=True, null=True)
    
    def __str__(self):
        return f"{self.nome} {self.sobrenome}"


 
class Equipamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE) 
    tipo = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.nome} - {self.marca} {self.modelo}"

class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ('AGUARDANDO', 'Aguardando orçamento'),
        ('EM_ANDAMENTO', 'Aguardando aprovação'),
        ('APROVADO', 'Orçamento aprovado'),
        ('RECUSADO', 'Orçamento recusado'),
        ('CONCLUIDO', 'Concluído'),
        ('ENTREGUE', 'Equipamento entregue'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE)
    data_entrada = models.DateField(default=timezone.now)
    acessorios = models.TextField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    descricao_servico = models.TextField(blank=True, null=True)
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AGUARDANDO')
    data_aprovacao = models.DateField(blank=True, null=True)
    data_recusa = models.DateField(blank=True, null=True)
    data_entrega = models.DateField(blank=True, null=True)
    ultima_alteracao = models.DateTimeField(auto_now=True)
    recibo_entrega = models.FileField(upload_to='recibos/', blank=True, null=True)
    usuario_alteracao = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordens_alteradas'
    )
    
    def __str__(self):
        return f"OS #{self.id} - {self.cliente} - {self.equipamento}"
    
    def get_absolute_url(self):
        if self.usuario_alteracao and self.usuario_alteracao.is_tecnico:
            return reverse('ordem_servico_edit_tecnico', kwargs={'pk': self.pk})
        return reverse('ordem_servico_edit', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Atualiza datas específicas baseadas no status
        if self.status == 'APROVADO' and not self.data_aprovacao:
            self.data_aprovacao = timezone.now().date()
        elif self.status == 'RECUSADO' and not self.data_recusa:
            self.data_recusa = timezone.now().date()
        elif self.status == 'ENTREGUE' and not self.data_entrega:
            self.data_entrega = timezone.now().date()
        
        # Registra usuário que fez a alteração
        if 'request_user' in kwargs:
            self.usuario_alteracao = kwargs.pop('request_user')
        
        super().save(*args, **kwargs)
    
    def status_permitidos_para_tecnico(self):
        """Retorna os status para os quais um técnico pode mudar"""
        fluxo = {
            'AGUARDANDO': ['EM_ANDAMENTO'],
            'EM_ANDAMENTO': ['CONCLUIDO'],
            'CONCLUIDO': ['ENTREGUE'],
            'APROVADO': ['EM_ANDAMENTO', 'ENTREGUE'],
            'RECUSADO': ['ENTREGUE']
        }
        return fluxo.get(self.status, [])
    
    def pode_mudar_status(self, novo_status, user):
        """Verifica se a mudança de status é permitida"""
        if user.is_empresa:
            return True
        if user.is_tecnico:
            return novo_status in self.status_permitidos_para_tecnico()
        return False
    
    def get_status_info(self):
        """Retorna informações sobre o fluxo de status"""
        return {
            'atual': self.get_status_display(),
            'proximos': [
                (status, dict(self.STATUS_CHOICES)[status]) 
                for status in self.status_permitidos_para_tecnico()
            ] if not (self.usuario_alteracao and self.usuario_alteracao.is_empresa) else [
                (status, label) for status, label in self.STATUS_CHOICES
            ]
        }


from django.utils.translation import gettext_lazy as _

class HistoricoStatus(models.Model):
    ordem = models.ForeignKey(
        OrdemServico, 
        on_delete=models.CASCADE, 
        related_name='historico_status',
        verbose_name=_('Ordem de Serviço')
    )
    status_anterior = models.CharField(
        max_length=20, 
        choices=OrdemServico.STATUS_CHOICES,
        verbose_name=_('Status Anterior')
    )
    status_novo = models.CharField(
        max_length=20, 
        choices=OrdemServico.STATUS_CHOICES,
        verbose_name=_('Novo Status')
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Usuário'),
        related_name='alteracoes_status'
    )
    data_alteracao = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data da Alteração')
    )
    observacao = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_('Observações')
    )
    
    class Meta:
        ordering = ['-data_alteracao']
        verbose_name = _('Histórico de Status')
        verbose_name_plural = _('Históricos de Status')
        indexes = [
            models.Index(fields=['ordem', 'data_alteracao']),
            models.Index(fields=['usuario', 'data_alteracao']),
        ]
    
    def __str__(self):
        return _("{ordem} - {anterior} → {novo}").format(
            ordem=self.ordem,
            anterior=self.get_status_anterior_display(),
            novo=self.get_status_novo_display()
        )
    
    @classmethod
    def registrar_alteracao(cls, ordem, usuario, status_anterior, status_novo, observacao=None):
        """Método helper para registrar alterações de status"""
        return cls.objects.create(
            ordem=ordem,
            status_anterior=status_anterior,
            status_novo=status_novo,
            usuario=usuario,
            observacao=observacao
        )
    
    def tempo_desde_alteracao(self):
        """Retorna o tempo decorrido desde a alteração"""
        from django.utils.timezone import now
        return now() - self.data_alteracao