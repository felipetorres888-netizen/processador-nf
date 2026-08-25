from src.extraction.chave_acesso import chave_acesso_valida, extrair_chave_acesso


def _chave_valida_de_teste() -> str:
    """Monta uma chave de 44 dígitos com o DV (dígito verificador) real,
    calculado pelo mesmo algoritmo mod-11 que o módulo implementa — usar
    uma chave sintética aqui (não uma chave real de NF-e) é o correto,
    já que o objetivo é testar a matemática do DV, não uma nota real."""
    corpo = "3526" + "0" * 39  # 43 dígitos quaisquer
    pesos = [2, 3, 4, 5, 6, 7, 8, 9] * 6
    pesos = pesos[:43][::-1]
    soma = sum(int(d) * p for d, p in zip(corpo, pesos))
    resto = soma % 11
    dv = 0 if resto < 2 else 11 - resto
    return corpo + str(dv)


def test_chave_acesso_valida_aceita_chave_com_dv_correto():
    assert chave_acesso_valida(_chave_valida_de_teste()) is True


def test_chave_acesso_valida_rejeita_dv_errado():
    chave = _chave_valida_de_teste()
    dv_errado = "0" if chave[-1] != "0" else "1"
    assert chave_acesso_valida(chave[:-1] + dv_errado) is False


def test_chave_acesso_valida_rejeita_tamanho_errado():
    assert chave_acesso_valida("123") is False


def test_extrair_chave_acesso_encontra_em_grupos_de_4_separados_por_espaco():
    chave = _chave_valida_de_teste()
    grupos = " ".join(chave[i : i + 4] for i in range(0, 44, 4))
    texto = f"Chave de acesso\n{grupos}\nConsulte pela chave de acesso"

    resultado = extrair_chave_acesso(texto)

    assert resultado == chave


def test_extrair_chave_acesso_encontra_string_continua_de_44_digitos():
    chave = _chave_valida_de_teste()
    texto = f"Numero da chave: {chave}"

    resultado = extrair_chave_acesso(texto)

    assert resultado == chave


def test_extrair_chave_acesso_retorna_none_quando_nao_ha_chave():
    texto = "Nota fiscal sem chave de acesso nenhuma"

    resultado = extrair_chave_acesso(texto)

    assert resultado is None
