# tests/ocr/test_preprocess.py
import numpy as np
from PIL import Image, ImageDraw

from src.ocr.preprocess import binarizar, corrigir_inclinacao, para_cinza


def _linha_de_texto_inclinada(angulo_graus: float) -> np.ndarray:
    """Cria uma imagem branca com um retângulo preto simulando uma linha de
    texto, rotacionada por um ângulo conhecido — como uma digitalização
    torta do CamScanner."""
    tela = Image.new("L", (600, 400), color=255)
    desenho = ImageDraw.Draw(tela)
    desenho.rectangle([100, 190, 500, 210], fill=0)
    tela = tela.rotate(angulo_graus, fillcolor=255, expand=False)
    return np.array(tela)


def _variacao_horizontal_por_linha(imagem_cinza: np.ndarray) -> float:
    """Mede o quão 'torta' a imagem está: para cada linha com pixel escuro,
    pega a posição x mais à esquerda; retorna o desvio padrão dessas
    posições entre as linhas. Uma imagem bem alinhada tem desvio baixo."""
    posicoes = []
    for linha in imagem_cinza:
        indices_escuros = np.where(linha < 128)[0]
        if indices_escuros.size > 0:
            posicoes.append(indices_escuros[0])
    return float(np.std(posicoes)) if len(posicoes) > 1 else 0.0


def test_para_cinza_reduz_para_um_canal():
    imagem_colorida = np.zeros((50, 50, 3), dtype=np.uint8)

    resultado = para_cinza(imagem_colorida)

    assert resultado.ndim == 2
    assert resultado.shape == (50, 50)


def test_para_cinza_imagem_ja_cinza_retorna_inalterada():
    imagem_cinza = np.full((30, 30), 128, dtype=np.uint8)

    resultado = para_cinza(imagem_cinza)

    assert resultado.shape == (30, 30)
    assert np.array_equal(resultado, imagem_cinza)


def test_corrigir_inclinacao_reduz_variacao_horizontal():
    inclinada = _linha_de_texto_inclinada(8.0)
    variacao_antes = _variacao_horizontal_por_linha(inclinada)

    corrigida = corrigir_inclinacao(inclinada)
    variacao_depois = _variacao_horizontal_por_linha(corrigida)

    assert variacao_depois < variacao_antes * 0.5


def test_corrigir_inclinacao_imagem_ja_reta_fica_praticamente_igual():
    reta = _linha_de_texto_inclinada(0.0)

    corrigida = corrigir_inclinacao(reta)

    assert _variacao_horizontal_por_linha(corrigida) < 3.0


def test_binarizar_produz_apenas_dois_valores():
    imagem_cinza = np.random.randint(0, 255, (100, 100), dtype=np.uint8).astype(np.uint8)

    resultado = binarizar(imagem_cinza)

    valores_unicos = set(np.unique(resultado).tolist())
    assert valores_unicos.issubset({0, 255})
