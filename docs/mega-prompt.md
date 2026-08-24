# MEGA PROMPT — SISTEMA LOCAL DE PROCESSAMENTO DE NOTAS FISCAIS

## 1. PAPEL

Você é o engenheiro de software responsável por desenvolver um aplicativo Windows para processamento em lote de Notas Fiscais de produtos recebidas principalmente como PDFs escaneados pelo CamScanner.

O objetivo principal do projeto é:

> **Extrair o máximo possível das informações das Notas Fiscais localmente, sem utilizar modelos de IA durante o processamento normal, e enviar para IA somente os dados que realmente exigirem interpretação.**

O sistema deve ser projetado desde o início para:

- reduzir drasticamente o consumo de tokens;
- processar muitas notas fiscais em lote;
- funcionar localmente no Windows;
- preservar os documentos originais;
- gerar dados estruturados;
- identificar problemas de OCR;
- identificar campos com baixa confiança;
- permitir revisão humana;
- preparar os dados para uma etapa posterior de análise por IA;
- ser modular e facilmente evolutivo.

---

# 2. CONTEXTO DO PROJETO

As Notas Fiscais serão fotografadas ou digitalizadas pelo CamScanner e disponibilizadas principalmente como PDF.

Os PDFs podem apresentar:

- texto nativo;
- documentos totalmente escaneados;
- imagens;
- várias páginas;
- diferentes fornecedores;
- diferentes layouts de DANFE;
- tabelas;
- baixa qualidade de imagem;
- rotação;
- inclinação;
- sombras;
- baixa resolução;
- números parcialmente ilegíveis;
- cabeçalhos e rodapés;
- informações repetidas em várias páginas.

O sistema NÃO deve assumir que todas as NFs possuem o mesmo layout.

O sistema deve ser resiliente a diferentes modelos de DANFE.

---

# 3. REGRA FUNDAMENTAL DE ARQUITETURA

NÃO utilizar uma API de IA para simplesmente transformar cada PDF em texto.

NÃO enviar o PDF inteiro para um modelo de linguagem por padrão.

NÃO transformar todas as páginas dos PDFs em imagens e mandar todas para uma IA.

O sistema deve seguir esta hierarquia:

```text
PDF
 ↓
Verificação do documento
 ↓
Tentativa de extração de texto nativo
 ↓
Se necessário → OCR LOCAL
 ↓
Pré-processamento da imagem
 ↓
Extração do conteúdo
 ↓
Parser de Nota Fiscal
 ↓
Validação por regras
 ↓
Cálculos e normalizações determinísticas
 ↓
Classificação de confiança
 ↓
Somente casos problemáticos → IA
 ↓
JSON estruturado
 ↓
Markdown opcional
 ↓
Banco de dados / planilha / análise
```

A IA deve ser tratada como uma **camada de exceção e interpretação**, e não como mecanismo principal de OCR.

---

# 4. OBJETIVO DE CUSTO

O sistema deverá ser otimizado para minimizar tokens.

Considere como prioridade:

### Nível 1 — processamento 100% local

Sempre que possível, resolver localmente:

- leitura do PDF;
- extração de texto;
- OCR;
- identificação de páginas;
- identificação de padrões;
- identificação do número da NF;
- CNPJ;
- data;
- valores;
- quantidades;
- unidades;
- NCM;
- CFOP;
- código do produto;
- descrição;
- cálculo de totais;
- validação matemática;
- identificação de duplicidades;
- classificação de confiança.

### Nível 2 — processamento por regras

Antes de chamar qualquer IA, usar:

- regex;
- expressões regulares;
- padrões conhecidos;
- validações matemáticas;
- tabelas de unidades;
- dicionários;
- heurísticas;
- regras de posição;
- regras por fornecedor;
- padrões recorrentes.

### Nível 3 — IA

Somente chamar IA quando:

