import json, sys
from config import ads_client
CID="3136649243"
c=ads_client(); ga=c.get_service("GoogleAdsService")
def q(s):
    return list(ga.search(customer_id=CID, query=s))
out={}
for per in ["LAST_30_DAYS","LAST_7_DAYS"]:
    rows=q(f"""SELECT campaign.id,campaign.name,campaign.status,campaign.advertising_channel_type,campaign.bidding_strategy_type,
    ad_group.id,ad_group.name,ad_group.status,metrics.cost_micros,metrics.impressions,metrics.clicks,metrics.conversions,metrics.all_conversions,metrics.search_impression_share
    FROM ad_group WHERE segments.date DURING {per} AND metrics.impressions>0""")
    out["ag_"+per]=[dict(camp=r.campaign.name,cst=r.campaign.status.name,ch=r.campaign.advertising_channel_type.name,bid=r.campaign.bidding_strategy_type.name,budget=0,
      ag=r.ad_group.name,ags=r.ad_group.status.name,cost=round(r.metrics.cost_micros/1e6,2),imp=r.metrics.impressions,clk=r.metrics.clicks,conv=round(r.metrics.conversions,1),allconv=round(r.metrics.all_conversions,1)) for r in rows]
    rows=q(f"""SELECT campaign.name,ad_group.name,segments.conversion_action_name,metrics.conversions,metrics.all_conversions FROM ad_group WHERE segments.date DURING {per} AND metrics.all_conversions>0""")
    out["convaction_"+per]=[dict(camp=r.campaign.name,ag=r.ad_group.name,action=r.segments.conversion_action_name,conv=round(r.metrics.conversions,1),allc=round(r.metrics.all_conversions,1)) for r in rows]
rows=q("""SELECT campaign.name,campaign.status,ad_group.name,ad_group.status,ad_group_criterion.keyword.text,ad_group_criterion.keyword.match_type,ad_group_criterion.status,metrics.cost_micros,metrics.impressions,metrics.clicks,metrics.conversions
 FROM keyword_view WHERE segments.date DURING LAST_30_DAYS AND metrics.impressions>0 ORDER BY metrics.cost_micros DESC""")
out["kw30"]=[dict(camp=r.campaign.name,ag=r.ad_group.name,kw=r.ad_group_criterion.keyword.text,mt=r.ad_group_criterion.keyword.match_type.name,st=r.ad_group_criterion.status.name,cost=round(r.metrics.cost_micros/1e6,2),imp=r.metrics.impressions,clk=r.metrics.clicks,conv=round(r.metrics.conversions,1)) for r in rows]
rows=q("""SELECT campaign.name,ad_group.name,search_term_view.search_term,metrics.cost_micros,metrics.impressions,metrics.clicks,metrics.conversions FROM search_term_view WHERE segments.date DURING LAST_30_DAYS AND metrics.clicks>0 ORDER BY metrics.cost_micros DESC""")
out["st30"]=[dict(camp=r.campaign.name,ag=r.ad_group.name,term=r.search_term_view.search_term,cost=round(r.metrics.cost_micros/1e6,2),clk=r.metrics.clicks,conv=round(r.metrics.conversions,1)) for r in rows]
rows=q("""SELECT campaign.name,campaign.status,ad_group.name,ad_group.status FROM ad_group WHERE campaign.status='ENABLED'""")
out["structure"]=[dict(camp=r.campaign.name,ag=r.ad_group.name,ags=r.ad_group.status.name) for r in rows]
rows=q("""SELECT segments.date,ad_group.name,metrics.cost_micros,metrics.clicks,metrics.conversions FROM ad_group WHERE segments.date DURING LAST_30_DAYS AND campaign.status='ENABLED'""")
out["daily"]=[dict(d=r.segments.date,ag=r.ad_group.name,cost=round(r.metrics.cost_micros/1e6,2),clk=r.metrics.clicks,conv=round(r.metrics.conversions,1)) for r in rows]
rows=q("""SELECT ad_group.name,ad_group_ad.ad.final_urls,ad_group_ad.status FROM ad_group_ad WHERE campaign.status='ENABLED' AND ad_group_ad.status='ENABLED'""")
out["urls"]=[dict(ag=r.ad_group.name,url=list(r.ad_group_ad.ad.final_urls)) for r in rows]
rows=q("""SELECT conversion_action.name,conversion_action.primary_for_goal,conversion_action.status,conversion_action.category FROM conversion_action WHERE conversion_action.status='ENABLED'""")
out["convactions"]=[dict(n=r.conversion_action.name,prim=r.conversion_action.primary_for_goal,cat=r.conversion_action.category.name) for r in rows]
rows=q("SELECT campaign.name,campaign.status,campaign_budget.amount_micros FROM campaign WHERE campaign.status='ENABLED'")
out["budgets"]=[dict(c=r.campaign.name,b=r.campaign_budget.amount_micros/1e6) for r in rows]
json.dump(out,open("dados/santanna_ads_2026-10-15.json","w"),ensure_ascii=False,indent=1)
print("ok")
