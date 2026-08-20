"""CLI de lote da Fase 1: PDF(s) -> detectar texto -> extrair -> salvar -> mostrar resultado.

Nunca move ou apaga o PDF original. Um arquivo com erro não interrompe o lote.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.pdf.reader import PDFInvalidoError, ResultadoExtracao, processar_pdf


def listar_pdfs(entrada: Path) -> list[Path]:
    if entrada.is_file():
        return [entrada]
    return sorted(p for p in entrada.glob("*.pdf") if p.is_file())


def salvar_texto(resultado: ResultadoExtracao, pasta_saida: Path) -> Path:
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
            resultado = processar_pdf(pdf)
            salvar_texto(resultado, pasta_saida)
            processados += 1
            detalhes.append(
                {
                    "arquivo": pdf.name,
                    "status": "OK",
                    "num_paginas": resultado.num_paginas,
                    "possui_texto_nativo": resultado.possui_texto_nativo,
                    "erro": None,
                }
            )
        except PDFInvalidoError as exc:
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
    parser = argparse.ArgumentParser(description="Processador NF - Fase 1 (PDF -> texto nativo)")
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
            origem = "texto_nativo" if d["possui_texto_nativo"] else "precisa_ocr"
            print(f"  OK    {d['arquivo']:40s} paginas={d['num_paginas']:<3} origem={origem}")
        else:
            print(f"  ERRO  {d['arquivo']:40s} {d['erro']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
