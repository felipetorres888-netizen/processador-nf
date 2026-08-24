# Processador NF — Fase 2 (OCR Local) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** For pages that Fase 1 flagged as lacking usable native text, render the page to an image, preprocess it, run local OCR (Tesseract via pytesseract), and fill in real extracted text — without touching Fase 1's already-shipped `processar_pdf`/`ResultadoExtracao` contract. Still no AI, no GUI, no database.

**Architecture:** Four new, narrowly-scoped modules layer OCR on top of Fase 1 rather than modifying it: `src/pdf/render.py` rasterizes one PDF page to a numpy image via PyMuPDF; `src/ocr/preprocess.py` does pure OpenCV image cleanup (grayscale, deskew, adaptive threshold); `src/ocr/engine.py` wraps pytesseract with this environment's non-standard Tesseract location; `src/pdf/pipeline.py` composes all of it plus Fase 1's `processar_pdf` into `processar_pdf_completo`, which returns native text untouched for good pages and OCR text for the rest. The CLI (`src/cli/phase1_cli.py`) then swaps its one call from `processar_pdf` to `processar_pdf_completo` — everything else about it (listing, saving, batch error isolation) is unchanged and already tested.

**Tech Stack:** Adds `opencv-python`, `pytesseract`, `numpy`, `Pillow` to the existing Python 3.12.10 + PyMuPDF + pytest stack. Tesseract 5.4.0 (binary) and the `por` (Portuguese) language pack are already installed for this environment — see Global Constraints for their exact locations.

## Global Constraints

- Tesseract is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` but is **not** on the system PATH — every OCR call must set `pytesseract.pytesseract.tesseract_cmd` explicitly (via `src/ocr/config.py`), never assume `tesseract` is invokable bare.
- The Portuguese language file (`por.traineddata`) lives at `C:\Users\felip\ProcessadorNF\tessdata\por.traineddata` — a **project-local** folder, not Tesseract's own `tessdata` under Program Files (that folder isn't writable without admin rights and only has `eng`/`osd`). Every OCR call must pass `--tessdata-dir` pointing at this project-local folder. (Amendment, Task 4: the literal `--tessdata-dir "<path>"` pytesseract config-string was found broken on Windows — Tesseract's own config-string tokenizer mishandles the quoted path's backslashes — so the shipped code in `src/ocr/engine.py` sets the `TESSDATA_PREFIX` environment variable instead, which achieves the same override contract cross-platform.)
- Both paths above, plus the OCR language code (`por`), must be overridable via environment variables (`PROCESSADOR_NF_TESSERACT_CMD`, `PROCESSADOR_NF_TESSDATA_DIR`, `PROCESSADOR_NF_OCR_LANG`) so the project still runs on a machine where Tesseract is installed differently — hardcoded absolute paths with no override is not acceptable.
- Fase 1's `src/pdf/reader.py` (`PDFInvalidoError`, `ResultadoExtracao`, `processar_pdf`) is **not modified** in this phase — it already gives Fase 2 everything it needs (`paginas_com_texto_suficiente`, and the guarantee that only `PDFInvalidoError` ever escapes it). Fase 2 composes on top of it in a new module rather than editing it, so Fase 1's existing tests and review stay valid untouched.
- No mega-file: PDF rendering stays in `src/pdf/`, pure image math stays in `src/ocr/preprocess.py`, the Tesseract wrapper stays in `src/ocr/engine.py`, orchestration stays in `src/pdf/pipeline.py`.
- Original PDFs are never moved or modified — this phase only reads pages to render them; it never writes back into a PDF.
- No AI, no GUI, no database in this phase.
- `processar_pdf_completo` re-opens the PDF a second time (in addition to the open `processar_pdf` already does internally) to render pages for OCR. This is a deliberate trade-off — it avoids touching Fase 1's already-reviewed `reader.py` internals — not an oversight; do not flag it as a defect without weighing that trade-off.
- Project root: `C:\Users\felip\ProcessadorNF`.

---

### Task 1: Dependencies, OCR config, folder scaffolding

**Files:**
- Modify: `C:\Users\felip\ProcessadorNF\requirements.txt`
- Create: `C:\Users\felip\ProcessadorNF\src\ocr\__init__.py`
- Create: `C:\Users\felip\ProcessadorNF\src\ocr\config.py`
- Create: `C:\Users\felip\ProcessadorNF\tests\ocr\__init__.py`

**Interfaces:**
- Produces: `opencv-python`, `pytesseract`, `numpy`, `Pillow` installed in the project venv; `src.ocr.config` exporting `TESSERACT_CMD: str`, `TESSDATA_DIR: str`, `OCR_LANG: str` — every later task in this phase imports these three names.

- [ ] **Step 1: Update `requirements.txt`**

Replace the file's full content with:

```text
pymupdf>=1.24,<2.0
pytest>=8.0,<9.0
opencv-python>=4.9,<5.0
pytesseract>=0.3.10,<0.4
numpy>=1.26,<3.0
Pillow>=10.0,<12.0
```

- [ ] **Step 2: Write `src/ocr/config.py`**

```python
"""Configuração do motor de OCR (Fase 2).

O Tesseract não está no PATH deste ambiente Windows, e o pacote de idioma
português foi baixado para uma pasta local do projeto (fora de Program
Files, que exige permissão de administrador para escrita). Este módulo
centraliza os três valores que a Fase 2 precisa para encontrar o Tesseract
e seus dados de idioma — cada um substituível por variável de ambiente
para que o projeto funcione em outra máquina com instalação diferente.
"""

