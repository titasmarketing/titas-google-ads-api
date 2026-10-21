import sys, json
sys.path.insert(0, 'scripts')
from config import ga_credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import *
c = BetaAnalyticsDataClient(credentials=ga_credentials())
P = 'properties/259700810'
def run(dims, mets, start, end, filt=None, limit=50, order=None):
    r = c.run_report(RunReportRequest(property=P, dimensions=[Dimension(name=d) for d in dims], metrics=[Metric(name=m) for m in mets],
        date_ranges=[DateRange(start_date=start, end_date=end)], dimension_filter=filt, limit=limit,
        order_bys=order or []))
    return [[*(v.value for v in row.dimension_values), *(v.value for v in row.metric_values)] for row in r.rows]
out = {}
out['realtime'] = [[*(v.value for v in r.dimension_values), *(v.value for v in r.metric_values)] for r in c.run_realtime_report(RunRealtimeReportRequest(property=P, dimensions=[Dimension(name='eventName')], metrics=[Metric(name='eventCount')])).rows]
out['mensal'] = run(['yearMonth'], ['sessions','totalUsers','ecommercePurchases','purchaseRevenue','addToCarts','checkouts'], '2026-04-01', '2026-10-12')
f = FilterExpression(filter=Filter(field_name='pagePath', string_filter=Filter.StringFilter(match_type=Filter.StringFilter.MatchType.CONTAINS, value='checkout')))
out['checkout_pages'] = run(['pagePath'], ['screenPageViews','totalUsers'], '2026-09-19', '2026-10-12', f)
f2 = FilterExpression(filter=Filter(field_name='pagePath', string_filter=Filter.StringFilter(match_type=Filter.StringFilter.MatchType.CONTAINS, value='success')))
out['success_pages'] = run(['pagePath','date'], ['screenPageViews'], '2026-09-01', '2026-10-12', f2)
out['eventos'] = run(['eventName'], ['eventCount','totalUsers'], '2026-10-01', '2026-10-12', limit=60)
out['pagamento'] = run(['eventName','paymentType'], ['eventCount'], '2026-09-01', '2026-10-12', FilterExpression(filter=Filter(field_name='eventName', in_list_filter=Filter.InListFilter(values=['add_payment_info','purchase','add_shipping_info']))))
out['browser_checkout'] = run(['deviceCategory','operatingSystem'], ['sessions','checkouts','ecommercePurchases'], '2026-09-19', '2026-10-12', limit=15, order=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name='sessions'), desc=True)])
out['novos_recorrentes'] = run(['newVsReturning'], ['sessions','ecommercePurchases','purchaseRevenue'], '2026-07-01', '2026-10-12')
out['itens_receita_90d'] = run(['itemName'], ['itemRevenue','itemsPurchased','itemsViewed'], '2026-07-14', '2026-10-12', limit=25, order=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name='itemRevenue'), desc=True)])
out['busca'] = run(['searchTerm'], ['eventCount'], '2026-09-12', '2026-10-12', limit=20, order=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name='eventCount'), desc=True)])
json.dump(out, open('/tmp/audit.json','w'), ensure_ascii=False)
for k,v in out.items(): print('==',k); [print(r) for r in v[:30]]
