// Função para formatar CNPJ
function formatCNPJ(cnpj) {
    cnpj = cnpj.replace(/\D/g, '');
    cnpj = cnpj.replace(/^(\d{2})(\d)/, '$1.$2');
    cnpj = cnpj.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
    cnpj = cnpj.replace(/\.(\d{3})(\d)/, '.$1/$2');
    cnpj = cnpj.replace(/(\d{4})(\d)/, '$1-$2');
    return cnpj;
}

// Aplicar máscara de CNPJ
$(document).ready(function() {
    // Máscara para CNPJ
    $('#id_cnpj').on('input', function() {
        this.value = formatCNPJ(this.value);
    });

    // Máscara para telefone
    $('#id_telefone, #id_celular').on('input', function() {
        var phone = this.value.replace(/\D/g, '');
        if (phone.length > 2) {
            phone = phone.replace(/^(\d{2})(\d)/g, '($1) $2');
            if (phone.length > 10) {
                phone = phone.replace(/(\d{4,5})(\d{4})$/, '$1-$2');
            }
        }
        this.value = phone;
    });

    // Inicializar tooltips
    $('[data-toggle="tooltip"]').tooltip();
});