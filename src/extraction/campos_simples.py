# src/extraction/campos_simples.py
"""Extração de campos sem dígito verificador (Fase 3a): número, série,
data de emissão, valor total. Regex puro, sem normalização de formato
(a unidade/formato original é preservada, igual à regra de unidades do
spec §12 — aqui aplicada ao mesmo princípio para data/valor).

data_emissao e valor_total lidam com dois layouts observados nas 6 NFs
reais usadas para validar a Fase 3a:
1. Rótulo e valor na mesma linha, próximos (recibos simples, algumas NFs).
2. Layout DANFE: uma linha de rótulos (às vezes vários lado a lado),
   seguida por uma linha de valores na MESMA ordem posicional. Nesse caso
   o rótulo relevante costuma ser o ÚLTIMO da linha, e o valor
   correspondente é o ÚLTIMO valor da linha seguinte — não o primeiro.
"""

from __future__ import annotations

import re

_PADRAO_NUMERO = re.compile(r"N[uú]mero\D{0,5}(\d+)", re.IGNORECASE)
_PADRAO_SERIE = re.compile(r"S[eé]rie\D{0,5}(\d+)", re.IGNORECASE)

# Aceita "Data de/da Emissao", "DATA DA EMISSÃO", ou rótulo colado sem
# espaço ("DATADA EMISSAO", como o OCR às vezes produz). O valor pode
# estar na mesma linha ou numa linha seguinte (após uma linha em branco,
# como no layout DANFE) — por isso a janela ampla com DOTALL. Como um
# CNPJ tem só UMA barra ("/"), nunca colide com o padrão de duas barras
# de uma data, então pegar a primeira data-shaped token após o rótulo é
# seguro mesmo quando há um CNPJ no meio do caminho.
_PADRAO_DATA = re.compile(
    r"Data\s*(?:de|da)?\s*Emiss[aã]o.{0,200}?(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE | re.DOTALL,
)

# Padrão direto: rótulo com "R$" próximo, tudo na mesma linha (recibos
# simples, notas não-DANFE).
_PADRAO_VALOR_DIRETO = re.compile(
    r"(?:Valor Total|TOTAL)\D{0,15}R\$\s*([\d.]+,\d{2})", re.IGNORECASE
)

# Fallback para o layout DANFE: localiza a linha com o rótulo "VALOR
# TOTAL DA NOTA" e olha para a(s) linha(s) seguinte(s) em busca de
# valores monetários (formato brasileiro, ex. "1.234,56" ou "284,95").
_PADRAO_ROTULO_VALOR_TOTAL = re.compile(r"VALOR\s*TOTAL\s*DA\s*NOTA", re.IGNORECASE)
_PADRAO_MONETARIO = re.compile(r"\d{1,3}(?:\.\d{3})*,\d{2}")


def extrair_numero_serie(texto: str) -> tuple[str | None, str | None]:
    numero_match = _PADRAO_NUMERO.search(texto)
    serie_match = _PADRAO_SERIE.search(texto)
    numero = numero_match.group(1) if numero_match else None
    serie = serie_match.group(1) if serie_match else None
    return numero, serie


def extrair_data_emissao(texto: str) -> str | None:
    match = _PADRAO_DATA.search(texto)
    return match.group(1) if match else None


def _para_float(valor_str: str) -> float:
    return float(valor_str.replace(".", "").replace(",", "."))


def extrair_valor_total(texto: str) -> float | None:
    match_direto = _PADRAO_VALOR_DIRETO.search(texto)
    if match_direto:
        return _para_float(match_direto.group(1))

    linhas = texto.split("\n")
    for indice, linha in enumerate(linhas):
        if _PADRAO_ROTULO_VALOR_TOTAL.search(linha):
            for linha_seguinte in linhas[indice + 1 : indice + 3]:
                valores = _PADRAO_MONETARIO.findall(linha_seguinte)
                if valores:
                    return _para_float(valores[-1])

    return None
