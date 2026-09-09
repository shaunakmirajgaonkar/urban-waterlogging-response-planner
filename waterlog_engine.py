from __future__ import annotations
import numpy as np
import pandas as pd

BANDS=("Low","Moderate","High","Critical")

def classify_score(score):
    s=float(score)
    return "Low" if s<25 else "Moderate" if s<50 else "High" if s<75 else "Critical"

def validate_inputs(zones, history, reports):
    required = {
        "zones": {"zone_id","zone_name","area","elevation_risk_pct","drainage_capacity_pct","road_importance_pct","population_exposure","critical_facilities","drain_clearance_pct","response_team_readiness_pct","rainfall_24h_mm","rainfall_6h_mm","low_lying_pct","road_blockage_pct","response_distance_km"},
        "history": {"zone_id","date","rainfall_mm","water_depth_cm","drain_clearance_pct","road_blockage_pct","citizen_report_count","response_time_min"},
        "reports": {"report_id","zone_id","date","report_type","severity","resolved"}}
    for name, needed in required.items():
        df={"zones":zones,"history":history,"reports":reports}[name]
        missing=sorted(needed-set(df.columns))
        if missing: raise ValueError(f"{name} missing required columns: {', '.join(missing)}")

def _num(df, cols):
    for c in cols: df[c]=pd.to_numeric(df[c],errors="coerce").fillna(0.0)

def build_response_screening(zones, history, reports):
    validate_inputs(zones, history, reports)
    z,h,r=zones.copy(),history.copy(),reports.copy()
    _num(z,["elevation_risk_pct","drainage_capacity_pct","road_importance_pct","population_exposure","critical_facilities","drain_clearance_pct","response_team_readiness_pct","rainfall_24h_mm","rainfall_6h_mm","low_lying_pct","road_blockage_pct","response_distance_km"])
    _num(h,["rainfall_mm","water_depth_cm","drain_clearance_pct","road_blockage_pct","citizen_report_count","response_time_min"])
    hist=h.groupby("zone_id",as_index=False).agg(historical_rainfall=("rainfall_mm","mean"),historical_water_depth=("water_depth_cm","mean"),historical_reports=("citizen_report_count","mean"),historical_response_time=("response_time_min","mean"))
    rep=r.groupby("zone_id",as_index=False).agg(report_count=("report_id","count"),unresolved_reports=("resolved",lambda x:int((x.astype(str).str.lower()!="true").sum())))
    o=z.merge(hist,on="zone_id",how="left").merge(rep,on="zone_id",how="left")
    for c in ["historical_rainfall","historical_water_depth","historical_reports","historical_response_time","report_count","unresolved_reports"]: o[c]=o[c].fillna(0)
    o["rainfall_component"]=(o["rainfall_24h_mm"].clip(0,200)/200*100*.65+o["rainfall_6h_mm"].clip(0,100)/100*100*.35).clip(0,100)
    o["elevation_component"]=(o["elevation_risk_pct"]*.65+o["low_lying_pct"]*.35).clip(0,100)
    o["drainage_component"]=(100-o["drainage_capacity_pct"]).clip(0,100)
    o["road_component"]=(o["road_importance_pct"]*.55+o["road_blockage_pct"]*.45).clip(0,100)
    o["citizen_component"]=np.minimum(o["report_count"]*8+o["unresolved_reports"]*10+o["historical_reports"]*2,100)
    o["clearance_component"]=(100-o["drain_clearance_pct"]).clip(0,100)
    o["response_component"]=((100-o["response_team_readiness_pct"])*.55+np.minimum(o["response_distance_km"]/10*100,100)*.45).clip(0,100)
    o["facility_component"]=np.minimum(o["critical_facilities"]*12+o["population_exposure"]*.25,100)
    o["history_component"]=np.minimum(o["historical_water_depth"]*8+o["historical_rainfall"]/2+o["historical_response_time"]/2,100)
    o["response_priority_score"]=(o["rainfall_component"]*.18+o["elevation_component"]*.14+o["drainage_component"]*.14+o["road_component"]*.13+o["citizen_component"]*.12+o["clearance_component"]*.11+o["response_component"]*.09+o["facility_component"]*.05+o["history_component"]*.04).clip(0,100).round(1)
    o["risk_band"]=o["response_priority_score"].map(classify_score)
    o["response_readiness_pct"]=(100-(o["clearance_component"]*.35+o["response_component"]*.30+o["drainage_component"]*.20+o["road_component"]*.15)).clip(0,100).round(1)
    driver_map={"rainfall_component":"Rainfall pressure","elevation_component":"Low-elevation exposure","drainage_component":"Drainage-capacity gap","road_component":"Road importance / blockage","citizen_component":"Citizen-report pressure","clearance_component":"Drain-clearance gap","response_component":"Response-readiness gap","facility_component":"Critical-facility exposure","history_component":"Historical waterlogging signal"}
    o["top_driver"]=o[list(driver_map)].idxmax(axis=1).map(driver_map)
    return o

