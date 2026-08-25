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
    assert resultado.cnpj_emitente.confianca < 1.0


def test_extrair_identificacao_texto_vazio_no_missing_field_crashes():
    resultado = extrair_identificacao("")

    assert resultado.numero.valor is None
    assert resultado.chave_acesso.valor is None
    assert resultado.cnpj_emitente.valor is None
