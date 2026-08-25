# tests/extraction/test_campos_simples.py
from src.extraction.campos_simples import (
    extrair_data_emissao,
    extrair_numero_serie,
    extrair_valor_total,
)


def test_extrair_numero_serie_encontra_ambos():
    texto = "NOTA FISCAL\nNumero: 004021  Serie: 1\nOutros dados"

    numero, serie = extrair_numero_serie(texto)

    assert numero == "004021"
    assert serie == "1"


def test_extrair_numero_serie_retorna_none_quando_ausente():
    texto = "Documento sem numero nem serie indicados"

    numero, serie = extrair_numero_serie(texto)

    assert numero is None
    assert serie is None


def test_extrair_data_emissao_formato_barra():
    texto = "Data de Emissao: 28/08/2026\nHora de saida: 14:00"

    resultado = extrair_data_emissao(texto)

    assert resultado == "28/08/2026"


def test_extrair_data_emissao_retorna_none_quando_ausente():
    assert extrair_data_emissao("sem data nenhuma aqui") is None


def test_extrair_valor_total_formato_brasileiro():
    texto = "Valor Total da Nota: R$ 797,50"

    resultado = extrair_valor_total(texto)

    assert resultado == 797.50


def test_extrair_valor_total_com_milhar():
    texto = "TOTAL: R$ 1.234,56"

    resultado = extrair_valor_total(texto)

    assert resultado == 1234.56


def test_extrair_valor_total_retorna_none_quando_ausente():
    assert extrair_valor_total("nota sem valor nenhum") is None
