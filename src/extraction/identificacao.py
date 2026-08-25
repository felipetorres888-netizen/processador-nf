# src/extraction/identificacao.py
"""Orquestra os extratores de campo em um único IdentificacaoNF, com
confiança por campo (spec §14) — sem IA, tudo determinístico (spec §40)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.extraction.campos_simples import (
    extrair_data_emissao,
    extrair_numero_serie,
    extrair_valor_total,
)
from src.extraction.chave_acesso import chave_acesso_valida, extrair_chave_acesso
from src.extraction.cnpj import cnpj_valido, extrair_cnpj


@dataclass
class CampoComConfianca:
    valor: Any
    confianca: float
    origem: str


@dataclass
class IdentificacaoNF:
    chave_acesso: CampoComConfianca
    cnpj_emitente: CampoComConfianca
    numero: CampoComConfianca
    serie: CampoComConfianca
    data_emissao: CampoComConfianca
    valor_total: CampoComConfianca


def _campo_nao_encontrado() -> CampoComConfianca:
    return CampoComConfianca(valor=None, confianca=0.0, origem="nao_encontrado")


def _campo_regex(valor: Any) -> CampoComConfianca:
    if valor is None:
        return _campo_nao_encontrado()
    return CampoComConfianca(valor=valor, confianca=0.7, origem="regex")


def extrair_identificacao(texto: str) -> IdentificacaoNF:
    chave = extrair_chave_acesso(texto)
    if chave is None:
        chave_campo = _campo_nao_encontrado()
    else:
        valida = chave_acesso_valida(chave)
        chave_campo = CampoComConfianca(
            valor=chave, confianca=1.0 if valida else 0.3, origem="regex+dv"
        )

    cnpj = extrair_cnpj(texto)
    if cnpj is None:
        cnpj_campo = _campo_nao_encontrado()
    else:
        valido = cnpj_valido(cnpj)
        cnpj_campo = CampoComConfianca(
            valor=cnpj, confianca=1.0 if valido else 0.3, origem="regex+dv"
        )

    numero, serie = extrair_numero_serie(texto)
    data = extrair_data_emissao(texto)
    valor_total = extrair_valor_total(texto)

    return IdentificacaoNF(
        chave_acesso=chave_campo,
        cnpj_emitente=cnpj_campo,
        numero=_campo_regex(numero),
        serie=_campo_regex(serie),
        data_emissao=_campo_regex(data),
        valor_total=_campo_regex(valor_total),
    )