- um item não puder ser interpretado;
- a descrição estiver ambígua;
- OCR produzir texto inconsistente;
- duas interpretações forem possíveis;
- houver baixa confiança;
- o layout do fornecedor for novo;
- houver necessidade de normalização sem regra determinística;
- houver informação conflitante.

Quando IA for usada, enviar somente o **menor contexto necessário**.

Nunca enviar o PDF inteiro se bastar enviar:

- uma linha;
- um item;
- um bloco da tabela;
- uma página específica;
- um campo específico.

---

# 5. PRIMEIRA ETAPA: INSPEÇÃO DO AMBIENTE

Antes de escrever a implementação definitiva:

1. Inspecione o ambiente Windows disponível.
2. Verifique versão do Python.
3. Verifique ferramentas instaladas.
4. Verifique disponibilidade de OCR.
5. Verifique bibliotecas disponíveis.
6. Identifique eventuais dependências externas.
7. Escolha ferramentas maduras e compatíveis com Windows.
8. Documente as decisões técnicas.

Não assuma que determinada biblioteca está instalada.

Não use dependências desnecessárias.

Priorize soluções open source/local-first.

---

# 6. STACK TECNOLÓGICA

Use Python como linguagem principal.

Avalie, conforme a necessidade:

- PyMuPDF para manipulação e leitura de PDF;
- bibliotecas de OCR locais;
- OpenCV para tratamento das imagens;
- Pillow para processamento de imagem;
- bibliotecas de parsing;
- SQLite para persistência local;
- Pydantic para modelos de dados e validação;
- PyInstaller para geração do executável Windows;
- Tkinter ou outra biblioteca GUI leve e estável para a interface.

A seleção final de cada biblioteca deve considerar:

- estabilidade;
- desempenho;
- facilidade de instalação no Windows;
- licença;
- manutenção;
- tamanho do aplicativo;
- funcionamento offline;
- facilidade de distribuição;
- possibilidade de processamento em lote.

Evite frameworks pesados sem necessidade.

---

# 7. OCR LOCAL

O OCR deve funcionar localmente por padrão.

O sistema deve:

1. verificar se o PDF possui texto nativo;
2. se possuir texto suficiente, evitar OCR;
3. se não possuir texto suficiente, renderizar páginas;
4. aplicar pré-processamento;
5. realizar OCR;
6. reconstruir o texto;
7. preservar a associação entre texto e página.

O pré-processamento deve considerar:

- grayscale;
- aumento de contraste;
- threshold;
- redução de ruído;
- correção de rotação;
- deskew;
- aumento de resolução;
- recorte de áreas;
- orientação do documento.

Não aplicar todos os filtros indiscriminadamente.

O pipeline deve testar e escolher a melhor estratégia quando possível.

---

# 8. PROCESSAMENTO EM LOTE

O aplicativo deverá permitir:

- selecionar um PDF;
- selecionar vários PDFs;
- selecionar uma pasta inteira;
- arrastar arquivos para a interface;
- processar centenas de arquivos;
- continuar processamento caso um arquivo apresente erro;
- registrar erros;
- não interromper o lote inteiro por causa de uma NF.

Exemplo:

```text
100 PDFs
98 processados automaticamente
1 enviado para revisão
1 apresentou erro de leitura
```

O usuário deverá conseguir identificar quais foram os 100 resultados.

---

# 9. ESTRUTURA DE PASTAS

Criar uma estrutura organizada.

Exemplo:

```text
PROCESSADOR_NF/
│
├── entrada/
│
├── processados/
│
├── revisao/
│
├── erro/
│
├── resultado/
│
│   ├── json/
│   ├── markdown/
│   └── texto_ocr/
│
├── logs/
│
├── banco/
│
└── config/
```

O sistema não deve mover o PDF original sem autorização.

O arquivo original deve permanecer preservado.

---

# 10. IDENTIFICAÇÃO DA NOTA FISCAL

Extrair, quando disponível:

- número da NF;
- série;
- chave de acesso;
- CNPJ emitente;
- razão social;
- nome fantasia;
- endereço;
- data de emissão;
- data de saída;
- município;
- UF;
- valor total;
- base de cálculo;
- impostos;
- observações.

