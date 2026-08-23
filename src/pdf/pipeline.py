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