from __future__ import annotations

import os
from pathlib import Path

TESSERACT_CMD = os.environ.get(
    "PROCESSADOR_NF_TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)

TESSDATA_DIR = os.environ.get(
    "PROCESSADOR_NF_TESSDATA_DIR",
    str(Path(__file__).resolve().parent.parent.parent / "tessdata"),
)

OCR_LANG = os.environ.get("PROCESSADOR_NF_OCR_LANG", "por")
```

- [ ] **Step 3: Create `src/ocr/__init__.py` and `tests/ocr/__init__.py` (both empty)**

- [ ] **Step 4: Install the new dependencies**

Run (from `C:\Users\felip\ProcessadorNF`):
```bash
.venv/Scripts/python -m pip install -r requirements.txt
```
Expected: `opencv-python`, `pytesseract`, `numpy`, `Pillow` install without errors (pymupdf/pytest already satisfied).

- [ ] **Step 5: Verify the config resolves to real, existing paths**

Run:
```bash
.venv/Scripts/python -c "from src.ocr.config import TESSERACT_CMD, TESSDATA_DIR, OCR_LANG; import os; print(TESSERACT_CMD, os.path.exists(TESSERACT_CMD)); print(TESSDATA_DIR, os.path.exists(os.path.join(TESSDATA_DIR, 'por.traineddata'))); print(OCR_LANG)"
```
Expected: both `os.path.exists(...)` calls print `True`, and `OCR_LANG` prints `por`. If either is `False`, STOP and report BLOCKED — later tasks cannot do real OCR without this.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt src/ocr/__init__.py src/ocr/config.py tests/ocr/__init__.py
git commit -m "chore: add Fase 2 OCR dependencies and Tesseract/tessdata config"
```

---

### Task 2: `src/pdf/render.py` — rasterize a PDF page to an image

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\src\pdf\render.py`
- Test: `C:\Users\felip\ProcessadorNF\tests\pdf\test_render.py`

**Interfaces:**
- Consumes: `pymupdf` (`fitz.Page`, `fitz.Matrix`), `numpy`.
- Produces (used by Task 5): `def renderizar_pagina(pagina: fitz.Page, dpi: int = 300) -> np.ndarray` — returns a BGR `uint8` array shaped `(height, width, 3)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/pdf/test_render.py
import numpy as np
import pymupdf as fitz

from src.pdf.render import renderizar_pagina


def test_renderizar_pagina_dimensoes_esperadas_72dpi():
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)  # A4 em pontos (72 dpi)

    imagem = renderizar_pagina(pagina, dpi=72)

    assert imagem.shape == (842, 595, 3)
    assert imagem.dtype == np.uint8
    doc.close()


def test_renderizar_pagina_escala_com_dpi():
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)

    imagem_72 = renderizar_pagina(pagina, dpi=72)
    imagem_300 = renderizar_pagina(pagina, dpi=300)

    razao = imagem_300.shape[1] / imagem_72.shape[1]
    assert 4.0 < razao < 4.35  # 300/72 ~= 4.17
    doc.close()


def test_renderizar_pagina_com_texto_produz_pixels_nao_brancos():
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.insert_text((72, 72), "NOTA FISCAL", fontsize=24)

    imagem = renderizar_pagina(pagina, dpi=150)

    assert not np.all(imagem == 255)
    doc.close()


def test_renderizar_pagina_branca_e_praticamente_toda_branca():
    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)

    imagem = renderizar_pagina(pagina, dpi=150)

    assert np.mean(imagem) > 250
    doc.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/pdf/test_render.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.pdf.render'`.