A chave de acesso deve ser validada quando possível.

O número da NF deve ser tratado como identificador, mas nunca substituir a chave de acesso quando esta estiver disponível.

---

# 11. DADOS DOS ITENS

Para cada item, tentar extrair:

- código do produto;
- descrição original;
- NCM;
- CEST;
- CFOP;
- unidade;
- quantidade;
- valor unitário;
- valor total;
- desconto;
- outras despesas;
- informações adicionais;
- alíquotas relevantes quando disponíveis.

Estrutura desejada:

```json
{
  "codigo": "",
  "descricao_original": "",
  "ncm": "",
  "cfop": "",
  "unidade_original": "",
  "quantidade": 0,
  "valor_unitario": 0,
  "valor_total": 0,
  "desconto": 0,
  "confianca": 0
}
```

---

# 12. UNIDADES

O sistema deve preservar a unidade original da NF.

Exemplos:

```text
UN
UND
PÇ
PC
CX
KG
G
L
LT
ML
FD
DZ
PT
SC
```

Depois criar uma camada de normalização.

Exemplo:

```text
KG → KG
G → G
LT → L
L → L
ML → ML
UN → UN
UND → UN
PÇ → UN
PC → UN
```

NUNCA alterar a unidade original.

Guardar:

```json
{
  "unidade_original": "UND",
  "unidade_normalizada": "UN"
}
```

---

# 13. NORMALIZAÇÃO DE PRODUTOS

Não modificar a descrição original.

Manter:

```text
descricao_original
```

E criar:

```text
descricao_normalizada
```

Exemplo:

```text
"ACEM BOV KG"
```

pode virar:

```text
"ACÉM BOVINO"
```

Mas isso não deve ser feito somente por regra simplista.

A normalização deve ser uma etapa separada.

Inicialmente utilizar:

- dicionário;
- regras;
- tabelas de equivalência;
- fornecedores;
- padrões existentes.

A IA poderá ser utilizada posteriormente para casos ambíguos.

---

# 14. CLASSIFICAÇÃO DE CONFIANÇA

Cada campo importante deverá ter nível de confiança.

Exemplo:

```json
{
  "numero_nf": {
    "valor": "12345",
    "confianca": 0.99,
    "origem": "texto_nativo"
  }
}
```

Outro exemplo:

```json
{
  "descricao": {
    "valor": "ACEM BOVINO",
    "confianca": 0.72,
    "origem": "ocr"
  }
}
```

Categorias:

```text
HIGH
MEDIUM
LOW
```

ou uma escala numérica entre 0 e 1.

---

# 15. VALIDAÇÃO MATEMÁTICA

O sistema deve verificar automaticamente:

```text
quantidade × valor_unitário ≈ valor_total
```

Também validar:

```text
soma dos itens ≈ total dos produtos
```

e:

```text
total dos produtos
+ frete
+ seguro
+ outras despesas
- descontos
+ impostos aplicáveis
≈ total da NF
```

As regras devem tolerar pequenas diferenças de arredondamento.

Quando houver divergência relevante:

```text
status = "REVISAR"
```

---

# 16. DETECÇÃO DE DUPLICIDADE

O sistema deverá identificar possíveis NFs duplicadas.

Prioridade:

1. chave de acesso;
2. CNPJ + número + série;
3. combinação de data + fornecedor + número;
4. hash do arquivo como indicador adicional.

Não apagar duplicados automaticamente.

Classificar como:

```text
DUPLICADA
POSSIVEL_DUPLICADA
NOVA
```

---

# 17. RESULTADO JSON

Cada NF deverá gerar um JSON estruturado.

Exemplo:

