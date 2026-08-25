"""Extração e validação de CNPJ (Fase 3a).

Regex puro + o algoritmo padrão de dígito verificador do CNPJ (dois
dígitos, mod 11) — sem IA, sem heurística probabilística.
"""

from __future__ import annotations

import re

_PESOS_DV1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_PESOS_DV2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

# CNPJ formatado (com pontuação) ou 14 dígitos crus, desde que rotulados
# como CNPJ nas proximidades (evita casar qualquer sequência de 14 dígitos
# solta no texto, ex. um código de rastreio).
_PADRAO_FORMATADO = re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}")
_PADRAO_ROTULADO = re.compile(
    r"CNPJ\D{0,10}(\d{14})", re.IGNORECASE
)


def _digito_verificador(digitos: list[int], pesos: list[int]) -> int:
    soma = sum(d * p for d, p in zip(digitos, pesos))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cnpj_valido(cnpj: str) -> bool:
    if len(cnpj) != 14 or not cnpj.isascii() or not cnpj.isdigit():
        return False

    digitos = [int(c) for c in cnpj]
    dv1 = _digito_verificador(digitos[:12], _PESOS_DV1)
    dv2 = _digito_verificador(digitos[:12] + [dv1], _PESOS_DV2)

    return digitos[12] == dv1 and digitos[13] == dv2


def extrair_cnpj(texto: str) -> str | None:
    formatado = _PADRAO_FORMATADO.search(texto)
    if formatado:
        return re.sub(r"\D", "", formatado.group())

    rotulado = _PADRAO_ROTULADO.search(texto)
    if rotulado:
        return rotulado.group(1)

    return None