- [ ] **Step 3: Write the implementation**

```python
# src/pdf/render.py
"""Renderização de páginas de PDF em imagens (Fase 2).

Converte uma página de um documento PyMuPDF já aberto em um array numpy
no formato BGR (convenção do OpenCV), na resolução (DPI) pedida. Não abre
nem fecha o documento — quem chama controla o ciclo de vida do
fitz.Document, do mesmo jeito que src/pdf/reader.py já faz.
"""

from __future__ import annotations

import numpy as np
import pymupdf as fitz


def renderizar_pagina(pagina: fitz.Page, dpi: int = 300) -> np.ndarray:
    zoom = dpi / 72
    matriz = fitz.Matrix(zoom, zoom)
    pixmap = pagina.get_pixmap(matrix=matriz, colorspace=fitz.csRGB, alpha=False)
    imagem = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
        pixmap.height, pixmap.width, pixmap.n
    )
    # RGB (saída do fitz) -> BGR (convenção do OpenCV)
    return imagem[:, :, ::-1].copy()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/pdf/test_render.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/pdf/render.py tests/pdf/test_render.py
git commit -m "feat: render PDF pages to numpy images for OCR"
```

---

### Task 3: `src/ocr/preprocess.py` — grayscale, deskew, binarize

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\src\ocr\preprocess.py`
- Test: `C:\Users\felip\ProcessadorNF\tests\ocr\test_preprocess.py`

**Interfaces:**
- Consumes: `opencv-python` (`cv2`), `numpy`, `Pillow` (`PIL.Image`, `PIL.ImageDraw` — test fixtures only).
- Produces (used by Task 5): `def para_cinza(imagem: np.ndarray) -> np.ndarray`, `def corrigir_inclinacao(imagem_cinza: np.ndarray) -> np.ndarray`, `def binarizar(imagem_cinza: np.ndarray) -> np.ndarray`, `def preprocessar(imagem: np.ndarray) -> np.ndarray` (composes all three: grayscale → deskew → binarize).

- [ ] **Step 1: Write the failing tests**

```python
# tests/ocr/test_preprocess.py
import numpy as np
from PIL import Image, ImageDraw

from src.ocr.preprocess import binarizar, corrigir_inclinacao, para_cinza


def _linha_de_texto_inclinada(angulo_graus: float) -> np.ndarray:
    """Cria uma imagem branca com um retângulo preto simulando uma linha de
    texto, rotacionada por um ângulo conhecido — como uma digitalização
    torta do CamScanner."""
    tela = Image.new("L", (600, 400), color=255)
    desenho = ImageDraw.Draw(tela)
    desenho.rectangle([100, 190, 500, 210], fill=0)
    tela = tela.rotate(angulo_graus, fillcolor=255, expand=False)
    return np.array(tela)


def _variacao_horizontal_por_linha(imagem_cinza: np.ndarray) -> float:
    """Mede o quão 'torta' a imagem está: para cada linha com pixel escuro,
    pega a posição x mais à esquerda; retorna o desvio padrão dessas
    posições entre as linhas. Uma imagem bem alinhada tem desvio baixo."""
    posicoes = []
    for linha in imagem_cinza:
        indices_escuros = np.where(linha < 128)[0]
        if indices_escuros.size > 0:
            posicoes.append(indices_escuros[0])
    return float(np.std(posicoes)) if len(posicoes) > 1 else 0.0


def test_para_cinza_reduz_para_um_canal():
    imagem_colorida = np.zeros((50, 50, 3), dtype=np.uint8)

    resultado = para_cinza(imagem_colorida)

    assert resultado.ndim == 2
    assert resultado.shape == (50, 50)


def test_para_cinza_imagem_ja_cinza_retorna_inalterada():
    imagem_cinza = np.full((30, 30), 128, dtype=np.uint8)

    resultado = para_cinza(imagem_cinza)

    assert resultado.shape == (30, 30)
    assert np.array_equal(resultado, imagem_cinza)


def test_corrigir_inclinacao_reduz_variacao_horizontal():
    inclinada = _linha_de_texto_inclinada(8.0)
    variacao_antes = _variacao_horizontal_por_linha(inclinada)

    corrigida = corrigir_inclinacao(inclinada)
    variacao_depois = _variacao_horizontal_por_linha(corrigida)

    assert variacao_depois < variacao_antes * 0.5


def test_corrigir_inclinacao_imagem_ja_reta_fica_praticamente_igual():
    reta = _linha_de_texto_inclinada(0.0)

    corrigida = corrigir_inclinacao(reta)

    assert _variacao_horizontal_por_linha(corrigida) < 3.0


