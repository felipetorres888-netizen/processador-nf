# Processador NF — Fase 3a (Identificação da NF) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the NF-level identification fields (spec §10: chave de acesso, CNPJ emitente, número, série, data de emissão, valor total) from the text `ResultadoExtracaoCompleto.texto_completo` (Fase 2) produces, using regex + deterministic validation only (no AI, per spec §3/§40). Each field carries a confidence score and origin, per spec §14. This is a deliberately narrower slice than the full "Fase 3" the mega prompt names — item-table extraction (spec §11) is materially harder (multi-line tabular data, no consistent layout across suppliers) and is deferred to a follow-up plan; NF-level identification is a coherent, independently testable, and immediately useful subset, consistent with the project's own incremental-phase philosophy (spec §36-38).

**Architecture:** A new `src/extraction/` package holds one pure-function extractor per field group: `chave_acesso.py` (44-digit key + NFe mod-11 check digit), `cnpj.py` (14-digit CNPJ + its own two-check-digit mod-11 algorithm), and `campos_simples.py` (número/série, data de emissão, valor total — plain regex, no checksum). `src/extraction/identificacao.py` composes all of them into one `extrair_identificacao(texto: str) -> IdentificacaoNF` orchestrator, where `IdentificacaoNF` holds a `CampoComConfianca` (valor + confiança 0-1 + origem) per field, matching spec §14's JSON shape. Nothing here touches Fase 1/2's `src/pdf/`, `src/ocr/`, or `src/cli/` — this package only consumes a plain `str`, so it is testable with hand-written text fixtures and, separately, against the real OCR output already sitting in the project from Fase 2's validation.

**Tech Stack:** Pure Python stdlib (`re`, `dataclasses`) — no new dependencies.

## Global Constraints

- No AI/LLM calls anywhere in this phase (spec §3, §19, §40) — every field is regex + deterministic math only.
- Extractors never raise on missing/unparseable input — a field that can't be found returns a `CampoComConfianca` with `valor=None`, `confianca=0.0`, `origem="nao_encontrado"`, so one bad NF never crashes a batch (consistent with Fase 1/2's error-isolation philosophy, spec §8).
- Chave de acesso and CNPJ must be validated via their real check-digit algorithms when a candidate is found (spec §10: "chave de acesso deve ser validada quando possível") — a syntactically-shaped-but-checksum-invalid match is reported with low confidence, not silently accepted as correct.
- No mega-file: one file per field group under `src/extraction/`, composed by a single orchestrator file — spec §31.
- Original PDFs / OCR text are read-only inputs here — this phase produces new data, never mutates Fase 1/2's output structures.
- Project root: `C:\Users\felip\ProcessadorNF`.

---

### Task 1: `src/extraction/cnpj.py` — CNPJ extraction and validation

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\src\extraction\__init__.py` (empty)
- Create: `C:\Users\felip\ProcessadorNF\src\extraction\cnpj.py`
- Create: `C:\Users\felip\ProcessadorNF\tests\extraction\__init__.py` (empty)
- Create: `C:\Users\felip\ProcessadorNF\tests\extraction\test_cnpj.py`

**Interfaces:**
- Produces (used by Task 3): `def extrair_cnpj(texto: str) -> str | None` — returns the first CNPJ-shaped substring found (14 digits, formatting stripped), or `None` if none found. `def cnpj_valido(cnpj: str) -> bool` — takes a 14-digit string (no formatting) and returns whether its two check digits are mathematically correct.

- [ ] **Step 1: Write the failing tests**

```python
# tests/extraction/test_cnpj.py
from src.extraction.cnpj import cnpj_valido, extrair_cnpj


def test_cnpj_valido_aceita_cnpj_real_correto():
    # CNPJ real do projeto (Prime 4S Bar & Restaurante LTDA), recuperado via
    # OCR na validação da Fase 2 — usado aqui como caso de referência real.
    assert cnpj_valido("62833832000146") is True


def test_cnpj_valido_rejeita_digito_verificador_errado():
    # Mesmo CNPJ acima, mas com o último dígito verificador alterado.
    assert cnpj_valido("62833832000145") is False


def test_cnpj_valido_rejeita_string_de_tamanho_errado():
    assert cnpj_valido("123") is False
    assert cnpj_valido("") is False


def test_extrair_cnpj_encontra_formatado_com_pontuacao():
    texto = "Emitente\nCNPJ: 62.833.832/0001-46\nOutros dados"

    resultado = extrair_cnpj(texto)

    assert resultado == "62833832000146"


def test_extrair_cnpj_encontra_sem_pontuacao():
    texto = "CNPJ 62833832000146 conferido"

    resultado = extrair_cnpj(texto)

    assert resultado == "62833832000146"


