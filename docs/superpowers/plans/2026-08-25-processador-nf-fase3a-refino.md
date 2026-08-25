# Processador NF — Fase 3a Refinamento (data_emissao / valor_total) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the two weakest extractors from Fase 3a's real-OCR validation — `extrair_data_emissao` (0/6 real files) and `extrair_valor_total` (1/6) — using the ACTUAL DANFE table structure observed in the project's 6 real OCR text files (not guesswork), grounded by direct inspection of `resultado/texto_ocr/*.txt`.

**Root cause (found by inspecting the real files directly, not assumed):** DANFEs render as a label row followed by a value row on the line(s) below, e.g.:
```
NOMERAZÃO SOCIAL CNPYCPF DATA DA EMISSÃO

PRIME4S BAR & RESTAURANTE LTDA 62.833.832/0001-46  |19/08/2026
```
and
```
VYVALOR DO FRSTE VYALOR DO SEGURO DESCONTO Om DESPESAS ACESSÓRIAS VALOR DOIPI ' - [VALOR TOTAL DA NOTA_
: 10,95| -. 000 —— 0,00 — 0,00 | : 0,00 | . 284,95
```
The original Fase 3a regexes required the value directly adjacent to the label on the same line (`\D{0,10}`/`\D{0,15}` gap) — real DANFEs put the value on the *next* line, sometimes after a blank line. `data_emissao`'s date is safely findable as "the first date-shaped (`\d{2}/\d{2}/\d{4}`) token after the label within a wider window" because a CNPJ (one `/`) never accidentally matches that two-`/` shape. `valor_total` is harder: "VALOR TOTAL DA NOTA" is always the LAST label in its row, and its value is the LAST monetary-shaped token on the following value line — several *other* columns' values (frete, seguro, desconto...) appear earlier on that same line, so "first monetary match after the label" would silently grab the wrong column (confirmed by inspection: TRILIX's value row is `10,95| -. 000 —— 0,00 — 0,00 | : 0,00 | . 284,95` — the real total, `284,95`, is last, not first).

**Architecture:** Both fixes live entirely in `src/extraction/campos_simples.py` — no other file changes. `extrair_data_emissao` keeps its existing single-regex approach but widens the label pattern (tolerates "DA"/"DE"/merged, per real OCR variance) and the gap between label and value (via `re.DOTALL` and a larger window) so it can reach across the blank-line-then-value-row structure. `extrair_valor_total` becomes two-stage: try the original label+R$-adjacent pattern first (keeps existing non-DANFE test cases working, e.g. a simple receipt with "Valor Total: R$ 797,50" on one line), then fall back to a line-based DANFE strategy (find the label line, take the *last* monetary token from the next 1-2 lines) only if the first pattern doesn't match.

**Tech Stack:** Pure Python stdlib (`re`) — no new dependencies, consistent with Fase 3a.

## Global Constraints

- No AI/LLM calls (spec §3, §40) — still regex + deterministic parsing only.
- Neither extractor may raise on missing/unparseable input — both return `None` on no match, exactly as today.
- `src/extraction/cnpj.py`, `src/extraction/chave_acesso.py`, `src/extraction/identificacao.py` are NOT touched by this plan — this is a narrow, isolated fix to two functions in one file.
- All of Fase 3a's existing 59 tests must keep passing unchanged — this plan only ADDS capability (new fallback paths), it must not regress the cases that already worked (e.g. HORTIFRUTI's simple `"Valor Total da Nota: R$ 797,50"` layout, or the synthetic test fixtures in `tests/extraction/test_campos_simples.py`).
- Project root: `C:\Users\felip\ProcessadorNF`.

---

### Task 1: Widen `extrair_data_emissao` and rebuild `extrair_valor_total` for the real DANFE table layout

**Files:**
- Modify: `C:\Users\felip\ProcessadorNF\src\extraction\campos_simples.py`
- Modify: `C:\Users\felip\ProcessadorNF\tests\extraction\test_campos_simples.py` (add new tests; do not remove or weaken existing ones)

**Interfaces:**
- No signature changes: `extrair_data_emissao(texto: str) -> str | None` and `extrair_valor_total(texto: str) -> float | None` keep their exact existing signatures — only their internal implementation and regex patterns change.

- [ ] **Step 1: Write the failing tests (new ones — append to the existing file, keep all current tests as-is)**

```python
# Append to tests/extraction/test_campos_simples.py

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
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `.venv/Scripts/python -m pytest tests/extraction/test_campos_simples.py -v`
Expected: the 7 pre-existing tests still PASS (implementation hasn't changed yet); the 7 new tests FAIL (current implementation doesn't handle the multi-line/table layout).

- [ ] **Step 3: Rewrite `extrair_data_emissao` and `extrair_valor_total` in `campos_simples.py`**

Replace the file's full content with:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/extraction/test_campos_simples.py -v`
Expected: 14 passed (7 pre-existing + 7 new). If `test_extrair_data_emissao_nao_confunde_com_data_de_saida_ou_impressao` fails, check that `_PADRAO_DATA` is genuinely anchored on "Emiss[aã]o" and not accidentally matching "Saida"/"Impressao" — do not weaken the other tests to compensate.

- [ ] **Step 5: Run the full suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests pass — 59 pre-existing + 7 new = 66 total.

- [ ] **Step 6: Re-validate against the 6 real NF OCR files**

Run:
```bash
.venv/Scripts/python -c "
from pathlib import Path
from src.extraction.identificacao import extrair_identificacao

for arquivo in sorted(Path('resultado/texto_ocr').glob('*.txt')):
    texto = arquivo.read_text(encoding='utf-8')
    resultado = extrair_identificacao(texto)
    print(f'--- {arquivo.name} ---')
    print(f'  Data: {resultado.data_emissao.valor} (confianca={resultado.data_emissao.confianca})')
    print(f'  Valor total: {resultado.valor_total.valor} (confianca={resultado.valor_total.confianca})')
"
```
Report the real recall honestly. Expected improvement based on direct inspection of the 6 files during this plan's design: `data_emissao` should now hit on CAPUEIRA and TRILIX at minimum (both confirmed to have the "label line, value on next line" structure by direct inspection); `valor_total` should now hit on TRILIX at minimum (confirmed `284,95` is recoverable via the last-value-on-next-line strategy). Some files may still miss (e.g. if their OCR text lost the value row entirely, not just misformatted it) — report the actual per-file result, do not force a match by loosening the regex further if a file still doesn't hit.

- [ ] **Step 7: Commit**

```bash
git add src/extraction/campos_simples.py tests/extraction/test_campos_simples.py
git commit -m "fix: recognize DANFE label-row/value-row layout for data_emissao and valor_total"
```

---

## Next Phase

Fase 3b (item-table extraction, spec §11) faces the same label-row/value-row DANFE structure at a larger scale (multiple item rows, more columns) — the line-based "find label, read next line(s)" technique proven here is a direct building block for that phase's design.