def test_binarizar_produz_apenas_dois_valores():
    imagem_cinza = np.random.randint(0, 255, (100, 100), dtype=np.uint8).astype(np.uint8)

    resultado = binarizar(imagem_cinza)

    valores_unicos = set(np.unique(resultado).tolist())
    assert valores_unicos.issubset({0, 255})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/ocr/test_preprocess.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.ocr.preprocess'`.

- [ ] **Step 3: Write the implementation**

```python
# src/ocr/preprocess.py
"""Pré-processamento de imagem para OCR (Fase 2).

Aplica só os passos de maior impacto para digitalizações de Nota Fiscal
(CamScanner): escala de cinza, correção de inclinação (deskew) e
binarização adaptativa. Cada função é pura e testável isoladamente com
imagens sintéticas — nenhuma depende do Tesseract.
"""

from __future__ import annotations

import cv2
import numpy as np


def para_cinza(imagem: np.ndarray) -> np.ndarray:
    if imagem.ndim == 2:
        return imagem
    return cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)


def corrigir_inclinacao(imagem_cinza: np.ndarray) -> np.ndarray:
    """Corrige pequenas rotações (inclinação de digitalização) usando o
    ângulo do retângulo mínimo que envolve os pixels escuros (texto)."""
    invertida = cv2.bitwise_not(imagem_cinza)
    _, binaria = cv2.threshold(invertida, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(binaria > 0))
    if coords.shape[0] < 10:
        return imagem_cinza  # pouco ou nenhum conteúdo — nada a corrigir

    angulo = cv2.minAreaRect(coords)[-1]
    if angulo < -45:
        angulo = -(90 + angulo)
    else:
        angulo = -angulo

    if abs(angulo) < 0.1:
        return imagem_cinza  # já está reto o suficiente

    altura, largura = imagem_cinza.shape[:2]
    centro = (largura // 2, altura // 2)
    matriz_rotacao = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    return cv2.warpAffine(
        imagem_cinza,
        matriz_rotacao,
        (largura, altura),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def binarizar(imagem_cinza: np.ndarray) -> np.ndarray:
    """Binarização adaptativa: lida melhor com sombras/iluminação desigual
    do que um limiar fixo — comum em fotos de celular/CamScanner."""
    return cv2.adaptiveThreshold(
        imagem_cinza,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )


def preprocessar(imagem: np.ndarray) -> np.ndarray:
    """Pipeline completo: cinza -> deskew -> binarização."""
    cinza = para_cinza(imagem)
    corrigida = corrigir_inclinacao(cinza)
    return binarizar(corrigida)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/ocr/test_preprocess.py -v`
Expected: 5 passed. If `test_corrigir_inclinacao_reduz_variacao_horizontal` fails because the measured reduction is smaller than expected, the deskew angle-sign convention may need adjusting (try flipping the sign of `angulo` before `getRotationMatrix2D`) — this is a known ambiguity in OpenCV's `minAreaRect` angle convention across versions; fix by empirical verification (print `variacao_antes`/`variacao_depois` while iterating), not by weakening the test's threshold.

- [ ] **Step 5: Commit**

```bash
git add src/ocr/preprocess.py tests/ocr/test_preprocess.py
git commit -m "feat: add grayscale/deskew/binarize OCR preprocessing"
```

---

### Task 4: `src/ocr/engine.py` — pytesseract wrapper

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\src\ocr\engine.py`
- Test: `C:\Users\felip\ProcessadorNF\tests\ocr\test_engine.py`

**Interfaces:**
- Consumes: `pytesseract`, `numpy`, `TESSERACT_CMD`/`TESSDATA_DIR`/`OCR_LANG` from `src.ocr.config` (Task 1).
- Produces (used by Task 5): `def ocr_imagem(imagem: np.ndarray, lang: str = OCR_LANG) -> str`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/ocr/test_engine.py
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.ocr.engine import ocr_imagem


def _carregar_fonte(tamanho: int) -> ImageFont.FreeTypeFont:
    caminhos_candidatos = [
        "arial.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ]
    for caminho in caminhos_candidatos:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except OSError:
            continue
    return ImageFont.load_default()


def _imagem_com_texto(texto: str) -> np.ndarray:
    tela = Image.new("L", (800, 200), color=255)
    desenho = ImageDraw.Draw(tela)
    desenho.text((20, 60), texto, fill=0, font=_carregar_fonte(48))
    return np.array(tela)


def test_ocr_imagem_reconhece_texto_simples_e_grande():
    imagem = _imagem_com_texto("NOTA FISCAL")

    resultado = ocr_imagem(imagem)

    assert "NOTA" in resultado.upper()
    assert "FISCAL" in resultado.upper()


def test_ocr_imagem_pagina_em_branco_retorna_string_vazia():
    imagem_branca = np.full((200, 800), 255, dtype=np.uint8)

    resultado = ocr_imagem(imagem_branca)

    assert resultado.strip() == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/ocr/test_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.ocr.engine'`.

