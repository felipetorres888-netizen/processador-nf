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
