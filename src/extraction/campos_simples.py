# src/extraction/campos_simples.py
"""Extração de campos sem dígito verificador (Fase 3a): número, série,
data de emissão, valor total. Regex puro, sem normalização de formato
(a unidade/formato original é preservada, igual à regra de unidades do
spec §12 — aqui aplicada ao mesmo princípio para data/valor)."""

from __future__ import annotations

import re

_PADRAO_NUMERO = re.compile(r"N[uú]mero\D{0,5}(\d+)", re.IGNORECASE)
_PADRAO_SERIE = re.compile(r"S[eé]rie\D{0,5}(\d+)", re.IGNORECASE)
_PADRAO_DATA = re.compile(
    r"Data de Emiss[aã]o\D{0,10}(\d{2}/\d{2}/\d{4})", re.IGNORECASE
)
_PADRAO_VALOR = re.compile(
    r"(?:Valor Total|TOTAL)\D{0,15}R\$\s*([\d.]+,\d{2})", re.IGNORECASE
)


def extrair_numero_serie(texto: str) -> tuple[str | None, str | None]:
    numero_match = _PADRAO_NUMERO.search(texto)
    serie_match = _PADRAO_SERIE.search(texto)
    numero = numero_match.group(1) if numero_match else None
    serie = serie_match.group(1) if serie_match else None
    return numero, serie


def extrair_data_emissao(texto: str) -> str | None:
    match = _PADRAO_DATA.search(texto)
    return match.group(1) if match else None


def extrair_valor_total(texto: str) -> float | None:
    match = _PADRAO_VALOR.search(texto)
    if not match:
        return None
    valor_str = match.group(1).replace(".", "").replace(",", ".")
    return float(valor_str)
