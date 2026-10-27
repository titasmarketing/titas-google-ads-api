# Google Ads + GA4 API: TITÃS Marketing

Acesso direto às APIs oficiais do Google Ads (MCC) e do Google Analytics 4. Sem Zapier, sem MCP.

## Regras (valem para qualquer gestor que abrir esta pasta)
- Credenciais (`.env`, `credenciais/`): nunca imprimir, commitar, colar em chat ou enviar a terceiros. Para conferir, mostre só o nome da variável.
- Somente leitura por padrão. Alterar conta de cliente (criar, pausar ou editar campanha, orçamento, lance, público) só depois de: (1) mostrar exatamente o que vai mudar, (2) o gestor confirmar aquela ação, (3) rodar antes com `validate_only=True` quando a API permitir.
- Dados baixados ficam em `dados/` (ignorado pelo git; são dados de clientes). Não enviar para serviços externos.
- Cada gestor usa a própria chave. Nunca reutilizar a de outra pessoa.

## Como rodar
`uv run --python 3.12 --with-requirements requirements.txt python scripts/ads_test.py` (e `ga4_test.py`). Cliente Python em `scripts/config.py`.

## Detalhes técnicos
- Google Ads API v25, sem developer token (descontinuado em 09/09/2026). Acesso por projeto do Cloud; `login-customer-id` = MCC do `.env`.
- Relatórios (Search/SearchStream) contam no limite diário: prefira consultas agregadas a laços por campanha.
- GA4: a conta de serviço só vê as contas em que foi adicionada como Leitor. Propriedades via Admin API (`list_account_summaries`), relatórios via Data API (`properties/ID`).

## Dados para análise no Claude Desktop
- Os gestores analisam cada cliente no Claude Desktop (um projeto por cliente). Ele lê as pastas anexadas, mas NÃO roda comandos. Quem mantém `dados/` atualizado é você (Claude Code).
- Pedido "atualize os dados" / "baixe os dados da conta X": rode `uv run --python 3.12 --with-requirements requirements.txt python scripts/baixar_dados_google.py [--conta ID]`, confira o `_LEIAME.md` gerado e diga ao gestor qual pasta anexar (`dados/google_ads/<id> - <nome>`).
- Se o Claude Desktop pediu um dado que não existe: crie um script somente leitura em `scripts/` (padrão dos existentes), rode você mesmo, grave em `dados/` e atualize o `_LEIAME.md`.
- Nunca peça ao gestor para rodar comandos: você tem o terminal. O texto de instruções do projeto no Claude Desktop está em `INSTRUCOES_CLAUDE_DESKTOP.md`.
