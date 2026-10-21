from config import ads_client
c=ads_client(); svc=c.get_service("KeywordPlanIdeaService"); CID="3136649243"
kws=["vacina dtpa","dtpa","vacina dtpa gestante","vacina coqueluche","vacina coqueluche gestante","vacina hpv","vacina hpv preço","vacina hpv vinhedo","vacina meningite b","vacina meningite","beyfortus","vacina vsr gestante","abrysvo","vacina bebe","vacinas bebe","pacote vacina bebe","clinica de vacina","clinica de vacinação","vacina gestante","vacinas para gestante","vacina herpes zoster","shingrix","vacina dengue","qdenga","vacinas vinhedo","clinica de vacina vinhedo","vacina pneumo 20"]
req=c.get_type("GenerateKeywordHistoricalMetricsRequest")
req.customer_id=CID; req.keywords.extend(kws)
for g in ["1031780","1032130","9074204","9074222"]: req.geo_target_constants.append(f"geoTargetConstants/{g}")
req.language="languageConstants/1014"
req.keyword_plan_network=c.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
gs=c.get_service("GeoTargetConstantService")
r=svc.generate_keyword_historical_metrics(request=req)
for x in sorted(r.results,key=lambda x:-x.keyword_metrics.avg_monthly_searches):
    m=x.keyword_metrics
    vols=[v.monthly_searches for v in m.monthly_search_volumes][-6:]
    print(f"{x.text:30s} avg={m.avg_monthly_searches:6d} comp={m.competition.name:8s} cpc_low={m.low_top_of_page_bid_micros/1e6:.2f} cpc_high={m.high_top_of_page_bid_micros/1e6:.2f} last6={vols} close={list(x.close_variants)[:3]}")
ga=c.get_service("GoogleAdsService")
for row in ga.search(customer_id=CID,query="SELECT geo_target_constant.name,geo_target_constant.id FROM geo_target_constant WHERE geo_target_constant.id IN (1031780,1032130,9074204,9074222)"):
    print(row.geo_target_constant.id,row.geo_target_constant.name)
