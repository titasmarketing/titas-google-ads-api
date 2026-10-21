"""Teste GA4: lista contas/propriedades que a conta de serviço enxerga e puxa sessões dos últimos 7 dias (somente leitura)."""
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
from google.api_core.exceptions import GoogleAPICallError

from config import ga_credentials


def main():
    creds = ga_credentials()
    admin = AnalyticsAdminServiceClient(credentials=creds)
    data = BetaAnalyticsDataClient(credentials=creds)

    try:
        summaries = list(admin.list_account_summaries())
    except GoogleAPICallError as ex:
        print("ERRO ao listar contas do GA4:", ex.message)
        return

    props = [(s.display_name, p) for s in summaries for p in s.property_summaries]
    print(f"{len(summaries)} conta(s) GA4 e {len(props)} propriedade(s) visíveis para a conta de serviço")
    if not props:
        print("Nenhuma ainda: adicione o e-mail da conta de serviço como Leitor em cada conta do GA4 (Fase 5).")
        return

    for account_name, p in props:
        label = f"{account_name} / {p.display_name} ({p.property})"
        try:
            resp = data.run_report(
                RunReportRequest(
                    property=p.property,
                    date_ranges=[DateRange(start_date="7daysAgo", end_date="yesterday")],
                    metrics=[Metric(name="sessions"), Metric(name="totalUsers"), Metric(name="keyEvents")],
                )
            )
        except GoogleAPICallError as ex:
            print(f"- {label}: ERRO {ex.message}")
            continue
        if not resp.rows:
            print(f"- {label}: sem dados nos últimos 7 dias")
            continue
        v = [m.value for m in resp.rows[0].metric_values]
        print(f"- {label}: {int(v[0]):,} sessões | {int(v[1]):,} usuários | {float(v[2]):,.0f} eventos-chave")


if __name__ == "__main__":
    main()
