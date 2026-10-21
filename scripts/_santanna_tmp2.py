from config import ads_client
c=ads_client(); ga=c.get_service("GoogleAdsService"); CID="3136649243"
for q in ["SELECT campaign.name,campaign.geo_target_type_setting.positive_geo_target_type,campaign.network_settings.target_search_network,campaign.network_settings.target_content_network FROM campaign WHERE campaign.status='ENABLED'",
 "SELECT campaign.name,campaign_criterion.location.geo_target_constant,campaign_criterion.proximity.radius,campaign_criterion.type,campaign_criterion.negative FROM campaign_criterion WHERE campaign.status='ENABLED' AND campaign_criterion.type IN ('LOCATION','PROXIMITY')",
 "SELECT campaign.name,metrics.search_impression_share,metrics.search_budget_lost_impression_share,metrics.search_rank_lost_impression_share,metrics.average_cpc FROM campaign WHERE campaign.status='ENABLED' AND segments.date DURING LAST_7_DAYS",
 "SELECT user_location_view.country_criterion_id,segments.geo_target_city,metrics.clicks,metrics.cost_micros FROM user_location_view WHERE segments.date DURING LAST_7_DAYS AND campaign.status='ENABLED'",
 "SELECT campaign.name,campaign_criterion.keyword.text,campaign_criterion.negative FROM campaign_criterion WHERE campaign.status='ENABLED' AND campaign_criterion.type='KEYWORD'"]:
    try:
        for r in ga.search(customer_id=CID,query=q): print(str(r).replace("\n"," ")[:400])
    except Exception as e: print("ERR",str(e)[-300:])
    print("----")
