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