def test_extrair_cnpj_retorna_none_quando_nao_ha_cnpj():
    texto = "Nota fiscal sem nenhum numero de documento aqui"

    resultado = extrair_cnpj(texto)

    assert resultado is None


def test_extrair_cnpj_ignora_sequencia_de_14_digitos_sem_formatacao_de_cnpj_por_perto():
    # 14 digitos soltos, sem rotulo "CNPJ" nem formatacao tipica proxima --
    # nao deve ser confundido com telefone/codigo de barras truncado.
    texto = "Codigo de rastreio: 11111111111111"

    resultado = extrair_cnpj(texto)

    assert resultado is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/extraction/test_cnpj.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.extraction.cnpj'`.

- [ ] **Step 3: Write the implementation**

```python
# src/extraction/cnpj.py
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
    if len(cnpj) != 14 or not cnpj.isdigit():
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/extraction/test_cnpj.py -v`
Expected: 7 passed. If `test_cnpj_valido_aceita_cnpj_real_correto` fails, do not weaken the assertion — double-check the weight arrays and the modulo/dv formula against a second known-valid CNPJ before concluding the reference number itself might be wrong.

- [ ] **Step 5: Commit**

```bash
git add src/extraction/__init__.py src/extraction/cnpj.py tests/extraction/__init__.py tests/extraction/test_cnpj.py
git commit -m "feat: extract and validate CNPJ (mod-11 check digits)"
```

---

### Task 2: `src/extraction/chave_acesso.py` — chave de acesso extraction and validation

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\src\extraction\chave_acesso.py`
- Create: `C:\Users\felip\ProcessadorNF\tests\extraction\test_chave_acesso.py`

**Interfaces:**
- Produces (used by Task 3): `def extrair_chave_acesso(texto: str) -> str | None` — returns the first 44-digit access-key-shaped substring found (spaces/formatting stripped), or `None`. `def chave_acesso_valida(chave: str) -> bool` — takes a 44-digit string and returns whether its final check digit is mathematically correct.

- [ ] **Step 1: Write the failing tests**

```python
# tests/extraction/test_chave_acesso.py
from src.extraction.chave_acesso import chave_acesso_valida, extrair_chave_acesso


def _chave_valida_de_teste() -> str:
    """Monta uma chave de 44 dígitos com o DV (dígito verificador) real,
    calculado pelo mesmo algoritmo mod-11 que o módulo implementa — usar
    uma chave sintética aqui (não uma chave real de NF-e) é o correto,
    já que o objetivo é testar a matemática do DV, não uma nota real."""
    corpo = "3526" + "0" * 39  # 43 dígitos quaisquer
    pesos = [2, 3, 4, 5, 6, 7, 8, 9] * 6
    pesos = pesos[:43][::-1]
    soma = sum(int(d) * p for d, p in zip(corpo, pesos))
    resto = soma % 11
    dv = 0 if resto < 2 else 11 - resto
    return corpo + str(dv)


def test_chave_acesso_valida_aceita_chave_com_dv_correto():
    assert chave_acesso_valida(_chave_valida_de_teste()) is True


def test_chave_acesso_valida_rejeita_dv_errado():
    chave = _chave_valida_de_teste()
    dv_errado = "0" if chave[-1] != "0" else "1"
    assert chave_acesso_valida(chave[:-1] + dv_errado) is False


def test_chave_acesso_valida_rejeita_tamanho_errado():
    assert chave_acesso_valida("123") is False


def test_extrair_chave_acesso_encontra_em_grupos_de_4_separados_por_espaco():
    chave = _chave_valida_de_teste()
    grupos = " ".join(chave[i : i + 4] for i in range(0, 44, 4))
    texto = f"Chave de acesso\n{grupos}\nConsulte pela chave de acesso"

    resultado = extrair_chave_acesso(texto)

    assert resultado == chave


def test_extrair_chave_acesso_encontra_string_continua_de_44_digitos():
    chave = _chave_valida_de_teste()
    texto = f"Numero da chave: {chave}"

    resultado = extrair_chave_acesso(texto)

    assert resultado == chave


def test_extrair_chave_acesso_retorna_none_quando_nao_ha_chave():
    texto = "Nota fiscal sem chave de acesso nenhuma"

    resultado = extrair_chave_acesso(texto)

    assert resultado is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/extraction/test_chave_acesso.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.extraction.chave_acesso'`.

- [ ] **Step 3: Write the implementation**

```python
# src/extraction/chave_acesso.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/extraction/test_chave_acesso.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/extraction/chave_acesso.py tests/extraction/test_chave_acesso.py
git commit -m "feat: extract and validate NF-e chave de acesso (mod-11 check digit)"
```

---

