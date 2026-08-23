# src/ocr/preprocess.py
"""Pré-processamento de imagem para OCR (Fase 2).

Aplica só os passos de maior impacto para digitalizações de Nota Fiscal
(CamScanner): escala de cinza, correção de inclinação (deskew) e
binarização adaptativa. Cada função é pura e testável isoladamente com
imagens sintéticas — nenhuma depende do Tesseract.
"""

from __future__ import annotations

import cv2
import numpy as np


def para_cinza(imagem: np.ndarray) -> np.ndarray:
    if imagem.ndim == 2:
        return imagem
    return cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)


def corrigir_inclinacao(imagem_cinza: np.ndarray) -> np.ndarray:
    """Corrige pequenas rotações (inclinação de digitalização) usando o
    ângulo do retângulo mínimo que envolve os pixels escuros (texto)."""
    invertida = cv2.bitwise_not(imagem_cinza)
    _, binaria = cv2.threshold(invertida, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(binaria > 0))
    if coords.shape[0] < 10:
        return imagem_cinza  # pouco ou nenhum conteúdo — nada a corrigir

    angulo = cv2.minAreaRect(coords)[-1]
    if angulo < -45:
        angulo = -(90 + angulo)
    else:
        angulo = -angulo

    if abs(angulo) < 0.1:
        return imagem_cinza  # já está reto o suficiente

    altura, largura = imagem_cinza.shape[:2]
    centro = (largura // 2, altura // 2)
    matriz_rotacao = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    return cv2.warpAffine(
        imagem_cinza,
        matriz_rotacao,
        (largura, altura),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def binarizar(imagem_cinza: np.ndarray) -> np.ndarray:
    """Binarização adaptativa: lida melhor com sombras/iluminação desigual
    do que um limiar fixo — comum em fotos de celular/CamScanner."""
    return cv2.adaptiveThreshold(
        imagem_cinza,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )


def preprocessar(imagem: np.ndarray) -> np.ndarray:
    """Pipeline completo: cinza -> deskew -> binarização."""
    cinza = para_cinza(imagem)
    corrigida = corrigir_inclinacao(cinza)
    return binarizar(corrigida)
