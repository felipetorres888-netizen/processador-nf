# tests/cli/test_phase1_cli.py
from pathlib import Path

import pymupdf as fitz

from src.cli.phase1_cli import listar_pdfs, main, processar_lote, salvar_texto
from src.pdf.reader import processar_pdf


def _criar_pdf_com_texto(caminho: Path, texto: str) -> None:
    doc = fitz.open()
    pagina = doc.new_page()
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


def _criar_pdf_protegido_por_senha(caminho: Path, texto: str) -> None:
    """Cria um PDF que abre com sucesso via fitz.open() (sem levantar exceção),
    mas cujo conteúdo exige senha para ser lido — reproduzindo o bug de
    falha tardia (lazy failure) descrito na revisão: fitz.open() não levanta
    erro, só o acesso à página levanta.
    """
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), texto, fontsize=12)
    doc.save(
        str(caminho),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="dono",
        user_pw="usuario",
        permissions=0,
    )
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


def test_processar_lote_isola_pdf_protegido_por_senha(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_texto(entrada / "a_boa.pdf", "nota valida a com texto suficiente para passar")
    _criar_pdf_protegido_por_senha(
        entrada / "b_protegida.pdf", "conteudo protegido por senha que nao deve ser lido"
    )
    _criar_pdf_com_texto(entrada / "c_boa.pdf", "nota valida c com texto suficiente para passar")
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    assert resumo["processados"] == 2
    assert resumo["erros"] == 1
    detalhes_por_arquivo = {d["arquivo"]: d for d in resumo["detalhes"]}
    assert detalhes_por_arquivo["a_boa.pdf"]["status"] == "OK"
    assert detalhes_por_arquivo["b_protegida.pdf"]["status"] == "ERRO"
    # O arquivo listado alfabeticamente depois do protegido precisa ter sido
    # processado normalmente: o lote não pode abortar após a falha tardia.
    assert detalhes_por_arquivo["c_boa.pdf"]["status"] == "OK"


def test_processar_lote_pdf_escaneado_reporta_nao_nativo(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_sem_texto(entrada / "escaneada.pdf", num_paginas=1)
    _criar_pdf_com_texto(entrada / "nativa.pdf", "nota valida com texto suficiente para passar")
    pasta_saida = tmp_path / "saida"

    resumo = processar_lote(entrada, pasta_saida)

    detalhes_por_arquivo = {d["arquivo"]: d for d in resumo["detalhes"]}
    assert detalhes_por_arquivo["escaneada.pdf"]["status"] == "OK"
    assert detalhes_por_arquivo["escaneada.pdf"]["possui_texto_nativo"] is False
    assert detalhes_por_arquivo["nativa.pdf"]["status"] == "OK"
    assert detalhes_por_arquivo["nativa.pdf"]["possui_texto_nativo"] is True


def test_main_retorna_zero_e_gera_arquivo(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    _criar_pdf_com_texto(entrada / "nota.pdf", "nota valida com texto suficiente para passar")
    pasta_saida = tmp_path / "saida"

    codigo = main([str(entrada), "--saida", str(pasta_saida)])

    assert codigo == 0
    assert (pasta_saida / "nota.txt").exists()


def test_main_caminho_inexistente_retorna_1(tmp_path):
    codigo = main([str(tmp_path / "nao_existe"), "--saida", str(tmp_path / "saida")])

    assert codigo == 1
