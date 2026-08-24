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


def test_processar_pdf_completo_pdf_misto_mantem_ordem_e_origem_por_pagina(tmp_path):
    """PDF de 3 páginas: nativa, escaneada (imagem), nativa de novo — garante
    que processar_pdf_completo não embaralha o alinhamento de índices entre
    resultado_base.texto_por_pagina e o doc reaberto para OCR, e que cada
    página é classificada corretamente (não só a primeira/única página, como
    em todos os outros testes deste arquivo)."""
    from PIL import Image, ImageDraw

    caminho = tmp_path / "mista.pdf"
    texto_pagina_0 = "NOTA FISCAL 111 - PRIMEIRA PAGINA NATIVA"
    texto_pagina_1 = "FORNECEDOR ESCANEADO PAGINA DO MEIO"
    texto_pagina_2 = "BOLETO 999 - TERCEIRA PAGINA NATIVA"

    doc = fitz.open()

    pagina_0 = doc.new_page(width=595, height=842)
    pagina_0.insert_text((72, 72), texto_pagina_0, fontsize=12)

    pagina_1 = doc.new_page(width=595, height=842)
    tela = Image.new("RGB", (900, 300), color="white")
    desenho = ImageDraw.Draw(tela)
    desenho.text((30, 100), texto_pagina_1, fill="black")
    caminho_png = tmp_path / "pagina_1.png"
    tela.save(caminho_png)
    pagina_1.insert_image(fitz.Rect(50, 50, 545, 250), filename=str(caminho_png))

    pagina_2 = doc.new_page(width=595, height=842)
    pagina_2.insert_text((72, 72), texto_pagina_2, fontsize=12)

    doc.save(str(caminho))
    doc.close()
    caminho_png.unlink()

    resultado = processar_pdf_completo(caminho)

    assert resultado.origem_por_pagina == ["texto_nativo", "ocr", "texto_nativo"]
    assert texto_pagina_0 in resultado.texto_por_pagina[0]
    assert "FORNECEDOR" in resultado.texto_por_pagina[1].upper()
    assert "ESCANEADO" in resultado.texto_por_pagina[1].upper()
    assert texto_pagina_2 in resultado.texto_por_pagina[2]
