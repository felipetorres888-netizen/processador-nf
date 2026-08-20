# Processador NF — Fase 1 (PDF → Texto Nativo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working prototype that takes one or more PDFs, detects whether each has usable native text, extracts that text per page, reports page counts, and saves the result — with zero OCR, zero AI, zero GUI, zero database. This is Fase 1 of the 12-phase "Mega Prompt — Sistema Local de Processamento de Notas Fiscais" spec (`~/Downloads/Mega Prompt — Sistema Local de Processamento de Notas Fiscais para Redução de Tokens.md`).

**Architecture:** A small `src/pdf/reader.py` module wraps PyMuPDF (`fitz`) to open a PDF, extract text per page, and decide (via a char-count heuristic) whether the text is native/usable or the page will need OCR in a later phase — it never runs OCR itself. A `src/cli/phase1_cli.py` module walks a file or folder of PDFs, calls the reader for each, saves a `.txt` per PDF, continues past per-file errors, and prints a batch summary. No modules from later phases (OCR, parsing, validation, DB, GUI) are touched.

**Tech Stack:** Python 3.12.10 (already installed), PyMuPDF (`pymupdf`, not yet installed), pytest (not yet installed), stdlib `argparse`/`pathlib`/`dataclasses`.

## Global Constraints

- Original PDFs are never moved or modified — only read (spec §9).
- No single mega-file: PDF logic lives in `src/pdf/`, CLI logic in `src/cli/` (spec §31).
- No IA, no complex DB, no sophisticated UI, no supplier system, no advanced export in this phase (spec §38).
- A batch must continue past a single file's error, not abort (spec §8, §36 Fase 7 is later — but the CLI's error-isolation is needed from the start per §38's "mostrar resultado").
- PyMuPDF was chosen over pdfplumber/poppler-based tools because the environment inspection (2026-08-20) found no `poppler` (`pdftoppm`) on PATH and no Tesseract installed; PyMuPDF needs neither binary for text extraction and can also rasterize pages later for OCR (Fase 2) without adding a poppler dependency.
- Project root: `C:\Users\felip\ProcessadorNF`. Data folders (`entrada/`, `resultado/texto_ocr/`, etc.) already scaffolded per spec §9.

---