- [ ] **Step 3: Write the implementation**

```python
# src/ocr/engine.py
"""Wrapper do Tesseract via pytesseract (Fase 2).

Centraliza a configuração (binário do Tesseract fora do PATH, dados de
idioma locais ao projeto — ver src/ocr/config.py) para que o resto do
código só precise chamar ocr_imagem(imagem) e receber texto de volta.
"""

from __future__ import annotations

import numpy as np
import pytesseract

from src.ocr.config import OCR_LANG, TESSDATA_DIR, TESSERACT_CMD

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def ocr_imagem(imagem: np.ndarray, lang: str = OCR_LANG) -> str:
    """Executa OCR em uma imagem já pré-processada (numpy array) e retorna
    o texto reconhecido."""
    config = f'--tessdata-dir "{TESSDATA_DIR}"'
    texto = pytesseract.image_to_string(imagem, lang=lang, config=config)
    return texto.strip()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/ocr/test_engine.py -v`
Expected: 2 passed. If `test_ocr_imagem_reconhece_texto_simples_e_grande` fails because Tesseract can't be found, re-verify Task 1 Step 5's path check before touching this file — the bug is almost certainly in `src/ocr/config.py`'s paths, not here.

- [ ] **Step 5: Commit**

```bash
git add src/ocr/engine.py tests/ocr/test_engine.py
git commit -m "feat: wrap pytesseract with project-local Tesseract/tessdata config"
```

---

### Task 5: `src/pdf/pipeline.py` — compose native-text + OCR fallback

**Files:**
- Create: `C:\Users\felip\ProcessadorNF\src\pdf\pipeline.py`
- Test: `C:\Users\felip\ProcessadorNF\tests\pdf\test_pipeline.py`

**Interfaces:**
- Consumes: `processar_pdf`, `PDFInvalidoError` from `src.pdf.reader` (Fase 1, unmodified); `renderizar_pagina` from `src.pdf.render` (Task 2); `preprocessar` from `src.ocr.preprocess` (Task 3); `ocr_imagem` from `src.ocr.engine` (Task 4).
- Produces (used by Task 6): `class ResultadoExtracaoCompleto` (dataclass: `arquivo: Path`, `num_paginas: int`, `texto_por_pagina: list[str]`, `texto_completo: str`, `origem_por_pagina: list[str]` — each entry `"texto_nativo"` or `"ocr"`), `def processar_pdf_completo(caminho: Path, min_chars_por_pagina: int = 30, dpi: int = 300) -> ResultadoExtracaoCompleto`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/pdf/test_pipeline.py
from pathlib import Path

import pymupdf as fitz
import pytest

from src.pdf.pipeline import ResultadoExtracaoCompleto, processar_pdf_completo
from src.pdf.reader import PDFInvalidoError


def _pdf_com_texto_nativo(caminho: Path, texto: str) -> None:
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), texto, fontsize=12)
    doc.save(str(caminho))
    doc.close()


def _pdf_com_imagem_de_texto(caminho: Path, texto: str) -> None:
    """Simula uma NF escaneada: insere o texto como IMAGEM (não como texto
    nativo pesquisável), do jeito que um scan de celular/CamScanner produz."""
    from PIL import Image, ImageDraw

    tela = Image.new("RGB", (900, 300), color="white")
    desenho = ImageDraw.Draw(tela)
    desenho.text((30, 100), texto, fill="black")
    caminho_png = caminho.with_suffix(".png")
    tela.save(caminho_png)

    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.insert_image(fitz.Rect(50, 50, 545, 250), filename=str(caminho_png))
    doc.save(str(caminho))
    doc.close()
    caminho_png.unlink()


def test_processar_pdf_completo_texto_nativo_nao_usa_ocr(tmp_path):
    caminho = tmp_path / "nativa.pdf"
    _pdf_com_texto_nativo(caminho, "NOTA FISCAL 555 - TOTAL 100,00")

    resultado = processar_pdf_completo(caminho)

    assert isinstance(resultado, ResultadoExtracaoCompleto)
    assert resultado.origem_por_pagina == ["texto_nativo"]
    assert "NOTA FISCAL 555" in resultado.texto_por_pagina[0]


