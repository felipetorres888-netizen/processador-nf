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