### Task 3: `src/extraction/campos_simples.py` + `src/extraction/identificacao.py` — remaining fields and orchestrator

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\src\extraction\campos_simples.py`
- Create: `C:\Users\felip\ProcessadorNF\src\extraction\identificacao.py`
- Create: `C:\Users\felip\ProcessadorNF\tests\extraction\test_campos_simples.py`
- Create: `C:\Users\felip\ProcessadorNF\tests\extraction\test_identificacao.py`

**Interfaces:**
- Consumes: `extrair_cnpj` from `src.extraction.cnpj` (Task 1), `extrair_chave_acesso`/`chave_acesso_valida` from `src.extraction.chave_acesso` (Task 2). Note: `cnpj_valido` is also consumed here to score confidence, alongside `extrair_cnpj`.
- Produces: `def extrair_numero_serie(texto: str) -> tuple[str | None, str | None]` (número, série), `def extrair_data_emissao(texto: str) -> str | None` (format `DD/MM/AAAA` as found, not reformatted — spec §10 doesn't mandate ISO normalization at this stage), `def extrair_valor_total(texto: str) -> float | None`, all in `campos_simples.py`. And in `identificacao.py`: `@dataclass class CampoComConfianca` (fields: `valor: object`, `confianca: float`, `origem: str`), `@dataclass class IdentificacaoNF` (fields: `chave_acesso: CampoComConfianca`, `cnpj_emitente: CampoComConfianca`, `numero: CampoComConfianca`, `serie: CampoComConfianca`, `data_emissao: CampoComConfianca`, `valor_total: CampoComConfianca`), `def extrair_identificacao(texto: str) -> IdentificacaoNF`.

- [ ] **Step 1: Write the failing tests**

```python
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
```

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/extraction/test_campos_simples.py tests/extraction/test_identificacao.py -v`
Expected: FAIL with `ModuleNotFoundError` for both new modules.

- [ ] **Step 3: Write the implementation**

```python
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
```

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/extraction/ -v`
Expected: all tests in `tests/extraction/` pass (7 from Task 1 + 6 from Task 2 + 7 from `test_campos_simples.py` + 3 from `test_identificacao.py` = 23).

- [ ] **Step 5: Run the full suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests pass — Fase 1+2's 29 plus this phase's 23 = 52 total, all green.

- [ ] **Step 6: Validate against real Fase 2 OCR output**

The 6 real NF `.txt` files already generated in `resultado/texto_ocr/` during Fase 2's validation (from the user's real CamScanner-scanned NFs) are real, messy OCR text — a much better validation input than any synthetic fixture. Run:
```bash
.venv/Scripts/python -c "
from pathlib import Path
from src.extraction.identificacao import extrair_identificacao

for arquivo in sorted(Path('resultado/texto_ocr').glob('*.txt')):
    texto = arquivo.read_text(encoding='utf-8')
    resultado = extrair_identificacao(texto)
    print(f'--- {arquivo.name} ---')
    print(f'  CNPJ: {resultado.cnpj_emitente.valor} (confianca={resultado.cnpj_emitente.confianca})')
    print(f'  Numero: {resultado.numero.valor} (confianca={resultado.numero.confianca})')
    print(f'  Data: {resultado.data_emissao.valor} (confianca={resultado.data_emissao.confianca})')
    print(f'  Valor total: {resultado.valor_total.valor} (confianca={resultado.valor_total.confianca})')
    print(f'  Chave de acesso: {resultado.chave_acesso.valor} (confianca={resultado.chave_acesso.confianca})')
"
```
Report the output honestly — real OCR text from CamScanner scans has typos, inconsistent spacing, and supplier-specific layouts the regexes above were not tuned against. Low/no extraction on several fields is an expected, informative result at this stage (spec §37: a phase isn't done just because code was written — but this validation step's job is to *measure* current recall accurately, not to force every field to match on the first attempt). Do not loosen the regexes to force a match; report the real hit rate per field across the 6 files, and note candidate regex gaps (e.g., a supplier's label wording that doesn't match `_PADRAO_NUMERO`/`_PADRAO_VALOR`) as a follow-up item rather than patching them into this task's scope.

- [ ] **Step 7: Commit**

```bash
git add src/extraction/campos_simples.py src/extraction/identificacao.py tests/extraction/test_campos_simples.py tests/extraction/test_identificacao.py
git commit -m "feat: extract NF identification fields (numero, serie, data, valor) with per-field confidence"
```

---

## Next Phase

Fase 3b (item-table extraction, spec §11) and Fase 4 (JSON output, spec §17, which will wrap `IdentificacaoNF` plus the eventual item list) are separate plans, written after this phase's real-OCR validation (Step 6) shows what recall to expect and which regex gaps matter most.