def test_processar_pdf_completo_pagina_escaneada_usa_ocr(tmp_path):
    caminho = tmp_path / "escaneada.pdf"
    _pdf_com_imagem_de_texto(caminho, "FORNECEDOR TESTE")

    resultado = processar_pdf_completo(caminho)

    assert resultado.origem_por_pagina == ["ocr"]
    assert "FORNECEDOR" in resultado.texto_por_pagina[0].upper()


def test_processar_pdf_completo_pdf_invalido_levanta_erro(tmp_path):
    caminho = tmp_path / "nao_existe.pdf"

    with pytest.raises(PDFInvalidoError):
        processar_pdf_completo(caminho)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tests/pdf/test_pipeline.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.pdf.pipeline'`.

- [ ] **Step 3: Write the implementation**

```python
# src/pdf/pipeline.py
"""Pipeline completo de extração de uma NF (Fase 2): texto nativo primeiro,
OCR local só nas páginas que precisarem (§3 do mega prompt).

Reaproveita processar_pdf da Fase 1 (que já garante que só PDFInvalidoError
escapa, e já decide por página se o texto nativo é suficiente) e só
adiciona OCR por cima, sem alterar o contrato da Fase 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz

from src.ocr.engine import ocr_imagem
from src.ocr.preprocess import preprocessar
from src.pdf.reader import PDFInvalidoError, processar_pdf
from src.pdf.render import renderizar_pagina


@dataclass
class ResultadoExtracaoCompleto:
    arquivo: Path
    num_paginas: int
    texto_por_pagina: list[str]
    texto_completo: str
    origem_por_pagina: list[str]  # "texto_nativo" ou "ocr"


def processar_pdf_completo(
    caminho: Path, min_chars_por_pagina: int = 30, dpi: int = 300
) -> ResultadoExtracaoCompleto:
    resultado_base = processar_pdf(caminho, min_chars_por_pagina)

    texto_final = list(resultado_base.texto_por_pagina)
    origem_por_pagina = [
        "texto_nativo" if suficiente else "ocr"
        for suficiente in resultado_base.paginas_com_texto_suficiente
    ]

    indices_para_ocr = [
        i
        for i, suficiente in enumerate(resultado_base.paginas_com_texto_suficiente)
        if not suficiente
    ]

    if indices_para_ocr:
        try:
            doc = fitz.open(str(caminho))
        except Exception as exc:
            raise PDFInvalidoError(
                f"Não foi possível reabrir o PDF para OCR: {caminho} ({exc})"
            ) from exc
        try:
            for indice in indices_para_ocr:
                pagina = doc[indice]
                imagem = renderizar_pagina(pagina, dpi=dpi)
                imagem_preparada = preprocessar(imagem)
                texto_final[indice] = ocr_imagem(imagem_preparada)
        finally:
            doc.close()

    return ResultadoExtracaoCompleto(
        arquivo=resultado_base.arquivo,
        num_paginas=resultado_base.num_paginas,
        texto_por_pagina=texto_final,
        texto_completo="\n\n".join(texto_final),
        origem_por_pagina=origem_por_pagina,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tests/pdf/test_pipeline.py -v`
Expected: 3 passed.

- [ ] **Step 5: Run the full suite so far**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests from Fase 1 (13) plus this phase's Tasks 2-5 (4+5+2+3=14) pass — 27 total, all green.

- [ ] **Step 6: Commit**

```bash
git add src/pdf/pipeline.py tests/pdf/test_pipeline.py
git commit -m "feat: compose native-text and OCR fallback into one pipeline"
```

---

### Task 6: Wire the CLI to the full pipeline

**Files:**
- Modify: `C:\Users\felip\ProcessadorNF\src\cli\phase1_cli.py` (full replacement — see content below)
- Modify: `C:\Users\felip\ProcessadorNF\tests\cli\test_phase1_cli.py` (full replacement — see content below)

**Interfaces:**
- Consumes: `ResultadoExtracaoCompleto`, `processar_pdf_completo` from `src.pdf.pipeline` (Task 5), replacing the direct dependency on `src.pdf.reader`.
- Produces: same public names as Fase 1 (`listar_pdfs`, `salvar_texto`, `processar_lote`, `main`) — signatures unchanged; `processar_lote`'s detail dicts keep the same shape (`possui_texto_nativo` is now derived as "every page in this file used native text, none needed OCR").

- [ ] **Step 1: Replace `src/cli/phase1_cli.py` with this full content**

