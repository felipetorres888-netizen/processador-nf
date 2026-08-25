# tests/extraction/test_identificacao.py
from src.extraction.identificacao import IdentificacaoNF, extrair_identificacao


def test_extrair_identificacao_documento_completo_alta_confianca():
    texto = (
        "NOTA FISCAL\n"
        "Numero: 004021  Serie: 1\n"
        "Data de Emissao: 28/08/2026\n"
        "CNPJ: 62.833.832/0001-46\n"
        "Valor Total da Nota: R$ 797,50\n"
    )

    resultado = extrair_identificacao(texto)

    assert isinstance(resultado, IdentificacaoNF)
    assert resultado.numero.valor == "004021"
    assert resultado.numero.confianca > 0.5
    assert resultado.serie.valor == "1"
    assert resultado.data_emissao.valor == "28/08/2026"
    assert resultado.cnpj_emitente.valor == "62833832000146"
    assert resultado.cnpj_emitente.confianca == 1.0  # CNPJ com DV valido
    assert resultado.valor_total.valor == 797.50
    assert resultado.chave_acesso.valor is None
    assert resultado.chave_acesso.confianca == 0.0
    assert resultado.chave_acesso.origem == "nao_encontrado"


def test_extrair_identificacao_cnpj_com_dv_invalido_tem_confianca_baixa():
    texto = "CNPJ: 62.833.832/0001-00\n"  # DV alterado, invalido

    resultado = extrair_identificacao(texto)

    assert resultado.cnpj_emitente.valor == "62833832000100"
    assert resultado.cnpj_emitente.confianca == 0.3


def test_extrair_identificacao_texto_vazio_no_missing_field_crashes():
    resultado = extrair_identificacao("")

    assert resultado.numero.valor is None
    assert resultado.chave_acesso.valor is None
    assert resultado.cnpj_emitente.valor is None


def _chave_valida_com_cnpj_embutido(cnpj: str) -> str:
    """Monta uma chave de 44 digitos sintetica com `cnpj` (14 digitos)
    embutido na posicao [6:20] e o DV real calculado pelo mesmo algoritmo
    mod-11 que src.extraction.chave_acesso implementa -- mesma tecnica do
    helper `_chave_valida_de_teste()` em test_chave_acesso.py."""
    prefixo = "352601"  # 6 digitos quaisquer (UF+AAMM)
    sufixo = "0" * 23  # completa os 43 digitos do corpo
    corpo = prefixo + cnpj + sufixo
    pesos = [2, 3, 4, 5, 6, 7, 8, 9] * 6
    pesos = pesos[:43][::-1]
    soma = sum(int(d) * p for d, p in zip(corpo, pesos))
    resto = soma % 11
    dv = 0 if resto < 2 else 11 - resto
    return corpo + str(dv)


def test_extrair_identificacao_prefere_cnpj_da_chave_de_acesso_quando_disponivel():
    # CNPJ do comprador (o proprio restaurante do usuario) aparecendo no
    # texto livre -- e o CNPJ real do fornecedor (CAPUEIRA) embutido na
    # chave de acesso sintetica, valida, na posicao [6:20].
    cnpj_fornecedor = "37219596000397"
    chave = _chave_valida_com_cnpj_embutido(cnpj_fornecedor)
    grupos = " ".join(chave[i : i + 4] for i in range(0, 44, 4))
    texto = (
        "Destinatario\n"
        "CNPJ: 62.833.832/0001-46\n"
        "Chave de acesso\n"
        f"{grupos}\n"
    )

    resultado = extrair_identificacao(texto)

    assert resultado.cnpj_emitente.valor == cnpj_fornecedor
    assert resultado.cnpj_emitente.valor != "62833832000146"
    assert resultado.cnpj_emitente.confianca == 1.0
    assert resultado.cnpj_emitente.origem == "chave_acesso"


def test_extrair_identificacao_chave_acesso_valida_tem_confianca_alta():
    chave = _chave_valida_com_cnpj_embutido("37219596000397")
    grupos = " ".join(chave[i : i + 4] for i in range(0, 44, 4))
    texto = f"Chave de acesso\n{grupos}\n"

    resultado = extrair_identificacao(texto)

    assert resultado.chave_acesso.valor == chave
    assert resultado.chave_acesso.confianca == 1.0
    assert resultado.chave_acesso.origem == "regex+dv"


def test_extrair_identificacao_chave_e_cnpj_ambos_invalidos_confianca_baixa():
    # Chave sintetica de 44 digitos com DV incorreto (o algoritmo
    # chave_acesso_valida deve rejeitar, entao o override do Finding 1 NAO
    # deve se aplicar) e um CNPJ, separado no texto livre, tambem com DV
    # incorreto.
    chave_valida = _chave_valida_com_cnpj_embutido("37219596000397")
    dv_errado = "0" if chave_valida[-1] != "0" else "1"
    chave_invalida = chave_valida[:-1] + dv_errado
    grupos = " ".join(chave_invalida[i : i + 4] for i in range(0, 44, 4))
    texto = (
        "Chave de acesso\n"
        f"{grupos}\n"
        "CNPJ: 62.833.832/0001-00\n"  # DV alterado, invalido
    )

    resultado = extrair_identificacao(texto)

    assert resultado.chave_acesso.confianca == 0.3
    assert resultado.cnpj_emitente.valor == "62833832000100"
    assert resultado.cnpj_emitente.confianca == 0.3