def calculate_metrics(df):
    if df.empty:return {"zones":0,"avg_score":0,"high_critical":0,"rainfall":0,"readiness":0,"citizen":0}
    return {"zones":len(df),"avg_score":round(float(df.response_priority_score.mean()),1),"high_critical":int(df.risk_band.isin(["High","Critical"]).sum()),"rainfall":round(float(df.rainfall_component.mean()),1),"readiness":round(float(df.response_readiness_pct.mean()),1),"citizen":round(float(df.citizen_component.mean()),1)}

def build_area_summary(df):
    if df.empty:return pd.DataFrame(columns=["area","zones","avg_priority","high_critical","avg_rainfall","avg_readiness"])
    o=df.groupby("area",as_index=False).agg(zones=("zone_id","count"),avg_priority=("response_priority_score","mean"),high_critical=("risk_band",lambda x:int(x.isin(["High","Critical"]).sum())),avg_rainfall=("rainfall_component","mean"),avg_readiness=("response_readiness_pct","mean"))
    for c in ["avg_priority","avg_rainfall","avg_readiness"]: o[c]=o[c].round(1)
    return o.sort_values("avg_priority",ascending=False)

def build_response_team_summary(df):
    if df.empty:return pd.DataFrame(columns=["area","zones","readiness","priority","avg_distance_km"])
    o=df.groupby("area",as_index=False).agg(zones=("zone_id","count"),readiness=("response_team_readiness_pct","mean"),priority=("response_priority_score","mean"),avg_distance_km=("response_distance_km","mean"))
    for c in ["readiness","priority","avg_distance_km"]: o[c]=o[c].round(1)
    return o.sort_values("priority",ascending=False)

def build_signal_summary(df):
    vals={"Rainfall pressure":df.rainfall_component.mean(),"Elevation":df.elevation_component.mean(),"Drainage gap":df.drainage_component.mean(),"Road importance / blockage":df.road_component.mean(),"Citizen reports":df.citizen_component.mean(),"Drain clearance gap":df.clearance_component.mean(),"Response gap":df.response_component.mean(),"Facility exposure":df.facility_component.mean()}
    return pd.DataFrame({"signal":list(vals),"value_pct":[round(float(v),1) for v in vals.values()]})

def generate_recommendations(row):
    checks=[("rainfall_component",55,"🌧️ Review rainfall intensity and current local observations."),("elevation_component",50,"📍 Prioritize low-elevation locations for early field checks."),("drainage_component",45,"🕳️ Prioritize drain-clearing and inlet inspection."),("road_component",50,"🚧 Review road importance, blockage, diversions and traffic controls."),("citizen_component",45,"📣 Review clustered or unresolved citizen reports."),("clearance_component",45,"🧹 Assign drainage-clearing teams and update clearance status."),("response_component",45,"🚒 Review response-team readiness, staging and travel distance."),("facility_component",45,"🏥 Review critical-facility access priorities."),("history_component",45,"📋 Review historical waterlogging and response records.")]
    out=[msg for key,t,msg in checks if float(row[key])>=t]
    return out or ["✅ No dominant high-pressure signal detected. Continue routine monitoring."]

def scenario_score(rain,elev,drain,road,citizen,clearance,response,facility,history):
    return round(float(np.clip(rain*.18+elev*.14+drain*.14+road*.13+citizen*.12+clearance*.11+response*.09+facility*.05+history*.04,0,100)),1)