```python
# src/cli/phase1_cli.py
"""CLI de lote: PDF(s) -> texto (nativo ou OCR) -> salvar -> mostrar resultado.

Nunca move ou apaga o PDF original. Um arquivo com erro não interrompe o
lote. Usa o pipeline completo da Fase 2 (src.pdf.pipeline): tenta texto
nativo primeiro, só recorre a OCR local nas páginas que precisarem.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.pdf.pipeline import ResultadoExtracaoCompleto, processar_pdf_completo


def listar_pdfs(entrada: Path) -> list[Path]:
    if entrada.is_file():
        return [entrada]
    return sorted(p for p in entrada.glob("*.pdf") if p.is_file())


def salvar_texto(resultado: ResultadoExtracaoCompleto, pasta_saida: Path) -> Path:
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
            resultado = processar_pdf_completo(pdf)
            salvar_texto(resultado, pasta_saida)
            processados += 1
            possui_texto_nativo = all(
                origem == "texto_nativo" for origem in resultado.origem_por_pagina
            )
            detalhes.append(
                {
                    "arquivo": pdf.name,
                    "status": "OK",
                    "num_paginas": resultado.num_paginas,
                    "possui_texto_nativo": possui_texto_nativo,
                    "erro": None,
                }
            )
        except Exception as exc:
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
    parser = argparse.ArgumentParser(description="Processador NF - PDF -> texto (nativo ou OCR)")
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
            origem = "texto_nativo" if d["possui_texto_nativo"] else "ocr_aplicado"
            print(f"  OK    {d['arquivo']:40s} paginas={d['num_paginas']:<3} origem={origem}")
        else:
            print(f"  ERRO  {d['arquivo']:40s} {d['erro']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Replace `tests/cli/test_phase1_cli.py` with this full content**

```python
# tests/cli/test_phase1_cli.py
from pathlib import Path

import pymupdf as fitz

from src.cli.phase1_cli import listar_pdfs, processar_lote, salvar_texto
from src.pdf.pipeline import processar_pdf_completo


def _criar_pdf_com_texto(caminho: Path, texto: str) -> None:
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), texto, fontsize=12)
    doc.save(str(caminho))
    doc.close()


def _criar_pdf_com_imagem_de_texto(caminho: Path, texto: str) -> None:
    """Simula uma NF escaneada de verdade: o texto vira imagem, não texto
    nativo pesquisável."""
    from PIL import Image, ImageDraw

    tela = Image.new("RGB", (900, 300), color="white")
    desenho = ImageDraw.Draw(tela)
    desenho.text((30, 100), texto, fill="black")
    caminho_png = caminho.with_suffix(".png")
    tela.save(caminho_png)

    doc = fitz.open()
    pagina = doc.new_page(width=595, height=842)
    pagina.insert_image(fitz.Rect(50, 50, 545, 250), filename=str(caminho_png))
    doc.save(str(caminho))
    doc.close()
    caminho_png.unlink()


def test_listar_pdfs_arquivo_unico(tmp_path):
    pdf = tmp_path / "nota.pdf"
    _criar_pdf_com_texto(pdf, "conteudo")

    resultado = listar_pdfs(pdf)

    assert resultado == [pdf]


def test_listar_pdfs_pasta_com_varios_arquivos(tmp_path):
    _criar_pdf_com_texto(tmp_path / "a.pdf", "conteudo a")
    _criar_pdf_com_texto(tmp_path / "b.pdf", "conteudo b")
    (tmp_path / "nao_e_pdf.txt").write_text("ignorar", encoding="utf-8")

    resultado = listar_pdfs(tmp_path)

    nomes = sorted(p.name for p in resultado)
    assert nomes == ["a.pdf", "b.pdf"]


def test_salvar_texto_grava_arquivo_txt(tmp_path):
    pdf = tmp_path / "nota.pdf"
    _criar_pdf_com_texto(pdf, "NOTA FISCAL 999")
    resultado = processar_pdf_completo(pdf)
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


def test_processar_lote_isola_pdf_protegido_por_senha(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_texto(entrada / "a_boa.pdf", "nota valida a com texto suficiente para passar")
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "conteudo protegido", fontsize=12)
    doc.save(
        str(entrada / "b_protegida.pdf"),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="dono",
        user_pw="usuario",
        permissions=0,
    )
    doc.close()
    _criar_pdf_com_texto(entrada / "c_boa.pdf", "nota valida c com texto suficiente para passar")
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    assert resumo["processados"] == 2
    assert resumo["erros"] == 1
    status_por_arquivo = {d["arquivo"]: d["status"] for d in resumo["detalhes"]}
    assert status_por_arquivo["a_boa.pdf"] == "OK"
    assert status_por_arquivo["b_protegida.pdf"] == "ERRO"
    assert status_por_arquivo["c_boa.pdf"] == "OK"


