"""Leitura de PDF e extração de texto nativo (Fase 1).

Não faz OCR. Apenas abre o PDF, extrai o texto embutido de cada página e
decide, por uma heurística de contagem de caracteres, se esse texto nativo
é suficiente para uso ou se a página precisará de OCR em uma fase futura.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz


class PDFInvalidoError(Exception):
    """Levantado quando o caminho não existe ou não é um PDF legível."""


@dataclass
class ResultadoExtracao:
    arquivo: Path
    num_paginas: int
    texto_por_pagina: list[str]
    paginas_com_texto_suficiente: list[bool]
    texto_completo: str
    possui_texto_nativo: bool
    caracteres_totais: int


def _abrir_pdf(caminho: Path) -> fitz.Document:
    if not caminho.exists():
        raise PDFInvalidoError(f"Arquivo não encontrado: {caminho}")
    try:
        doc = fitz.open(str(caminho))
    except Exception as exc:  # fitz levanta várias exceções internas para PDF inválido
        raise PDFInvalidoError(f"Não foi possível abrir o PDF: {caminho} ({exc})") from exc

    if doc.needs_pass:
        doc.close()
        raise PDFInvalidoError(f"PDF protegido por senha: {caminho}")

    return doc


def _extrair_texto_por_pagina(doc: fitz.Document) -> list[str]:
    return [pagina.get_text("text") for pagina in doc]


def _paginas_com_texto_suficiente(texto_por_pagina: list[str], min_chars_por_pagina: int) -> list[bool]:
    return [len(t.strip()) >= min_chars_por_pagina for t in texto_por_pagina]


def processar_pdf(caminho: Path, min_chars_por_pagina: int = 30) -> ResultadoExtracao:
    try:
        doc = _abrir_pdf(caminho)
        try:
            texto_por_pagina = _extrair_texto_por_pagina(doc)
            num_paginas = doc.page_count
        finally:
            doc.close()
    except PDFInvalidoError:
        raise
    except Exception as exc:
        raise PDFInvalidoError(f"Falha ao processar o PDF: {caminho} ({exc})") from exc

    texto_completo = "\n\n".join(texto_por_pagina)
    caracteres_totais = sum(len(t.strip()) for t in texto_por_pagina)
    paginas_com_texto = _paginas_com_texto_suficiente(texto_por_pagina, min_chars_por_pagina)
    possui_texto_nativo = all(paginas_com_texto) if paginas_com_texto else False

    return ResultadoExtracao(
        arquivo=caminho,
        num_paginas=num_paginas,
        texto_por_pagina=texto_por_pagina,
        paginas_com_texto_suficiente=paginas_com_texto,
        texto_completo=texto_completo,
        possui_texto_nativo=possui_texto_nativo,
        caracteres_totais=caracteres_totais,
    )
