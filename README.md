# Processador NF

Sistema local de processamento em lote de Notas Fiscais (PDF escaneado/nativo).
Local-first: nenhuma IA, nenhum upload externo nesta fase.

## Fase atual: Fase 2 — PDF → Texto Nativo + OCR Local

Extrai texto nativo de cada página do PDF (Fase 1); páginas sem texto nativo
suficiente (ex.: NF escaneada) caem automaticamente em OCR local via
Tesseract (Fase 2).

## Setup

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

### OCR (Tesseract)

O OCR local depende do binário do Tesseract, que **não** é instalado via
pip — é preciso instalá-lo separadamente:

- **Windows**: baixe e instale o Tesseract 5.x pelo instalador da
  UB-Mannheim: https://github.com/UB-Mannheim/tesseract/wiki
- **Linux/macOS**: instale o pacote `tesseract`/`tesseract-ocr` 5.x pelo
  gerenciador de pacotes do seu sistema (ex.: `apt install tesseract-ocr`,
  `brew install tesseract`).

Também é preciso do pacote de idioma português (`por.traineddata`). Baixe
em https://github.com/tesseract-ocr/tessdata e coloque o arquivo em uma
pasta `tessdata/` na raiz do projeto (`C:\...\ProcessadorNF\tessdata\por.traineddata`
neste ambiente), ou aponte `PROCESSADOR_NF_TESSDATA_DIR` para onde preferir
guardá-lo.

Três variáveis de ambiente permitem rodar o projeto em uma máquina com o
Tesseract instalado em outro lugar (os padrões abaixo são os deste
ambiente — ver `src/ocr/config.py`):

| Variável | O que substitui | Padrão |
|---|---|---|
| `PROCESSADOR_NF_TESSERACT_CMD` | Caminho do executável `tesseract` | `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| `PROCESSADOR_NF_TESSDATA_DIR` | Pasta com os arquivos `.traineddata` (idiomas) | pasta `tessdata/` na raiz do projeto |
| `PROCESSADOR_NF_OCR_LANG` | Código do idioma usado no OCR | `por` |

`tessdata/` é ignorada pelo git (é um asset binário de ~15MB) — cada
clone do repositório precisa colocar `por.traineddata` lá (ou apontar
`PROCESSADOR_NF_TESSDATA_DIR` para uma pasta que já o tenha) antes de rodar
o OCR.

## Uso

    python -m src.cli.phase1_cli entrada/ --saida resultado/texto_ocr

## Testes

    pytest