def test_processar_lote_pdf_escaneado_reporta_nao_nativo(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.draw_rect(fitz.Rect(50, 50, 200, 200))  # conteudo grafico, sem texto
    doc.save(str(entrada / "escaneada.pdf"))
    doc.close()
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    assert resumo["processados"] == 1
    assert resumo["detalhes"][0]["possui_texto_nativo"] is False


def test_processar_lote_pdf_escaneado_com_texto_real_usa_ocr(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_imagem_de_texto(entrada / "nf_scan.pdf", "FORNECEDOR TESTE OCR")
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    assert resumo["processados"] == 1
    assert resumo["detalhes"][0]["possui_texto_nativo"] is False
    texto_gerado = (pasta_saida / "nf_scan.txt").read_text(encoding="utf-8")
    assert "FORNECEDOR" in texto_gerado.upper()


def test_main_retorna_zero_e_gera_arquivo(tmp_path):
    from src.cli.phase1_cli import main

    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_texto(entrada / "nota.pdf", "conteudo de teste com texto suficiente")
    pasta_saida = tmp_path / "saida"

    codigo = main([str(entrada), "--saida", str(pasta_saida)])

    assert codigo == 0
    assert (pasta_saida / "nota.txt").exists()


def test_main_caminho_inexistente_retorna_1(tmp_path):
    from src.cli.phase1_cli import main

    codigo = main([str(tmp_path / "nao_existe"), "--saida", str(tmp_path / "saida")])

    assert codigo == 1
```

- [ ] **Step 3: Run the CLI tests**

Run: `.venv/Scripts/python -m pytest tests/cli/test_phase1_cli.py -v`
Expected: 9 passed. `test_processar_lote_pdf_escaneado_com_texto_real_usa_ocr` and `test_ocr_imagem_reconhece_texto_simples_e_grande` (Task 4) are the two tests genuinely exercising real Tesseract OCR end-to-end — if OCR misreads the exact synthetic text and either test is flaky, prefer strengthening the fixture (larger font, higher DPI, simpler text) over weakening the assertion to something that would also pass on garbage output.

- [ ] **Step 4: Run the full suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests pass — Fase 1 (5 reader + 9 cli, cli count now includes the 2 new Fase 2 CLI tests) + Fase 2 (4 render + 5 preprocess + 2 engine + 3 pipeline) = 28 total.

- [ ] **Step 5: Commit**

```bash
git add src/cli/phase1_cli.py tests/cli/test_phase1_cli.py
git commit -m "feat: wire CLI to the Fase 2 native-text+OCR pipeline"
```

---

### Task 7: Manual validation against real, genuinely-scanned NF PDFs

**Files:** none created — verification step per spec §37, same as Fase 1's Task 4.

**Interfaces:**
- Consumes: `main` from `src.cli.phase1_cli` (Task 6); the 6 real NF PDFs already used to validate Fase 1 (CAPUEIRA, MULT×2, HORTIFRUTI, TRILIX, ABELHA — already sitting in `entrada/` from Fase 1's validation, all previously confirmed `precisa_ocr`/scanned).

- [ ] **Step 1: Re-run the CLI against the same real PDFs already in `entrada/`**

Run: `.venv/Scripts/python -m src.cli.phase1_cli entrada --saida resultado/texto_ocr`

- [ ] **Step 2: Inspect the output**

For each of the 6 `.txt` files in `resultado/texto_ocr/`, confirm they are no longer empty (Fase 1 left them empty since it never ran OCR) and contain recognizable Portuguese words, numbers, or NF-typical terms (fornecedor names, "NOTA FISCAL", CNPJ-shaped digit groups, monetary values) — not garbage. Perfect transcription is not the bar; recognizable, mostly-correct text is.

- [ ] **Step 3: Report and fix**

If OCR output is unusably garbled across most files, first check whether the issue is preprocessing (try disabling `corrigir_inclinacao` or `binarizar` individually to isolate which step helps or hurts on real scans — real CamScanner output may behave differently than the synthetic test fixtures) or DPI (150 vs 300 vs 400) before concluding the approach needs to change. Only then is Fase 2 considered done (per spec §37).

---

## Next Phase

Fase 3 (Extração da NF) consumes `ResultadoExtracaoCompleto.texto_completo`/`texto_por_pagina` from this phase to parse structured fields (número da NF, CNPJ, itens, valores) via regex/rules — a separate plan, written after Fase 2 is validated.
