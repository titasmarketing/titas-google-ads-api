"""Teste Google Ads: lista as contas da MCC e puxa gasto/impressões/cliques dos últimos 7 dias (somente leitura)."""
from google.ads.googleads.errors import GoogleAdsException

from config import MCC_ID, ads_client


def explain(ex: GoogleAdsException) -> str:
    parts = []
    for err in ex.failure.errors:
        parts.append(f"{err.error_code} - {err.message}")
    return " | ".join(parts) or str(ex)


def main():
    client = ads_client()
    ga = client.get_service("GoogleAdsService")

    print(f"MCC {MCC_ID}: listando contas...")
    query = """
        SELECT customer_client.id, customer_client.descriptive_name, customer_client.manager,
               customer_client.status, customer_client.currency_code, customer_client.level
        FROM customer_client
        WHERE customer_client.status != 'CANCELED'
        ORDER BY customer_client.level, customer_client.descriptive_name
    """
    try:
        rows = list(ga.search(customer_id=MCC_ID, query=query))
    except GoogleAdsException as ex:
        print("ERRO ao listar contas da MCC:", explain(ex))
        return

    clients = [r.customer_client for r in rows]
    print(f"{len(clients)} conta(s) encontrada(s) sob a MCC")
    for c in clients:
        kind = "MCC" if c.manager else "conta"
        print(f"- {c.descriptive_name} | {c.id} | {kind} | {c.status.name} | {c.currency_code} | nível {c.level}")

    print("\nMétricas dos últimos 7 dias (contas ativas, não-MCC):")
    metrics_query = """
        SELECT metrics.cost_micros, metrics.impressions, metrics.clicks, metrics.conversions
        FROM customer
        WHERE segments.date DURING LAST_7_DAYS
    """
    for c in clients:
        if c.manager or c.status.name != "ENABLED":
            continue
        try:
            resp = list(ga.search(customer_id=str(c.id), query=metrics_query))
        except GoogleAdsException as ex:
            print(f"- {c.descriptive_name}: ERRO {explain(ex)}")
            continue
        cost = sum(r.metrics.cost_micros for r in resp) / 1_000_000
        imp = sum(r.metrics.impressions for r in resp)
        clk = sum(r.metrics.clicks for r in resp)
        conv = sum(r.metrics.conversions for r in resp)
        if imp == 0 and cost == 0:
            print(f"- {c.descriptive_name}: sem veiculação nos últimos 7 dias")
        else:
            print(f"- {c.descriptive_name}: {c.currency_code} {cost:,.2f} | {imp:,} impressões | {clk:,} cliques | {conv:,.1f} conversões")


if __name__ == "__main__":
    main()
