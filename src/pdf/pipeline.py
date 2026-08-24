# src/pdf/pipeline.py
"""Pipeline completo de extração de uma NF (Fase 2): texto nativo primeiro,
OCR local só nas páginas que precisarem (§3 do mega prompt).

Reaproveita processar_pdf da Fase 1 (que já garante que só PDFInvalidoError
escapa, e já decide por página se o texto nativo é suficiente) e só
adiciona OCR por cima.

Contrato de exceções: assim como processar_pdf, processar_pdf_completo
nunca deixa escapar nada além de PDFInvalidoError (arquivo inexistente,
corrompido, protegido por senha, ou a reabertura do PDF para renderizar
páginas para OCR falhando). Uma falha de OCR em UMA página (ex.: Tesseract
mal configurado, imagem renderizada corrompida, problema no pacote de
idioma) NÃO propaga e NÃO derruba o arquivo inteiro: ela é isolada por
página, o texto nativo já extraído para as OUTRAS páginas do mesmo arquivo
é preservado, e a página que falhou fica marcada com
origem_por_pagina[i] == "ocr_falhou" (mantendo texto_por_pagina[i] como o
que a extração nativa da Fase 1 já tinha produzido, tipicamente vazio ou
insuficiente) em vez de levantar uma exceção.
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
    origem_por_pagina: list[str]  # "texto_nativo", "ocr" ou "ocr_falhou"


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
                try:
                    pagina = doc[indice]
                    imagem = renderizar_pagina(pagina, dpi=dpi)
                    imagem_preparada = preprocessar(imagem)
                    texto_final[indice] = ocr_imagem(imagem_preparada)
                except Exception:
                    # OCR falhou só nesta página (ex.: Tesseract mal
                    # configurado, imagem corrompida, problema no pacote de
                    # idioma). Não deixamos a exceção escapar: mantemos o
                    # texto nativo já extraído (mesmo que insuficiente) e
                    # marcamos a origem, para não perder o arquivo inteiro
                    # nem confundir esta página com uma que nunca precisou
                    # de OCR ou com uma onde o OCR teve sucesso.
                    origem_por_pagina[indice] = "ocr_falhou"
        finally:
            doc.close()

    return ResultadoExtracaoCompleto(
        arquivo=resultado_base.arquivo,
        num_paginas=resultado_base.num_paginas,
        texto_por_pagina=texto_final,
        texto_completo="\n\n".join(texto_final),
        origem_por_pagina=origem_por_pagina,
    )
