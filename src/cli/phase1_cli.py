# src/cli/phase1_cli.py
"""CLI de lote: PDF(s) -> texto (nativo ou OCR) -> salvar -> mostrar resultado.

Nunca move ou apaga o PDF original. Um arquivo com erro não interrompe o
lote. Usa o pipeline completo da Fase 2 (src.pdf.pipeline): tenta texto
nativo primeiro, só recorre a OCR local nas páginas que precisarem.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.pdf.pipeline import ResultadoExtracaoCompleto, processar_pdf_completo


def listar_pdfs(entrada: Path) -> list[Path]:
    if entrada.is_file():
        return [entrada]
    return sorted(p for p in entrada.glob("*.pdf") if p.is_file())


def salvar_texto(resultado: ResultadoExtracaoCompleto, pasta_saida: Path) -> Path:
    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho_txt = pasta_saida / f"{resultado.arquivo.stem}.txt"
    caminho_txt.write_text(resultado.texto_completo, encoding="utf-8")
    return caminho_txt


def processar_lote(entrada: Path, pasta_saida: Path) -> dict:
    detalhes: list[dict] = []
    processados = 0
    erros = 0

    for pdf in listar_pdfs(entrada):
        try:
            resultado = processar_pdf_completo(pdf)
            salvar_texto(resultado, pasta_saida)
            processados += 1
            possui_texto_nativo = all(
                origem == "texto_nativo" for origem in resultado.origem_por_pagina
            )
            detalhes.append(
                {
                    "arquivo": pdf.name,
                    "status": "OK",
                    "num_paginas": resultado.num_paginas,
                    "possui_texto_nativo": possui_texto_nativo,
                    "erro": None,
                }
            )
        except Exception as exc:
            erros += 1
            detalhes.append(
                {
                    "arquivo": pdf.name,
                    "status": "ERRO",
                    "num_paginas": None,
                    "possui_texto_nativo": None,
                    "erro": str(exc),
                }
            )

    return {"processados": processados, "erros": erros, "detalhes": detalhes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Processador NF - PDF -> texto (nativo ou OCR)")
    parser.add_argument("entrada", type=Path, help="Arquivo PDF ou pasta com PDFs")
    parser.add_argument(
        "--saida", type=Path, default=Path("resultado/texto_ocr"), help="Pasta de saída dos .txt"
    )
    args = parser.parse_args(argv)

    if not args.entrada.exists():
        print(f"Caminho de entrada não encontrado: {args.entrada}", file=sys.stderr)
        return 1

    resumo = processar_lote(args.entrada, args.saida)

    print(f"Processados: {resumo['processados']}")
    print(f"Erros: {resumo['erros']}")
    for d in resumo["detalhes"]:
        if d["status"] == "OK":
            origem = "texto_nativo" if d["possui_texto_nativo"] else "ocr_aplicado"
            print(f"  OK    {d['arquivo']:40s} paginas={d['num_paginas']:<3} origem={origem}")
        else:
            print(f"  ERRO  {d['arquivo']:40s} {d['erro']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
