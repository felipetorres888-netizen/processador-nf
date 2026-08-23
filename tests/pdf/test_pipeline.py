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
