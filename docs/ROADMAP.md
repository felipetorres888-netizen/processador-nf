# Roadmap — Processador NF

12 fases do `docs/mega-prompt.md` (seção 36). Este arquivo é o checklist que a rotina noturna na nuvem consulta a cada disparo para saber exatamente o que já está pronto e qual é a próxima fase a atacar. Atualize a linha da fase (✅/⬜) e o commit correspondente sempre que uma fase for concluída, testada e validada — nunca marque ✅ só porque o código foi escrito (regra §37 do mega prompt).

| # | Fase | Escopo (nuvem?) | Status | Commit final |
|---|------|------------------|--------|--------------|
| 1 | PDF → texto nativo | ✅ Sim (feito localmente) | ✅ Concluída | `f4129ba` |
| 2 | OCR local (Tesseract) | ✅ Sim (feito localmente) | ✅ Concluída | `93f43a6` |
| 3a | Extração da NF — identificação (número, série, CNPJ, chave de acesso, data, valor total) | ✅ Sim | ✅ Concluída | `c6e6ab8` |
| 3b | Extração da NF — itens (tabela de produtos, spec §11) | ✅ Sim | ⬜ Pendente | — |
| 4 | JSON estruturado | ✅ Sim | ⬜ Pendente | — |
| 5 | Markdown legível | ✅ Sim | ⬜ Pendente | — |
| 6 | Validação matemática (qtd×valor≈total etc.) | ✅ Sim | ⬜ Pendente | — |
| 7 | Processamento em lote formal (métricas, resumo) | ✅ Sim | ⬜ Pendente | — |
| 8 | Interface Windows (GUI) | 🚫 **Não** — sem tela no sandbox Linux | ⬜ Fora de escopo esta rodada | — |
| 9 | Banco SQLite | ✅ Sim | ⬜ Pendente | — |
| 10 | Fila de revisão humana | ⚠️ Backend sim, tela não (depende da Fase 8) | ⬜ Pendente (só a parte sem tela) | — |
| 11 | Camada opcional de IA (arquitetura `AIService`, sem chamar API real) | ✅ Sim | ⬜ Pendente | — |
| 12 | Geração do .exe (PyInstaller) | 🚫 **Não** — precisa rodar no Windows | ⬜ Fora de escopo esta rodada | — |

## Regra de execução (vale para toda sessão desta rotina)

1. Leia este arquivo primeiro. Pegue a primeira fase `⬜ Pendente` na ordem da tabela (não pule fases).
2. Fases 8 e 12 estão **fora de escopo** desta rotina — nunca as inicie, mesmo que sejam a "próxima" na ordem numérica; pule para a próxima fase marcada `✅ Sim` na coluna Escopo.
3. Escreva o plano da fase (skill `superpowers:writing-plans`) em `docs/superpowers/plans/`, seguindo exatamente o padrão dos planos das Fases 1 e 2 já existentes nessa pasta — copie a estrutura (Global Constraints, tarefas com TDD passo a passo, código completo, sem placeholder).
4. Execute o plano (skill `superpowers:subagent-driven-development`) — um agente implementador + um revisor por tarefa, revisão final de branch inteiro ao terminar todas as tarefas da fase.
5. Rode a suíte de testes completa (`pytest -v` na raiz) antes de considerar a fase concluída — inclui os testes das Fases 1 e 2 (alguns usam Tesseract de verdade, ver Setup abaixo).
6. Atualize a linha da fase nesta tabela (✅, commit final) e faça commit disso junto com o resto.
7. `git push` imediatamente após cada fase concluída — nunca acumule várias fases sem enviar.
8. Se sobrar tempo na sessão, siga para a próxima fase pendente. Se não sobrar, pare no meio de uma fase de forma segura (commit do que está funcionando e testado; nunca deixe o repositório com testes quebrados).
