# Google Ads + GA4 via API oficial: TITÃS Marketing

Acesso direto às APIs do Google Ads (todas as contas da MCC) e do Google Analytics 4, sem Zapier e sem MCP.
Somente leitura nos scripts de teste.

## Configurar no seu computador (uma vez)

1. Instale o `uv` (gerenciador de Python):
   - macOS: `brew install uv`  (ou `curl -LsSf https://astral.sh/uv/install.sh | sh`)
   - Windows (PowerShell): `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. Copie `.env.example` para `.env`.
3. Crie a pasta `credenciais/` e salve nela a sua chave JSON com o nome `google-service-account.json`.
   A chave vem do cofre de senhas da TITÃS. Cada gestor tem a sua; não peça nem use a de outra pessoa.
4. Teste:

```
uv run --python 3.12 --with-requirements requirements.txt python scripts/ads_test.py
uv run --python 3.12 --with-requirements requirements.txt python scripts/ga4_test.py
```

`ads_test.py` lista as contas da MCC e mostra os últimos 7 dias de cada uma.
`ga4_test.py` lista as propriedades do GA4 que a conta de serviço enxerga.

## Cuidados

- `.env`, `credenciais/` e `dados/` nunca vão para o git (a chave dá acesso às contas dos clientes; `dados/` guarda dados de clientes).
- Não envie a chave por WhatsApp, e-mail ou chat. Use o cofre de senhas ou um link de uso único com expiração.
- Saiu alguém da equipe, ou a chave vazou? Avise o Pedro: a chave daquela pessoa é apagada no Google Cloud sem afetar as outras.

## Como funciona

- Google Ads API v25. Não usa developer token (descontinuado em 09/09/2026): o acesso é do projeto do Google Cloud `fiery-splice-511017-j6`.
- A conta de serviço `api-titas@fiery-splice-511017-j6.iam.gserviceaccount.com` entra na MCC como usuário e enxerga todas as contas de clientes; o ID da MCC vai no cabeçalho `login-customer-id`.
- Limite diário do Google Ads depende do nível de acesso do projeto (Explorer: 2.880 operações/dia em contas reais; relatórios contam). Confira em console.cloud.google.com/google/ads-apis/overview.
- No GA4 não existe MCC: a conta de serviço só enxerga as contas do Analytics em que foi adicionada como Leitor.

## Dados para analisar no Claude Desktop

O Claude Desktop lê pastas anexadas, mas não roda comandos. Por isso os dados são baixados antes, aqui, e cada pasta traz um `_LEIAME.md`.
Peça ao Claude Code: "atualize os dados do Google" (ou rode o script de download). Depois anexe a pasta do cliente ao projeto dele no Claude Desktop e cole o conteúdo de `INSTRUCOES_CLAUDE_DESKTOP.md` nas instruções do projeto.
