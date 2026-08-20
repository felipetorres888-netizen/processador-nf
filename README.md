# Processador NF

Sistema local de processamento em lote de Notas Fiscais (PDF escaneado/nativo).
Local-first: nenhuma IA, nenhum upload externo nesta fase.

## Fase atual: Fase 1 — PDF → Texto Nativo

## Setup

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

## Uso

    python -m src.cli.phase1_cli entrada/ --saida resultado/texto_ocr

## Testes

    pytest