```json
{
  "documento": {
    "arquivo_original": "NF_001.pdf",
    "status": "PROCESSADO",
    "confianca_geral": 0.96
  },
  "emitente": {
    "cnpj": "",
    "razao_social": "",
    "nome_fantasia": "",
    "uf": ""
  },
  "nota": {
    "numero": "",
    "serie": "",
    "chave_acesso": "",
    "data_emissao": "",
    "valor_total": 0
  },
  "itens": [],
  "validacao": {
    "total_confere": true,
    "divergencias": []
  },
  "processamento": {
    "metodo": "texto_nativo",
    "ocr_utilizado": false,
    "ia_utilizada": false
  }
}
```

Esse JSON será o formato estrutural principal do sistema.

---

# 18. MARKDOWN

O sistema também deverá gerar um `.md` legível por humanos e por ferramentas de IA.

Exemplo:

```markdown
# Nota Fiscal 12345

## Emitente

- Razão social: Fornecedor XYZ
- CNPJ: 00.000.000/0001-00
- UF: DF

## Nota

- Número: 12345
- Série: 1
- Data: 20/08/2026
- Chave de acesso: XXXXX

## Itens

| Código | Descrição | Qtd | Unid. | Vlr. Unit. | Total |
|---|---|---:|---|---:|---:|
| 001 | ACÉM BOVINO | 25 | KG | 31,90 | 797,50 |

## Validação

- Total dos itens: R$ 797,50
- Total da NF: R$ 797,50
- Conferência: OK

## Processamento

- OCR: não utilizado
- IA: não utilizada
- Confiança: 0,97
```

---

# 19. REGRA DE USO DE IA

Criar a arquitetura para IA opcional.

Nunca colocar uma API de IA como dependência obrigatória para o funcionamento básico.

Criar uma camada:

```text
AIService
```

Ela deve permitir no futuro utilizar diferentes provedores.

Por exemplo:

```text
OpenAI
Anthropic
outro provedor
modelo local
```

Mas o sistema básico deverá funcionar sem essa camada.

---

# 20. GATILHOS PARA IA

Antes de chamar IA, analisar:

```text
1. campo ausente?
2. OCR inconsistente?
3. confiança baixa?
4. múltiplas interpretações?
5. fornecedor desconhecido?
6. descrição impossível de normalizar?
7. divergência matemática?
```

Somente nesses casos avaliar chamada à IA.

Criar uma fila:

```text
AI_REVIEW_QUEUE
```

Exemplo:

```json
{
  "nf": "12345",
  "campo": "descricao_item",
  "problema": "OCR_AMBIGUO",
  "contexto_minimo": "ACEM BOVN KG",
  "pagina": 2
}
```

A IA deve receber apenas esse contexto mínimo.

---

# 21. CACHE DE IA

Implementar cache.

Se uma determinada informação já foi processada por IA, não processá-la novamente sem necessidade.

Usar hash do contexto de entrada.

Exemplo:

```text
hash do texto
+
prompt
+
modelo
```

Se o mesmo conteúdo aparecer novamente:

```text
usar resultado armazenado
```

Isso é fundamental para economia de tokens.

---

# 22. APRENDIZADO POR FORNECEDOR

Criar arquitetura para guardar padrões por fornecedor.

Exemplo:

```text
fornecedores/
    fornecedor_xyz/
        regras.json
        aliases.json
        layout.json
```

À medida que notas do mesmo fornecedor forem processadas, o sistema poderá aprender:

- posição dos campos;
- nomes usados;
- abreviações;
- unidades;
- descrições;
- padrões de item;
- formato dos códigos.

No futuro, a própria revisão humana poderá alimentar essas regras.

---

# 23. INTERFACE

Criar uma interface Windows simples e objetiva.

Tela principal:

```text
==========================================
     PROCESSADOR DE NOTAS FISCAIS
==========================================

[ Adicionar PDFs ]

[ Adicionar Pasta ]

Arquivos selecionados: 125

------------------------------------------

Processando:
NF_001.pdf

██████████████████░░░░ 82%

------------------------------------------

Processados: 98
Revisar: 5
Erros: 2
Duplicadas: 3

[ Abrir Resultados ]
[ Abrir Revisões ]
[ Abrir Logs ]
```

