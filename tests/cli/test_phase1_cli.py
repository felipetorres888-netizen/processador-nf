# tests/cli/test_phase1_cli.py
from pathlib import Path

import pymupdf as fitz

from src.cli.phase1_cli import listar_pdfs, processar_lote, salvar_texto
from src.pdf.pipeline import processar_pdf_completo


def _criar_pdf_com_texto(caminho: Path, texto: str) -> None:
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), texto, fontsize=12)
    doc.save(str(caminho))
    doc.close()


def _criar_pdf_com_imagem_de_texto(caminho: Path, texto: str) -> None:
    """Simula uma NF escaneada de verdade: o texto vira imagem, não texto
    nativo pesquisável."""
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


def test_listar_pdfs_arquivo_unico(tmp_path):
    pdf = tmp_path / "nota.pdf"
    _criar_pdf_com_texto(pdf, "conteudo")

    resultado = listar_pdfs(pdf)

    assert resultado == [pdf]


def test_listar_pdfs_pasta_com_varios_arquivos(tmp_path):
    _criar_pdf_com_texto(tmp_path / "a.pdf", "conteudo a")
    _criar_pdf_com_texto(tmp_path / "b.pdf", "conteudo b")
    (tmp_path / "nao_e_pdf.txt").write_text("ignorar", encoding="utf-8")

    resultado = listar_pdfs(tmp_path)

    nomes = sorted(p.name for p in resultado)
    assert nomes == ["a.pdf", "b.pdf"]


def test_salvar_texto_grava_arquivo_txt(tmp_path):
    pdf = tmp_path / "nota.pdf"
    _criar_pdf_com_texto(pdf, "NOTA FISCAL 999")
    resultado = processar_pdf_completo(pdf)
    pasta_saida = tmp_path / "saida"

    caminho_txt = salvar_texto(resultado, pasta_saida)

    assert caminho_txt.exists()
    assert caminho_txt.name == "nota.txt"
    assert "NOTA FISCAL 999" in caminho_txt.read_text(encoding="utf-8")


def test_processar_lote_continua_apos_erro(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_texto(entrada / "boa.pdf", "nota valida com texto suficiente para passar")
    (entrada / "invalida.pdf").write_bytes(b"nao e um pdf valido")
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    assert resumo["processados"] == 1
    assert resumo["erros"] == 1
    assert len(resumo["detalhes"]) == 2
    status_por_arquivo = {d["arquivo"]: d["status"] for d in resumo["detalhes"]}
    assert status_por_arquivo["boa.pdf"] == "OK"
    assert status_por_arquivo["invalida.pdf"] == "ERRO"
    assert (pasta_saida / "boa.txt").exists()
    assert not (pasta_saida / "invalida.txt").exists()


def test_processar_lote_isola_pdf_protegido_por_senha(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_texto(entrada / "a_boa.pdf", "nota valida a com texto suficiente para passar")
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "conteudo protegido", fontsize=12)
    doc.save(
        str(entrada / "b_protegida.pdf"),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="dono",
        user_pw="usuario",
        permissions=0,
    )
    doc.close()
    _criar_pdf_com_texto(entrada / "c_boa.pdf", "nota valida c com texto suficiente para passar")
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    assert resumo["processados"] == 2
    assert resumo["erros"] == 1
    status_por_arquivo = {d["arquivo"]: d["status"] for d in resumo["detalhes"]}
    assert status_por_arquivo["a_boa.pdf"] == "OK"
    assert status_por_arquivo["b_protegida.pdf"] == "ERRO"
    assert status_por_arquivo["c_boa.pdf"] == "OK"


def test_processar_lote_pdf_escaneado_reporta_nao_nativo(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.draw_rect(fitz.Rect(50, 50, 200, 200))  # conteudo grafico, sem texto
    doc.save(str(entrada / "escaneada.pdf"))
    doc.close()
    _criar_pdf_com_texto(entrada / "nativa.pdf", "nota valida com texto suficiente para passar")
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    assert resumo["processados"] == 2
    detalhes_por_arquivo = {d["arquivo"]: d for d in resumo["detalhes"]}
    assert detalhes_por_arquivo["escaneada.pdf"]["possui_texto_nativo"] is False
    assert detalhes_por_arquivo["nativa.pdf"]["possui_texto_nativo"] is True


def test_processar_lote_pdf_escaneado_com_texto_real_usa_ocr(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_imagem_de_texto(entrada / "nf_scan.pdf", "FORNECEDOR TESTE OCR")
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    assert resumo["processados"] == 1
    assert resumo["detalhes"][0]["possui_texto_nativo"] is False
    texto_gerado = (pasta_saida / "nf_scan.txt").read_text(encoding="utf-8")
    assert "FORNECEDOR" in texto_gerado.upper()


def test_main_retorna_zero_e_gera_arquivo(tmp_path):
    from src.cli.phase1_cli import main

    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_texto(entrada / "nota.pdf", "conteudo de teste com texto suficiente")
    pasta_saida = tmp_path / "saida"

    codigo = main([str(entrada), "--saida", str(pasta_saida)])

    assert codigo == 0
    assert (pasta_saida / "nota.txt").exists()


def test_main_caminho_inexistente_retorna_1(tmp_path):
    from src.cli.phase1_cli import main

    codigo = main([str(tmp_path / "nao_existe"), "--saida", str(tmp_path / "saida")])

    assert codigo == 1
