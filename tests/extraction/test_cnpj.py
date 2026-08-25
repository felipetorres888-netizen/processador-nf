from src.extraction.cnpj import cnpj_valido, extrair_cnpj


def test_cnpj_valido_aceita_cnpj_real_correto():
    # CNPJ real do projeto (Prime 4S Bar & Restaurante LTDA), recuperado via
    # OCR na validação da Fase 2 — usado aqui como caso de referência real.
    assert cnpj_valido("62833832000146") is True


def test_cnpj_valido_rejeita_digito_verificador_errado():
    # Mesmo CNPJ acima, mas com o último dígito verificador alterado.
    assert cnpj_valido("62833832000145") is False


def test_cnpj_valido_rejeita_string_de_tamanho_errado():
    assert cnpj_valido("123") is False
    assert cnpj_valido("") is False


def test_extrair_cnpj_encontra_formatado_com_pontuacao():
    texto = "Emitente\nCNPJ: 62.833.832/0001-46\nOutros dados"

    resultado = extrair_cnpj(texto)

    assert resultado == "62833832000146"


def test_extrair_cnpj_encontra_sem_pontuacao():
    texto = "CNPJ 62833832000146 conferido"

    resultado = extrair_cnpj(texto)

    assert resultado == "62833832000146"


def test_extrair_cnpj_retorna_none_quando_nao_ha_cnpj():
    texto = "Nota fiscal sem nenhum numero de documento aqui"

    resultado = extrair_cnpj(texto)

    assert resultado is None


def test_extrair_cnpj_ignora_sequencia_de_14_digitos_sem_formatacao_de_cnpj_por_perto():
    # 14 digitos soltos, sem rotulo "CNPJ" nem formatacao tipica proxima --
    # nao deve ser confundido com telefone/codigo de barras truncado.
    texto = "Codigo de rastreio: 11111111111111"

    resultado = extrair_cnpj(texto)

    assert resultado is None
