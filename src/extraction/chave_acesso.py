"""Extração e validação da chave de acesso da NF-e (Fase 3a).

44 dígitos, dígito verificador (o último) calculado por mod-11 com pesos
2-9 cíclicos da direita pra esquerda — mesmo algoritmo usado em boleto.
"""

from __future__ import annotations

import re

# Chave em grupos de 4 (como impressa no DANFE) ou como string continua de
# 44 digitos.
_PADRAO_AGRUPADO = re.compile(r"(?:\d{4}[ .]?){10}\d{4}")


def _digito_verificador(digitos_43: str) -> int:
    pesos = [2, 3, 4, 5, 6, 7, 8, 9] * 6
    pesos = pesos[:43][::-1]
    soma = sum(int(d) * p for d, p in zip(digitos_43, pesos))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def chave_acesso_valida(chave: str) -> bool:
    if len(chave) != 44 or not chave.isdigit():
        return False
    return int(chave[-1]) == _digito_verificador(chave[:43])


def extrair_chave_acesso(texto: str) -> str | None:
    match = _PADRAO_AGRUPADO.search(texto)
    if not match:
        return None
    return re.sub(r"\D", "", match.group())