### Task 1: Project scaffolding — dependencies, git, config

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\requirements.txt`
- Create: `C:\Users\felip\ProcessadorNF\.gitignore`
- Create: `C:\Users\felip\ProcessadorNF\README.md`
- Create: `C:\Users\felip\ProcessadorNF\src\__init__.py`
- Create: `C:\Users\felip\ProcessadorNF\src\pdf\__init__.py`
- Create: `C:\Users\felip\ProcessadorNF\src\cli\__init__.py`
- Create: `C:\Users\felip\ProcessadorNF\tests\__init__.py`
- Create: `C:\Users\felip\ProcessadorNF\tests\pdf\__init__.py`

**Interfaces:**
- Produces: an installed `pymupdf` + `pytest` environment every later task relies on; empty `__init__.py` files making `src.pdf`, `src.cli`, `tests.pdf` importable packages.

- [ ] **Step 1: Write `requirements.txt`**

```text
pymupdf>=1.24,<2.0
pytest>=8.0,<9.0
```

- [ ] **Step 2: Write `.gitignore`**

```text
__pycache__/
*.pyc
.pytest_cache/
entrada/*
!entrada/.gitkeep
processados/*
!processados/.gitkeep
revisao/*
!revisao/.gitkeep
erro/*
!erro/.gitkeep
resultado/**/*
!resultado/**/.gitkeep
logs/*
!logs/.gitkeep
banco/*
!banco/.gitkeep
```

- [ ] **Step 3: Write `README.md`**

```markdown
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
```

- [ ] **Step 4: Create empty `__init__.py` files**

Create each of these as an empty file: `src\__init__.py`, `src\pdf\__init__.py`, `src\cli\__init__.py`, `tests\__init__.py`, `tests\pdf\__init__.py`.

- [ ] **Step 5: Create `.gitkeep` placeholders for empty data folders**

Create empty files: `entrada\.gitkeep`, `processados\.gitkeep`, `revisao\.gitkeep`, `erro\.gitkeep`, `logs\.gitkeep`, `banco\.gitkeep`, `resultado\json\.gitkeep`, `resultado\markdown\.gitkeep`, `resultado\texto_ocr\.gitkeep`.

- [ ] **Step 6: Create virtualenv and install dependencies**

Run (from `C:\Users\felip\ProcessadorNF`):
```bash
python -m venv .venv
.venv/Scripts/python -m pip install --upgrade pip
.venv/Scripts/python -m pip install -r requirements.txt
```
Expected: `pymupdf` and `pytest` install without errors.

- [ ] **Step 7: Init git and commit scaffolding**

```bash
git init
git add -A
git commit -m "chore: scaffold ProcessadorNF Fase 1 project structure"
```

---

### Task 2: `src/pdf/reader.py` — open PDF, extract native text, detect if usable

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\src\pdf\reader.py`
- Test: `C:\Users\felip\ProcessadorNF\tests\pdf\test_reader.py`

**Interfaces:**
- Consumes: `fitz` (from `pymupdf` package, imported as `import fitz`).
- Produces (used by Task 3):
  - `class PDFInvalidoError(Exception)` — raised when a path doesn't exist or isn't a readable PDF.
  - `class ResultadoExtracao` (dataclass) with fields: `arquivo: pathlib.Path`, `num_paginas: int`, `texto_por_pagina: list[str]`, `texto_completo: str`, `possui_texto_nativo: bool`, `caracteres_totais: int`.
  - `def processar_pdf(caminho: pathlib.Path, min_chars_por_pagina: int = 30) -> ResultadoExtracao`

- [ ] **Step 1: Write the failing tests**

```python
# tests/pdf/test_reader.py
from pathlib import Path

import fitz
import pytest

from src.pdf.reader import PDFInvalidoError, ResultadoExtracao, processar_pdf


def _criar_pdf_com_texto(caminho: Path, paginas_texto: list[str]) -> None:
    doc = fitz.open()
    for texto in paginas_texto:
        pagina = doc.new_page()
        if texto:
            pagina.insert_text((72, 72), texto, fontsize=12)
    doc.save(str(caminho))
    doc.close()


def _criar_pdf_sem_texto(caminho: Path, num_paginas: int = 1) -> None:
    doc = fitz.open()
    for _ in range(num_paginas):
        pagina = doc.new_page()
        # Desenha um retângulo (conteúdo gráfico, sem nenhum objeto de texto)
        pagina.draw_rect(fitz.Rect(50, 50, 200, 200))
    doc.save(str(caminho))
    doc.close()


def test_processar_pdf_com_texto_nativo(tmp_path):
    caminho = tmp_path / "nota_com_texto.pdf"
    _criar_pdf_com_texto(caminho, ["NOTA FISCAL 12345 - Fornecedor XYZ - Total R$ 797,50"])

    resultado = processar_pdf(caminho)

    assert isinstance(resultado, ResultadoExtracao)
    assert resultado.num_paginas == 1
    assert "NOTA FISCAL 12345" in resultado.texto_por_pagina[0]
    assert "NOTA FISCAL 12345" in resultado.texto_completo
    assert resultado.possui_texto_nativo is True
    assert resultado.caracteres_totais > 30


def test_processar_pdf_multiplas_paginas(tmp_path):
    caminho = tmp_path / "nota_multipagina.pdf"
    _criar_pdf_com_texto(
        caminho,
        ["Pagina um com texto suficiente para contar", "Pagina dois com texto suficiente tambem"],
    )

    resultado = processar_pdf(caminho)

    assert resultado.num_paginas == 2
    assert len(resultado.texto_por_pagina) == 2
    assert "Pagina um" in resultado.texto_por_pagina[0]
    assert "Pagina dois" in resultado.texto_por_pagina[1]


def test_processar_pdf_sem_texto_nativo_detectado(tmp_path):
    caminho = tmp_path / "nota_escaneada.pdf"
    _criar_pdf_sem_texto(caminho, num_paginas=1)

    resultado = processar_pdf(caminho)

    assert resultado.num_paginas == 1
    assert resultado.possui_texto_nativo is False
    assert resultado.caracteres_totais == 0


def test_processar_pdf_inexistente_levanta_erro(tmp_path):
    caminho = tmp_path / "nao_existe.pdf"

    with pytest.raises(PDFInvalidoError):
        processar_pdf(caminho)


def test_processar_pdf_corrompido_levanta_erro(tmp_path):
    caminho = tmp_path / "corrompido.pdf"
    caminho.write_bytes(b"isto nao e um pdf valido")

    with pytest.raises(PDFInvalidoError):
        processar_pdf(caminho)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/pdf/test_reader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.pdf.reader'` (or `ImportError`).

- [ ] **Step 3: Write the implementation**

```python
# src/pdf/reader.py
"""Leitura de PDF e extração de texto nativo (Fase 1).

Não faz OCR. Apenas abre o PDF, extrai o texto embutido de cada página e
decide, por uma heurística de contagem de caracteres, se esse texto nativo
é suficiente para uso ou se a página precisará de OCR em uma fase futura.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz


class PDFInvalidoError(Exception):
    """Levantado quando o caminho não existe ou não é um PDF legível."""


@dataclass
class ResultadoExtracao:
    arquivo: Path
    num_paginas: int
    texto_por_pagina: list[str]
    texto_completo: str
    possui_texto_nativo: bool
    caracteres_totais: int


def _abrir_pdf(caminho: Path) -> fitz.Document:
    if not caminho.exists():
        raise PDFInvalidoError(f"Arquivo não encontrado: {caminho}")
    try:
        return fitz.open(str(caminho))
    except Exception as exc:  # fitz levanta várias exceções internas para PDF inválido
        raise PDFInvalidoError(f"Não foi possível abrir o PDF: {caminho} ({exc})") from exc


def _extrair_texto_por_pagina(doc: fitz.Document) -> list[str]:
    return [pagina.get_text("text") for pagina in doc]


def _possui_texto_suficiente(texto_por_pagina: list[str], min_chars_por_pagina: int) -> bool:
    if not texto_por_pagina:
        return False
    total_chars = sum(len(t.strip()) for t in texto_por_pagina)
    media_por_pagina = total_chars / len(texto_por_pagina)
    return media_por_pagina >= min_chars_por_pagina


def processar_pdf(caminho: Path, min_chars_por_pagina: int = 30) -> ResultadoExtracao:
    doc = _abrir_pdf(caminho)
    try:
        texto_por_pagina = _extrair_texto_por_pagina(doc)
        num_paginas = doc.page_count
    finally:
        doc.close()

    texto_completo = "\n\n".join(texto_por_pagina)
    caracteres_totais = sum(len(t.strip()) for t in texto_por_pagina)
    possui_texto_nativo = _possui_texto_suficiente(texto_por_pagina, min_chars_por_pagina)

    return ResultadoExtracao(
        arquivo=caminho,
        num_paginas=num_paginas,
        texto_por_pagina=texto_por_pagina,
        texto_completo=texto_completo,
        possui_texto_nativo=possui_texto_nativo,
        caracteres_totais=caracteres_totais,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/pdf/test_reader.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/pdf/reader.py tests/pdf/test_reader.py
git commit -m "feat: extract native PDF text and detect if OCR will be needed"
```

---

### Task 3: `src/cli/phase1_cli.py` — batch runner over a file or folder

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\src\cli\phase1_cli.py`
- Test: `C:\Users\felip\ProcessadorNF\tests\cli\test_phase1_cli.py`
- Create: `C:\Users\felip\ProcessadorNF\tests\cli\__init__.py`

**Interfaces:**
- Consumes: `processar_pdf`, `ResultadoExtracao`, `PDFInvalidoError` from `src.pdf.reader` (Task 2).
- Produces:
  - `def listar_pdfs(entrada: pathlib.Path) -> list[pathlib.Path]`
  - `def salvar_texto(resultado: ResultadoExtracao, pasta_saida: pathlib.Path) -> pathlib.Path`
  - `def processar_lote(entrada: pathlib.Path, pasta_saida: pathlib.Path) -> dict` — returns `{"processados": int, "erros": int, "detalhes": list[dict]}` where each detail dict has `{"arquivo": str, "status": "OK"|"ERRO", "num_paginas": int|None, "possui_texto_nativo": bool|None, "erro": str|None}`.
  - `def main(argv: list[str] | None = None) -> int` — argparse CLI entrypoint (`python -m src.cli.phase1_cli <entrada> --saida <pasta>`), returns process exit code.

- [ ] **Step 1: Write the failing tests**

```python
# tests/cli/test_phase1_cli.py
from pathlib import Path

import fitz

from src.cli.phase1_cli import listar_pdfs, processar_lote, salvar_texto
from src.pdf.reader import processar_pdf


def _criar_pdf_com_texto(caminho: Path, texto: str) -> None:
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), texto, fontsize=12)
    doc.save(str(caminho))
    doc.close()


def test_listar_pdfs_arquivo_unico(tmp_path):
    pdf = tmp_path / "nota.pdf"
    _criar_pdf_com_texto(pdf, "conteudo")

    resultado = listar_pdfs(pdf)

    assert resultado == [pdf]


def test_listar_pdfs_pasta_com_varios_arquivos(tmp_path):
    _criar_pdf_com_texto(tmp_path / "a.pdf", "conteudo a")
    _criar_pdf_com_texto(tmp_path / "b.pdf", "conteudo b")
    (tmp_path / "nao_e_pdf.txt").write_text("ignorar")

    resultado = listar_pdfs(tmp_path)

    nomes = sorted(p.name for p in resultado)
    assert nomes == ["a.pdf", "b.pdf"]


def test_salvar_texto_grava_arquivo_txt(tmp_path):
    pdf = tmp_path / "nota.pdf"
    _criar_pdf_com_texto(pdf, "NOTA FISCAL 999")
    resultado = processar_pdf(pdf)
    pasta_saida = tmp_path / "saida"

    caminho_txt = salvar_texto(resultado, pasta_saida)

    assert caminho_txt.exists()
    assert caminho_txt.name == "nota.txt"
    assert "NOTA FISCAL 999" in caminho_txt.read_text(encoding="utf-8")


def test_processar_lote_continua_apos_erro(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_texto(entrada / "boa.pdf", "nota valida com texto suficiente para passar")
    (entrada / "invalida.pdf").write_bytes(b"nao e um pdf valido")
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    assert resumo["processados"] == 1
    assert resumo["erros"] == 1
    assert len(resumo["detalhes"]) == 2
    status_por_arquivo = {d["arquivo"]: d["status"] for d in resumo["detalhes"]}
    assert status_por_arquivo["boa.pdf"] == "OK"
    assert status_por_arquivo["invalida.pdf"] == "ERRO"
    assert (pasta_saida / "boa.txt").exists()
    assert not (pasta_saida / "invalida.txt").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/cli/test_phase1_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.cli.phase1_cli'`.

- [ ] **Step 3: Write the implementation**

```python
# src/cli/phase1_cli.py
"""CLI de lote da Fase 1: PDF(s) -> detectar texto -> extrair -> salvar -> mostrar resultado.

Nunca move ou apaga o PDF original. Um arquivo com erro não interrompe o lote.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.pdf.reader import PDFInvalidoError, ResultadoExtracao, processar_pdf


def listar_pdfs(entrada: Path) -> list[Path]:
    if entrada.is_file():
        return [entrada]
    return sorted(p for p in entrada.glob("*.pdf") if p.is_file())


def salvar_texto(resultado: ResultadoExtracao, pasta_saida: Path) -> Path:
    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho_txt = pasta_saida / f"{resultado.arquivo.stem}.txt"
    caminho_txt.write_text(resultado.texto_completo, encoding="utf-8")
    return caminho_txt


def processar_lote(entrada: Path, pasta_saida: Path) -> dict:
    detalhes: list[dict] = []
    processados = 0
    erros = 0

    for pdf in listar_pdfs(entrada):
        try:
            resultado = processar_pdf(pdf)
            salvar_texto(resultado, pasta_saida)
            processados += 1
            detalhes.append(
                {
                    "arquivo": pdf.name,
                    "status": "OK",
                    "num_paginas": resultado.num_paginas,
                    "possui_texto_nativo": resultado.possui_texto_nativo,
                    "erro": None,
                }
            )
        except PDFInvalidoError as exc:
            erros += 1
            detalhes.append(
                {
                    "arquivo": pdf.name,
                    "status": "ERRO",
                    "num_paginas": None,
                    "possui_texto_nativo": None,
                    "erro": str(exc),
                }
            )

    return {"processados": processados, "erros": erros, "detalhes": detalhes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Processador NF - Fase 1 (PDF -> texto nativo)")
    parser.add_argument("entrada", type=Path, help="Arquivo PDF ou pasta com PDFs")
    parser.add_argument(
        "--saida", type=Path, default=Path("resultado/texto_ocr"), help="Pasta de saída dos .txt"
    )
    args = parser.parse_args(argv)

    if not args.entrada.exists():
        print(f"Caminho de entrada não encontrado: {args.entrada}", file=sys.stderr)
        return 1

    resumo = processar_lote(args.entrada, args.saida)

    print(f"Processados: {resumo['processados']}")
    print(f"Erros: {resumo['erros']}")
    for d in resumo["detalhes"]:
        if d["status"] == "OK":
            origem = "texto_nativo" if d["possui_texto_nativo"] else "precisa_ocr"
            print(f"  OK    {d['arquivo']:40s} paginas={d['num_paginas']:<3} origem={origem}")
        else:
            print(f"  ERRO  {d['arquivo']:40s} {d['erro']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/cli/test_phase1_cli.py -v`
Expected: 4 passed.

- [ ] **Step 5: Run the full test suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all 9 tests (5 from Task 2 + 4 from Task 3) pass.

- [ ] **Step 6: Commit**

```bash
git add src/cli/phase1_cli.py tests/cli/test_phase1_cli.py tests/cli/__init__.py
git commit -m "feat: add Fase 1 batch CLI (folder/file -> txt, error-isolated)"
```

---

### Task 4: Manual validation against real NF PDFs

**Files:** none created — this is a verification step per spec §37 ("testar → corrigir → validar" before considering a phase done).

**Interfaces:**
- Consumes: `main` from `src.cli.phase1_cli` (Task 3), real PDF files supplied by the user.

- [ ] **Step 1: Ask the user to drop 3-5 real NF PDFs into `entrada/`**

These should include at least one CamScanner-scanned NF (image-only, to confirm `possui_texto_nativo=False` is detected correctly) and one born-digital PDF if available.

- [ ] **Step 2: Run the CLI against them**

Run: `.venv/Scripts/python -m src.cli.phase1_cli entrada --saida resultado/texto_ocr`

- [ ] **Step 3: Inspect the output**

Check `resultado/texto_ocr/*.txt` for each input PDF; confirm page counts printed match the actual PDFs, and that scanned/image-only NFs are correctly flagged `origem=precisa_ocr` (not silently treated as having usable text).

- [ ] **Step 4: Report and fix**

If any PDF crashes the batch instead of being isolated as an error, or if the native-text heuristic misclassifies a real scanned NF, fix `src/pdf/reader.py` or `src/cli/phase1_cli.py` and re-run Steps 2-3 until correct. Only then is Fase 1 considered done (per spec §37: "Não considere uma fase concluída apenas porque o código foi escrito. Ela deve estar funcionando.").

---

## Next Phase

Fase 2 (OCR local) requires installing Tesseract OCR (not present on this machine — `winget` is available and can install it) plus `opencv-python` and `pytesseract`, and will consume `ResultadoExtracao.possui_texto_nativo` from this phase's `reader.py` to decide which pages need OCR. That is a separate plan, written after Fase 1 is validated.
