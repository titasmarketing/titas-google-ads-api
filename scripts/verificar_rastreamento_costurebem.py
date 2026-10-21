"""CostureBem: verificação de rastreamento (somente leitura).
1) Google Ads: auto-tagging, sufixos/templates de URL e conversões de hoje e ontem por ação.
2) GA4: sessões e eventos de checkout/compra por origem/mídia (hoje e ontem), compras por transação (7 dias)
   e eventos em tempo real (últimos 30 min).
Rodar: uv run --python 3.12 --with-requirements requirements.txt python scripts/verificar_rastreamento_costurebem.py
"""
from google.ads.googleads.errors import GoogleAdsException
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (DateRange, Dimension, Filter, FilterExpression, FilterExpressionList,
                                                Metric, RunRealtimeReportRequest, RunReportRequest)
from config import ads_client, ga_credentials

CID = "3546290186"


def linha(t):
    print("\n" + "=" * 8 + " " + t)


def google_ads():
    ga = ads_client().get_service("GoogleAdsService")
    q = lambda s: list(ga.search(customer_id=CID, query=s))
    linha("GOOGLE ADS: CONTA")
    for r in q("SELECT customer.descriptive_name, customer.auto_tagging_enabled, customer.final_url_suffix, "
               "customer.tracking_url_template FROM customer"):
        c = r.customer
        print(f"{c.descriptive_name} | auto-tagging={c.auto_tagging_enabled} | sufixo='{c.final_url_suffix}' | template='{c.tracking_url_template}'")
    linha("GOOGLE ADS: CAMPANHAS ATIVAS")
    for r in q("SELECT campaign.id, campaign.name, campaign.advertising_channel_type, campaign.bidding_strategy_type, "
               "campaign.final_url_suffix, campaign.tracking_url_template FROM campaign WHERE campaign.status = 'ENABLED'"):
        c = r.campaign
        print(f"{c.id} | {c.name} | {c.advertising_channel_type.name} | {c.bidding_strategy_type.name} | sufixo='{c.final_url_suffix}' | template='{c.tracking_url_template}'")
    linha("GOOGLE ADS: ANÚNCIOS ATIVOS (URL final e sufixo)")
    for r in q("SELECT campaign.name, ad_group.name, ad_group_ad.ad.id, ad_group_ad.ad.final_urls, ad_group_ad.ad.final_url_suffix, "
               "ad_group_ad.ad.tracking_url_template FROM ad_group_ad WHERE campaign.status = 'ENABLED' "
               "AND ad_group.status = 'ENABLED' AND ad_group_ad.status = 'ENABLED'"):
        a = r.ad_group_ad.ad
        print(f"{r.campaign.name} | {r.ad_group.name} | {list(a.final_urls)} | sufixo='{a.final_url_suffix}' | template='{a.tracking_url_template}'")
    linha("GOOGLE ADS: AÇÕES DE CONVERSÃO ATIVAS")
    for r in q("SELECT conversion_action.id, conversion_action.name, conversion_action.category, conversion_action.type, "
               "conversion_action.primary_for_goal, conversion_action.counting_type, conversion_action.value_settings.default_value "
               "FROM conversion_action WHERE conversion_action.status = 'ENABLED'"):
        c = r.conversion_action
        print(f"{c.id} | {c.name} | {c.category.name} | {c.type_.name} | principal={c.primary_for_goal} | contagem={c.counting_type.name} | valor_padrao={c.value_settings.default_value}")
    linha("GOOGLE ADS: CONVERSÕES REGISTRADAS ONTEM E HOJE (por data do clique)")
    rows = q("SELECT segments.date, segments.conversion_action_name, metrics.all_conversions, metrics.all_conversions_value, "
             "metrics.conversions FROM customer WHERE segments.date DURING LAST_7_DAYS")
    rows += q("SELECT segments.date, segments.conversion_action_name, metrics.all_conversions, metrics.all_conversions_value, "
              "metrics.conversions FROM customer WHERE segments.date DURING TODAY")
    for r in sorted(rows, key=lambda r: r.segments.date):
        m = r.metrics
        if m.all_conversions:
            print(f"{r.segments.date} | {r.segments.conversion_action_name} | todas={m.all_conversions:.1f} | valor={m.all_conversions_value:.2f} | principais={m.conversions:.1f}")


def ga4():
    creds = ga_credentials()
    props = [(s.display_name, p) for s in AnalyticsAdminServiceClient(credentials=creds).list_account_summaries()
             for p in s.property_summaries]
    alvo = [p for n, p in props if "costure" in (n + p.display_name).lower()]
    if not alvo:
        print("GA4: nenhuma propriedade da CostureBem visível. Propriedades visíveis:", [(n, p.display_name) for n, p in props])
        return
    prop = alvo[0].property
    data = BetaAnalyticsDataClient(credentials=creds)
    eventos = FilterExpression(filter=Filter(field_name="eventName", in_list_filter=Filter.InListFilter(
        values=["session_start", "begin_checkout", "add_payment_info", "purchase"])))
    linha(f"GA4 {alvo[0].display_name} ({prop}): EVENTOS POR ORIGEM/MÍDIA/CAMPANHA, ONTEM E HOJE")
    resp = data.run_report(RunReportRequest(property=prop, date_ranges=[DateRange(start_date="yesterday", end_date="today")],
        dimensions=[Dimension(name="date"), Dimension(name="sessionSource"), Dimension(name="sessionMedium"),
                    Dimension(name="sessionCampaignName"), Dimension(name="eventName")],
        metrics=[Metric(name="eventCount"), Metric(name="totalUsers")], dimension_filter=eventos, limit=500))
    for r in resp.rows:
        d = [x.value for x in r.dimension_values]; m = [x.value for x in r.metric_values]
        print(" | ".join(d), "| eventos=", m[0], "| usuários=", m[1])
    linha("GA4: COMPRAS POR TRANSAÇÃO, 7 DIAS (duplicidade = eventos > 1)")
    resp = data.run_report(RunReportRequest(property=prop, date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        dimensions=[Dimension(name="transactionId"), Dimension(name="sessionSourceMedium")],
        metrics=[Metric(name="eventCount"), Metric(name="purchaseRevenue")],
        dimension_filter=FilterExpression(filter=Filter(field_name="eventName", string_filter=Filter.StringFilter(value="purchase"))), limit=200))
    for r in resp.rows:
        print(" | ".join(x.value for x in r.dimension_values), "| eventos=", r.metric_values[0].value, "| receita=", r.metric_values[1].value)
    linha("GA4 TEMPO REAL (últimos 30 min)")
    rt = data.run_realtime_report(RunRealtimeReportRequest(property=prop,
        dimensions=[Dimension(name="eventName"), Dimension(name="minutesAgo")], metrics=[Metric(name="eventCount")],
        dimension_filter=eventos, limit=200))
    for r in rt.rows:
        print(" | ".join(x.value for x in r.dimension_values), "| eventos=", r.metric_values[0].value)
    if not rt.rows:
        print("nenhum evento de sessão/checkout/compra nos últimos 30 min")


if __name__ == "__main__":
    try:
        google_ads()
    except GoogleAdsException as ex:
        print("ERRO Google Ads:", " | ".join(f"{e.error_code} - {e.message}" for e in ex.failure.errors))
    ga4()
