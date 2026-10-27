"""Baixa um conjunto padrão de dados do Google Ads (somente leitura) para análise no Claude Desktop.

Uso:
    uv run --python 3.12 --with-requirements requirements.txt python scripts/baixar_dados_google.py
    ... python scripts/baixar_dados_google.py --conta 2683775570     (só uma conta)
    ... python scripts/baixar_dados_google.py --dias 90              (janela de desempenho; padrão 60)

Saída: dados/google_ads/<id> - <nome>/*.json e um _LEIAME.md em cada pasta.
Se uma consulta falhar, o script avisa com [ERRO] e continua com as outras.
"""
import argparse
import datetime as dt
import json
import re
import time

from google.ads.googleads.errors import GoogleAdsException
from google.protobuf.json_format import MessageToDict

from config import MCC_ID, ROOT, ads_client

SAIDA = ROOT / "dados" / "google_ads"
METRICAS = "metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions, metrics.conversions_value"
DEMO = {
    "demografia_idade": ("age_range_view", "ad_group_criterion.age_range.type"),
    "demografia_genero": ("gender_view", "ad_group_criterion.gender.type"),
    "demografia_renda": ("income_range_view", "ad_group_criterion.income_range.type"),
    "demografia_filhos": ("parental_status_view", "ad_group_criterion.parental_status.type"),
}

# nome do arquivo -> (descrição, consulta GAQL). {ini}/{fim} = janela de desempenho; {ini_alt}/{fim_alt} = histórico (28 dias).
CONSULTAS = {
    "campanhas": (
        "Campanhas: status, tipo, estratégia de lances, orçamento diário e metas (CPA/ROAS).",
        "SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, "
        "campaign.bidding_strategy_type, campaign.start_date_time, campaign_budget.amount_micros, "
        "campaign.target_cpa.target_cpa_micros, campaign.maximize_conversions.target_cpa_micros, "
        "campaign.target_roas.target_roas FROM campaign WHERE campaign.status != 'REMOVED'",
    ),
    "acoes_de_conversao": (
        "Ações de conversão: tipo, categoria, se é primária, contagem e modelo de atribuição.",
        "SELECT conversion_action.id, conversion_action.name, conversion_action.status, conversion_action.type, "
        "conversion_action.category, conversion_action.primary_for_goal, conversion_action.counting_type, "
        "conversion_action.attribution_model_settings.attribution_model FROM conversion_action "
        "WHERE conversion_action.status != 'REMOVED'",
    ),
    "desempenho_diario_campanha": (
        "Desempenho por dia e campanha na janela escolhida.",
        f"SELECT segments.date, campaign.id, campaign.name, {METRICAS} FROM campaign "
        "WHERE segments.date BETWEEN '{ini}' AND '{fim}'",
    ),
    "ajustes_lance_demografia_grupo": (
        "Ajustes de lance ATUAIS por idade/gênero/renda/filhos no nível do grupo de anúncios (bid_modifier 1.0 = sem ajuste; vazio = sem ajuste).",
        "SELECT campaign.name, ad_group.name, ad_group_criterion.type, ad_group_criterion.bid_modifier, "
        "ad_group_criterion.negative, ad_group_criterion.status, ad_group_criterion.age_range.type, "
        "ad_group_criterion.gender.type, ad_group_criterion.income_range.type, ad_group_criterion.parental_status.type "
        "FROM ad_group_criterion WHERE ad_group_criterion.type IN ('AGE_RANGE','GENDER','INCOME_RANGE','PARENTAL_STATUS') "
        "AND ad_group_criterion.status != 'REMOVED'",
    ),
    "ajustes_lance_campanha": (
        "Ajustes de lance ATUAIS no nível da campanha (idade, gênero, renda, filhos, dispositivo, local, agenda).",
        "SELECT campaign.name, campaign_criterion.type, campaign_criterion.bid_modifier, campaign_criterion.negative, "
        "campaign_criterion.age_range.type, campaign_criterion.gender.type, campaign_criterion.income_range.type, "
        "campaign_criterion.parental_status.type, campaign_criterion.device.type "
        "FROM campaign_criterion WHERE campaign_criterion.type IN ('AGE_RANGE','GENDER','INCOME_RANGE','PARENTAL_STATUS','DEVICE') "
        "AND campaign_criterion.status != 'REMOVED'",
    ),
    "termos_de_pesquisa": (
        "Termos de pesquisa que geraram cliques na janela escolhida.",
        f"SELECT search_term_view.search_term, search_term_view.status, campaign.name, ad_group.name, {METRICAS} "
        "FROM search_term_view WHERE segments.date BETWEEN '{ini}' AND '{fim}' AND metrics.impressions > 0",
    ),
    "palavras_chave": (
        "Palavras-chave com desempenho na janela escolhida.",
        f"SELECT campaign.name, ad_group.name, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, "
        f"ad_group_criterion.status, {METRICAS} FROM keyword_view "
        "WHERE segments.date BETWEEN '{ini}' AND '{fim}' AND metrics.impressions > 0",
    ),
    "historico_alteracoes": (
        "Histórico de alterações dos últimos 28 dias: data, quem mudou, o que mudou, valor antigo e novo. O Google guarda só ~30 dias. "
        "Alterações pela API aparecem como a conta de serviço (api-titas), não como a pessoa.",
        "SELECT change_event.change_date_time, change_event.change_resource_type, change_event.change_resource_name, "
        "change_event.client_type, change_event.user_email, change_event.resource_change_operation, "
        "change_event.changed_fields, change_event.old_resource, change_event.new_resource, campaign.name "
        "FROM change_event WHERE change_event.change_date_time >= '{ini_alt}' AND change_event.change_date_time <= '{fim_alt}' "
        "ORDER BY change_event.change_date_time DESC LIMIT 10000",
    ),
}
for _nome, (_view, _campo) in DEMO.items():
    CONSULTAS[_nome] = (
        f"Desempenho por dia, campanha e grupo, segmentado por {_nome.split("_")[1].replace("genero","gênero")} (o 'UNDETERMINED' é o 'Desconhecido').",
        f"SELECT segments.date, campaign.name, ad_group.name, {_campo}, {METRICAS} FROM {_view} "
        "WHERE segments.date BETWEEN '{ini}' AND '{fim}'",
    )