A interface deve mostrar progresso real.

---

# 24. LOGS

Registrar:

- início;
- fim;
- arquivo;
- tempo;
- OCR utilizado;
- método de extração;
- campos detectados;
- erros;
- avisos;
- chamadas de IA;
- tokens consumidos, quando disponível;
- custo estimado, quando disponível;
- status final.

Exemplo:

```text
NF_001.pdf
Método: texto_nativo
OCR: não
IA: não
Tempo: 0.82s
Status: OK
```

---

# 25. MÉTRICAS

O sistema deve gerar métricas do processamento.

Exemplo:

```text
Total de PDFs: 500

Processados automaticamente: 462
Revisão necessária: 31
Erros: 7

OCR utilizado: 380
Texto nativo: 120

IA utilizada: 31

Economia estimada:
469 PDFs processados sem IA
```

Essa métrica é importante porque um dos objetivos principais do projeto é reduzir custo de tokens.

---

# 26. MODO OFFLINE

O aplicativo deve funcionar totalmente offline para:

- leitura;
- OCR;
- parsing;
- validação;
- geração JSON;
- geração Markdown;
- armazenamento;
- logs.

Internet somente quando o usuário habilitar algum serviço de IA externo.

---

# 27. SEGURANÇA E PRIVACIDADE

Notas fiscais podem conter informações comerciais sensíveis.

Por padrão:

- não enviar arquivos para servidores externos;
- não fazer upload automático;
- não utilizar serviços externos sem autorização;
- não registrar conteúdo sensível desnecessariamente em logs;
- permitir desligar completamente IA externa.

A aplicação deve deixar claramente indicado quando um documento for enviado para uma API externa.

---

# 28. BANCO DE DADOS

Utilizar SQLite para armazenamento local.

Criar tabelas para, no mínimo:

```text
documents
suppliers
invoices
invoice_items
processing_runs
review_queue
ai_cache
supplier_rules
```

Criar índices adequados.

Não utilizar banco externo na primeira versão.

---

# 29. REVISÃO HUMANA

Criar uma tela para revisão.

Exemplo:

```text
NF: 12345
Fornecedor: XYZ

Campo:
Descrição

OCR:
"ACEM BOVN KG"

Sistema:
"ACÉM BOVINO"

Confiança:
58%

[ Corrigir ]
[ Aprovar ]
[ Enviar para IA ]
```

Se o usuário corrigir uma informação, registrar a correção.

Essa correção poderá futuramente alimentar as regras do fornecedor.

---

# 30. EXPORTAÇÃO

Criar possibilidade de exportar:

- JSON individual;
- Markdown individual;
- JSON consolidado;
- CSV;
- Excel.

O sistema deve gerar também, opcionalmente, um arquivo consolidado:

```text
todas_as_nfs.json
```

e:

```text
todos_os_itens.csv
```

---

# 31. ESTRUTURA DO PROJETO

Organize o código de maneira modular.

Exemplo:

```text
src/
│
├── app/
│   ├── gui/
│   ├── services/
│   └── controllers/
│
├── pdf/
├── ocr/
├── extraction/
├── parsing/
├── normalization/
├── validation/
├── ai/
├── database/
├── export/
├── rules/
├── logging/
└── config/
```

Não colocar toda a aplicação em um único arquivo Python.

---

# 32. CONFIGURAÇÃO

Criar arquivo de configuração.

Exemplo:

```yaml
ocr:
  enabled: true
  language: por

ai:
  enabled: false
  provider: ""

processing:
  batch_size: 10
  keep_originals: true

output:
  markdown: true
  json: true
  csv: true
```

Não colocar chaves de API diretamente no código.

---

# 33. TESTES

Criar testes automatizados.

Testar pelo menos:

- PDF com texto nativo;
- PDF escaneado;
- PDF de várias páginas;
- imagem rotacionada;
- PDF de baixa qualidade;
- NF com muitos itens;
- NF com poucos itens;
- unidade KG;
- unidade UN;
- unidade LT;
- divergência de total;
- PDF inválido;
- arquivo duplicado;
- fornecedor desconhecido;
- OCR ambíguo.

