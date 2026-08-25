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


def test_extrair_data_emissao_layout_danfe_rotulo_e_valor_em_linhas_diferentes():
    # Reproduz a estrutura real observada em resultado/texto_ocr/CAPUEIRA*.txt:
    # linha de rotulo, linha em branco, linha de valores (nome, CNPJ, data).
    texto = (
        "NOMERAZAO SOCIAL CNPYCPF DATA DA EMISSAO\n"
        "\n"
        "FORNECEDOR TESTE LTDA 12.345.678/0001-90  |19/08/2026\n"
    )

    resultado = extrair_data_emissao(texto)

    assert resultado == "19/08/2026"


def test_extrair_data_emissao_rotulo_colado_sem_espaco_como_ocr_as_vezes_produz():
    # Reproduz resultado/texto_ocr/TRILIX*.txt: "DATADA EMISSAO" (OCR perdeu o
    # espaco entre "DATA" e "DA"), valor na linha seguinte.
    texto = "DATADA EMISSAO o\n12.345.678/0001-90 - 19/08/2026 T\n"

    resultado = extrair_data_emissao(texto)

    assert resultado == "19/08/2026"


def test_extrair_data_emissao_nao_confunde_com_data_de_saida_ou_impressao():
    texto = (
        "DATA DE SAIDA\n19/07/2026\n"
        "DATA E HORA DA IMPRESSAO: 20/07/2026 17:27:15\n"
        "DATA DA EMISSAO\n21/07/2026\n"
    )

    resultado = extrair_data_emissao(texto)

    assert resultado == "21/07/2026"


def test_extrair_valor_total_layout_danfe_pega_o_ultimo_valor_da_linha_seguinte():
    # Reproduz resultado/texto_ocr/TRILIX*.txt: linha de varios rotulos de
    # valor terminando em "VALOR TOTAL DA NOTA", linha seguinte com os
    # valores correspondentes na MESMA ordem -- o total e o ULTIMO numero,
    # nao o primeiro.
    texto = (
        "VALOR DO FRETE VALOR DO SEGURO DESCONTO OUTRAS DESPESAS VALOR DO IPI VALOR TOTAL DA NOTA\n"
        "10,95 0,00 0,00 0,00 0,00 284,95\n"
    )

    resultado = extrair_valor_total(texto)

    assert resultado == 284.95


def test_extrair_valor_total_no_layout_danfe_nao_pega_o_primeiro_valor_da_linha():
    # Mesmo caso acima, mas comprova explicitamente que NAO esta pegando o
    # primeiro numero da linha (10,95, que e o valor do frete, nao o total).
    texto = (
        "VALOR DO FRETE VALOR TOTAL DA NOTA\n"
        "10,95 284,95\n"
    )

    resultado = extrair_valor_total(texto)

    assert resultado == 284.95
    assert resultado != 10.95


def test_extrair_valor_total_prefere_padrao_direto_quando_disponivel():
    # Layout simples (nao-DANFE, ex. um recibo) continua funcionando como
    # antes: rotulo com "R$" colado, sem precisar do fallback de tabela.
    texto = "Valor Total da Nota: R$ 797,50\n"

    resultado = extrair_valor_total(texto)

    assert resultado == 797.50


def test_extrair_valor_total_layout_danfe_retorna_none_sem_linha_seguinte_numerica():
    texto = "VALOR TOTAL DA NOTA\ntexto sem numero nenhum aqui\n"

    resultado = extrair_valor_total(texto)

    assert resultado is None
