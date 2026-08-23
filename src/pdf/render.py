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
