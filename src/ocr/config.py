"""Configuração do motor de OCR (Fase 2).

O Tesseract não está no PATH deste ambiente Windows, e o pacote de idioma
português foi baixado para uma pasta local do projeto (fora de Program
Files, que exige permissão de administrador para escrita). Este módulo
centraliza os três valores que a Fase 2 precisa para encontrar o Tesseract
e seus dados de idioma — cada um substituível por variável de ambiente
para que o projeto funcione em outra máquina com instalação diferente.
"""

from __future__ import annotations

import os
from pathlib import Path

TESSERACT_CMD = os.environ.get(
    "PROCESSADOR_NF_TESSERACT_CMD",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)

TESSDATA_DIR = os.environ.get(
    "PROCESSADOR_NF_TESSDATA_DIR",
    str(Path(__file__).resolve().parent.parent.parent / "tessdata"),
)

OCR_LANG = os.environ.get("PROCESSADOR_NF_OCR_LANG", "por")