def limpar(nome: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", nome).strip()[:60] or "sem nome"


def linhas(ga, cid: str, gaql: str):
    out = []
    for lote in ga.search_stream(customer_id=cid, query=gaql):
        for r in lote.results:
            out.append(MessageToDict(type(r).pb(r), preserving_proto_field_name=True))
    return out


def baixar_conta(client, c, dias: int):
    ga = client.get_service("GoogleAdsService")
    hoje = dt.date.today()
    fmt = {
        "ini": (hoje - dt.timedelta(days=dias)).isoformat(),
        "fim": (hoje - dt.timedelta(days=1)).isoformat(),
        "ini_alt": (hoje - dt.timedelta(days=28)).isoformat() + " 00:00:00",
        "fim_alt": hoje.isoformat() + " 23:59:59",
    }
    pasta = SAIDA / f"{c.id} - {limpar(c.descriptive_name)}"
    pasta.mkdir(parents=True, exist_ok=True)
    resumo, erros = [], []
    for nome, (desc, gaql) in CONSULTAS.items():
        try:
            dados = linhas(ga, str(c.id), gaql.format(**fmt))
            (pasta / f"{nome}.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1))
            resumo.append((nome, desc, len(dados)))
        except GoogleAdsException as ex:
            msg = " | ".join(f"{e.error_code} {e.message}" for e in ex.failure.errors)
            erros.append((nome, msg))
            print(f"  [ERRO] {c.descriptive_name} / {nome}: {msg}")
        time.sleep(0.2)
    md = [f"# Google Ads: {c.descriptive_name} (conta {c.id})", "",
          f"Baixado em {hoje.isoformat()} (somente leitura). Moeda: {c.currency_code}. Janela de desempenho: {fmt['ini']} a {fmt['fim']}.", "",
          "Como ler: `cost_micros` ÷ 1.000.000 = valor na moeda da conta. `bid_modifier` 1.0 = sem ajuste, 0.8 = -20%, 1.2 = +20%. "
          "Datas em AAAA-MM-DD. Campos aparecem aninhados (ex.: `campaign.name`).", "", "## Arquivos", ""]
    md += [f"- `{n}.json` ({q} linhas): {d}" for n, d, q in resumo]
    if erros:
        md += ["", "## Consultas que falharam", ""] + [f"- `{n}`: {m}" for n, m in erros]
    md += ["", "## Limites", "- O histórico de alterações cobre no máximo ~30 dias; mudanças mais antigas não existem na API.",
           "- Para mais dados, peça ao gestor para pedir ao Claude Code: \"atualize os dados do Google Ads desta conta\"."]
    (pasta / "_LEIAME.md").write_text("\n".join(md))
    return pasta, len(resumo), len(erros)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conta", help="ID da conta (10 dígitos, sem hífen). Sem isso, baixa todas da MCC.")
    ap.add_argument("--dias", type=int, default=60)
    a = ap.parse_args()
    client = ads_client()
    ga = client.get_service("GoogleAdsService")
    q = ("SELECT customer_client.id, customer_client.descriptive_name, customer_client.manager, "
         "customer_client.status, customer_client.currency_code FROM customer_client WHERE customer_client.status = 'ENABLED'")
    contas = [r.customer_client for r in ga.search(customer_id=MCC_ID, query=q) if not r.customer_client.manager]
    if a.conta:
        contas = [c for c in contas if str(c.id) == a.conta.replace("-", "")]
        if not contas:
            raise SystemExit(f"Conta {a.conta} não encontrada na MCC {MCC_ID}.")
    print(f"{len(contas)} conta(s) para baixar (janela: {a.dias} dias)")
    indice = []
    for c in contas:
        pasta, ok, erros = baixar_conta(client, c, a.dias)
        print(f"- {c.descriptive_name}: {ok} consultas ok, {erros} com erro -> {pasta.relative_to(ROOT)}")
        indice.append(f"- {pasta.name}")
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "_LEIAME.md").write_text("# Dados do Google Ads (uma pasta por conta de cliente)\n\n"
                                      + "\n".join(sorted(indice)) + "\n\nCada pasta tem um _LEIAME.md descrevendo os arquivos.\n")


if __name__ == "__main__":
    main()
