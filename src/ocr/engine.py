"""Wrapper do Tesseract via pytesseract (Fase 2).

Centraliza a configuração (binário do Tesseract fora do PATH, dados de
idioma locais ao projeto — ver src/ocr/config.py) para que o resto do
código só precise chamar ocr_imagem(imagem) e receber texto de volta.
"""

from __future__ import annotations

import os

import numpy as np
import pytesseract

from src.ocr.config import OCR_LANG, TESSDATA_DIR, TESSERACT_CMD

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
# Não usamos o config-string `--tessdata-dir "<caminho>"` do pytesseract (a
# abordagem original do plano): no Windows, o tokenizador de config-string
# do próprio Tesseract lida mal com o caminho entre aspas contendo
# barras invertidas, quebrando a chamada (reproduzido e confirmado durante
# a revisão da Task 4). TESSDATA_PREFIX é o mecanismo padrão e documentado
# do Tesseract para isso e funciona corretamente em qualquer plataforma.
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR


def ocr_imagem(imagem: np.ndarray, lang: str = OCR_LANG) -> str:
    """Executa OCR em uma imagem já pré-processada (numpy array) e retorna
    o texto reconhecido."""
    texto = pytesseract.image_to_string(imagem, lang=lang)
    return texto.strip()
