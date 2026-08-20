# tests/cli/test_phase1_cli.py
from pathlib import Path

import fitz

from src.cli.phase1_cli import listar_pdfs, processar_lote, salvar_texto
from src.pdf.reader import processar_pdf


def _criar_pdf_com_texto(caminho: Path, texto: str) -> None:
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), texto, fontsize=12)
    doc.save(str(caminho))
    doc.close()


def test_listar_pdfs_arquivo_unico(tmp_path):
    pdf = tmp_path / "nota.pdf"
    _criar_pdf_com_texto(pdf, "conteudo")

    resultado = listar_pdfs(pdf)

    assert resultado == [pdf]


def test_listar_pdfs_pasta_com_varios_arquivos(tmp_path):
    _criar_pdf_com_texto(tmp_path / "a.pdf", "conteudo a")
    _criar_pdf_com_texto(tmp_path / "b.pdf", "conteudo b")
    (tmp_path / "nao_e_pdf.txt").write_text("ignorar")

    resultado = listar_pdfs(tmp_path)

    nomes = sorted(p.name for p in resultado)
    assert nomes == ["a.pdf", "b.pdf"]


def test_salvar_texto_grava_arquivo_txt(tmp_path):
    pdf = tmp_path / "nota.pdf"
    _criar_pdf_com_texto(pdf, "NOTA FISCAL 999")
    resultado = processar_pdf(pdf)
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
