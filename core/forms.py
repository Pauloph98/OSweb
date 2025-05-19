import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Empresa, Cliente, Equipamento, OrdemServico

class EmpresaRegistrationForm(UserCreationForm):
    nome_fantasia = forms.CharField(max_length=100)
    razao_social = forms.CharField(max_length=100)
    cnpj = forms.CharField(max_length=18)
    nome_representante = forms.CharField(max_length=100)
    telefone = forms.CharField(max_length=15, required=True)
    endereco = forms.CharField(max_length=200, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 
                 'nome_fantasia', 'razao_social', 'cnpj', 'nome_representante',
                 'telefone', 'endereco']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_empresa = True
        
        if commit:
            user.save()
            empresa = Empresa.objects.create(
                usuario=user,
                nome_fantasia=self.cleaned_data['nome_fantasia'],
                razao_social=self.cleaned_data['razao_social'],
                cnpj=self.cleaned_data['cnpj'],
                nome_representante=self.cleaned_data['nome_representante']
            )
            # Atualiza os campos adicionais no usuário
            user.telefone = self.cleaned_data['telefone']
            user.endereco = self.cleaned_data['endereco']
            user.save()
        
        return user
class EmpresaUpdateForm(forms.ModelForm):
    telefone = forms.CharField(max_length=15, required=False)
    endereco = forms.CharField(max_length=200, required=False)
    
    class Meta:
        model = Empresa
        fields = ['nome_fantasia', 'razao_social', 'cnpj', 'nome_representante', 'observacao_retirada']
        widgets = {
            'cnpj': forms.TextInput(attrs={'data-mask': '00.000.000/0000-00'}),
            'telefone': forms.TextInput(attrs={'data-mask': '(00) 0000-0000'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Preenche os campos do usuário
        if self.instance and hasattr(self.instance, 'usuario'):
            self.fields['telefone'].initial = self.instance.usuario.telefone
            self.fields['endereco'].initial = self.instance.usuario.endereco
        
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        empresa = super().save(commit=False)
        if commit:
            empresa.save()
            # Atualiza os dados do usuário associado
            if hasattr(empresa, 'usuario'):
                empresa.usuario.telefone = self.cleaned_data['telefone']
                empresa.usuario.endereco = self.cleaned_data['endereco']
                empresa.usuario.save()
        return empresa

class TecnicoRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_tecnico = True
        user.empresa = self.empresa
        if commit:
            user.save()
        return user

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'sobrenome', 'endereco', 'telefone', 'celular']
        widgets = {
            'telefone': forms.TextInput(attrs={'data-mask': '(00) 0000-0000'}),
            'celular': forms.TextInput(attrs={'data-mask': '(00) 00000-0000'}),
        }
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        


class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = ['tipo', 'marca', 'modelo', 'numero_serie']
        widgets = {
            'tipo': forms.TextInput(attrs={'placeholder': 'Ex: Notebook, Impressora'}),
            'numero_serie': forms.TextInput(attrs={'placeholder': 'Número único do equipamento'})
        }

from django import forms
from .models import OrdemServico, Equipamento, Cliente

class OrdemServicoForm(forms.ModelForm):
    # Campos para novo equipamento (obrigatórios)
    tipo_equipamento = forms.CharField(
        required=True,
        label="Tipo do Equipamento",
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Notebook, Impressora'})
    )
    marca_equipamento = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Marca do equipamento'})
    )
    modelo_equipamento = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Modelo do equipamento'})
    )
    numero_serie_equipamento = forms.CharField(
        required=True,
        label="Número de Série",
        widget=forms.TextInput(attrs={'placeholder': 'Número único do equipamento'})
    )

    class Meta:
        model = OrdemServico
        fields = ['cliente', 'data_entrada', 'acessorios', 'observacoes']
        widgets = {
            'data_entrada': forms.DateInput(attrs={'type': 'date'}),
            'acessorios': forms.Textarea(attrs={'rows': 3}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

        if empresa:
            self.fields['cliente'].queryset = Cliente.objects.filter(empresa=empresa)

    def save(self, commit=True):
        ordem_servico = super().save(commit=False)
        cliente = self.cleaned_data['cliente']

        # Sempre criar novo equipamento
        tipo = self.cleaned_data['tipo_equipamento']
        marca = self.cleaned_data['marca_equipamento']
        modelo = self.cleaned_data['modelo_equipamento']
        numero_serie = self.cleaned_data['numero_serie_equipamento']

        # Cria e associa equipamento
        equipamento = Equipamento.objects.create(
            cliente=cliente,
            tipo=tipo,
            marca=marca,
            modelo=modelo,
            numero_serie=numero_serie
        )
        ordem_servico.equipamento = equipamento

        if commit:
            ordem_servico.save()

        return ordem_servico



class OrdemServicoUpdateForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ('descricao_servico', 'valor_servico', 'status')

class ObservacaoRetiradaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ('observacao_retirada',)

class TecnicoOrdemServicoUpdateForm(forms.ModelForm):
    observacao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Registre observações sobre a alteração'}),
        label="Observação da Alteração"
    )
    
    class Meta:
        model = OrdemServico
        fields = ['status', 'descricao_servico']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'descricao_servico': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.user:
            # Limita as opções de status para técnicos
            if self.user.is_tecnico:
                status_permitidos = self.instance.status_permitidos_para_tecnico()
                self.fields['status'].choices = [
                    (status, dict(OrdemServico.STATUS_CHOICES)[status])
                    for status in status_permitidos
                ]