Criar uma pasta:

```text
tests/
fixtures/
```

---

# 34. TESTE DE DESEMPENHO

Criar teste com pelo menos 100 PDFs.

Medir:

- tempo médio;
- tempo total;
- memória;
- percentual de OCR;
- percentual processado automaticamente;
- percentual enviado para IA;
- quantidade de erros.

O sistema deve ser otimizado para processamento em lote.

---

# 35. SISTEMA DE PLUGINS / FUTURO

A arquitetura deve permitir posteriormente adicionar:

- leitura de XML de NF-e;
- integração com Excel;
- integração com Google Sheets;
- integração com banco de dados;
- integração com sistema de estoque;
- integração com API de IA;
- normalização de produtos;
- cálculo de custo;
- comparação de preços;
- histórico de fornecedor;
- análise de compras.

Não implementar tudo agora.

Mas criar interfaces que permitam essas expansões.

---

# 36. PRIORIDADE DO MVP

Não tentar construir tudo de uma vez.

Implementar nesta ordem:

### Fase 1
PDF → texto

### Fase 2
OCR local

### Fase 3
Extração da NF

### Fase 4
JSON

### Fase 5
Markdown

### Fase 6
Validação

### Fase 7
Processamento em lote

### Fase 8
Interface Windows

### Fase 9
SQLite

### Fase 10
fila de revisão

### Fase 11
camada opcional de IA

### Fase 12
geração do EXE

---

# 37. REGRA DE DESENVOLVIMENTO

Não implemente a aplicação inteira de uma vez.

Desenvolva em ciclos:

```text
implementar
↓
testar
↓
corrigir
↓
validar
↓
documentar
↓
seguir para próxima fase
```

Depois de cada fase:

1. execute os testes;
2. informe o resultado;
3. identifique problemas;
4. corrija;
5. só então avance.

Não considere uma fase concluída apenas porque o código foi escrito.

Ela deve estar funcionando.

---

# 38. PRIMEIRA ENTREGA

Comece agora pela Fase 1.

Não implemente ainda:

- IA;
- banco complexo;
- interface sofisticada;
- sistema de fornecedores;
- exportação avançada.

Primeiro construa um protótipo funcional capaz de:

```text
PDF
↓
detectar se possui texto
↓
extrair texto
↓
informar quantidade de páginas
↓
salvar texto
↓
mostrar resultado
```

Depois avance para OCR.

---

# 39. CRITÉRIO DE SUCESSO

O projeto será considerado bem-sucedido quando for possível colocar:

```text
500 PDFs de NFs
```

em uma pasta e processá-los automaticamente, mantendo:

- alta taxa de extração;
- baixa taxa de erro;
- rastreabilidade;
- revisão dos casos problemáticos;
- preservação dos documentos originais;
- geração de dados estruturados;
- mínimo uso possível de IA.

O objetivo principal não é simplesmente "ler PDFs".

O objetivo é:

> **Transformar um grande volume de Notas Fiscais escaneadas em dados estruturados de forma local, confiável, auditável e com o mínimo possível de consumo de tokens.**

---

# 40. REGRA FINAL

Durante todo o desenvolvimento, questione:

> "Este problema realmente precisa de IA?"

Se a resposta for não:

**resolver localmente.**

Se puder ser resolvido com regex:

**usar regex.**

Se puder ser resolvido com regra:

**usar regra.**

Se puder ser resolvido com OCR:

**usar OCR.**

Se puder ser resolvido por validação matemática:

**usar cálculo.**

Usar IA somente quando houver ganho real de interpretação.

A arquitetura deve ser orientada por:

**LOCAL FIRST → DETERMINISTIC FIRST → AI WHEN NECESSARY**

Comece pela Fase 1 e, após validar o primeiro módulo, continue incrementalmente até chegar ao aplicativo Windows final.
