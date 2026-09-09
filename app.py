
from pathlib import Path
import html
import pandas as pd
import plotly.express as px
import streamlit as st
from waterlog_engine import *

BASE=Path(__file__).resolve().parent
DATA=BASE/"data"
st.set_page_config(page_title="FloodOps • Urban Waterlogging Response Planner",page_icon="🌧️",layout="wide",initial_sidebar_state="expanded")
st.markdown("""<style>
:root{--ink:#142b3d;--muted:#60758a;--line:#dce7ee}
.stApp{background:linear-gradient(180deg,#fcfeff,#edf7f8);color:var(--ink)}
.block-container{max-width:1580px;padding-top:1rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:#f2f8fa;border-right:1px solid var(--line)}
.hero{background:linear-gradient(120deg,#fff,#eef8ff 52%,#ebfbf4);border:1px solid var(--line);border-radius:28px;padding:30px 34px;margin-bottom:18px;box-shadow:0 14px 44px rgba(30,67,84,.07)}
.ey{font-size:.72rem;font-weight:900;letter-spacing:.16em;text-transform:uppercase;color:#2875ea}.hero h1{font-size:2.45rem;margin:.35rem 0 .6rem}.hero p{color:var(--muted);max-width:1180px}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 8px 25px rgba(24,55,75,.05)}
.lab{font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);font-weight:800}.kpi{font-size:1.7rem;font-weight:900}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:15px}
</style>""",unsafe_allow_html=True)
st.markdown("""<div class="hero"><div class="ey">LOCAL-FIRST · URBAN DRAINAGE · RAPID RESPONSE</div><h1>🌧️ FloodOps</h1><p>Urban Waterlogging Response Planner — prioritizes drainage-clearing and response teams using rainfall pressure, low-elevation exposure, road importance, citizen reports, critical facilities, and response readiness.</p></div>""",unsafe_allow_html=True)

@st.cache_data
def load_data():
    return {"zones":pd.read_csv(DATA/"sample_waterlogging_zones.csv"),"history":pd.read_csv(DATA/"sample_waterlogging_history.csv"),"reports":pd.read_csv(DATA/"sample_citizen_reports.csv")}
d=load_data()
allx=build_response_screening(d["zones"],d["history"],d["reports"])
with st.sidebar:
    st.markdown("### FloodOps controls")
    page=st.radio("Workspace",["Response Command Center","Zone Explorer","Waterlogging Landscape","Drainage & Clearing","Roads & Critical Facilities","Team Dispatch","Scenario Lab","Citizen Report Log","Data & Export"])
    area=st.selectbox("Focus area",["All"]+sorted(allx.area.unique().tolist()))
    bands=st.multiselect("Priority bands",list(BANDS),default=list(BANDS))
    floor=st.slider("Minimum priority score",0,100,0)
    st.markdown("---");st.caption("🟢 Low  ·  🟡 Moderate  ·  🟠 High  ·  🔴 Critical")
s=allx.copy()
if area!="All": s=s[s.area==area]
if bands: s=s[s.risk_band.isin(bands)]
s=s[s.response_priority_score>=floor].copy()
m=calculate_metrics(s)

if page=="Response Command Center":
    st.markdown("## Response command center")
    items=[("Zones screened",m["zones"]),("Average priority",f'{m["avg_score"]:.1f}/100'),("High / Critical",m["high_critical"]),("Rainfall pressure",f'{m["rainfall"]:.1f}%'),("Response readiness",f'{m["readiness"]:.1f}%'),("Citizen pressure",f'{m["citizen"]:.1f}%')]
    cols=st.columns(6)
    for c,(label,val) in zip(cols,items):c.markdown(f'<div class="card"><div class="lab">{label}</div><div class="kpi">{val}</div></div>',unsafe_allow_html=True)
    l,r=st.columns([1.35,1])
    with l:
        top=s.nlargest(15,"response_priority_score")
        hov=[c for c in ["zone_name","area","top_driver","rainfall_24h_mm","road_blockage_pct","response_distance_km"] if c in top.columns]
        fig=px.bar(top,x="zone_id",y="response_priority_score",color="risk_band",hover_data=hov,labels={"zone_id":"Zone","response_priority_score":"Response priority"})
        fig.update_layout(height=410,margin=dict(l=8,r=8,t=20,b=8));st.plotly_chart(fig,use_container_width=True)
    with r:
        q=s.risk_band.value_counts().reindex(list(BANDS),fill_value=0).reset_index();q.columns=["risk_band","count"]
        fig=px.pie(q,values="count",names="risk_band",hole=.62);fig.update_layout(height=410,margin=dict(l=8,r=8,t=20,b=8));st.plotly_chart(fig,use_container_width=True)
    st.dataframe(build_area_summary(s),use_container_width=True,hide_index=True)

elif page=="Zone Explorer":
    st.markdown("## Zone Explorer")
    if s.empty: st.warning("No zones match the current filters.")
    else:
        zid=st.selectbox("Select zone",s.zone_id.tolist());r=s.loc[s.zone_id==zid].iloc[0]
        a,b,c,e,f=st.columns(5);a.metric("Priority",f'{r.response_priority_score:.1f}/100');b.metric("Band",r.risk_band);c.metric("Response readiness",f'{r.response_readiness_pct:.0f}%');e.metric("24h rainfall",f'{r.rainfall_24h_mm:.0f} mm');f.metric("Top driver",r.top_driver)
        vals={"24h rainfall":f"{r.rainfall_24h_mm:.0f} mm","6h rainfall":f"{r.rainfall_6h_mm:.0f} mm","Elevation risk":f"{r.elevation_risk_pct:.0f}%","Low-lying exposure":f"{r.low_lying_pct:.0f}%","Drainage capacity":f"{r.drainage_capacity_pct:.0f}%","Drain clearance":f"{r.drain_clearance_pct:.0f}%","Road importance":f"{r.road_importance_pct:.0f}%","Road blockage":f"{r.road_blockage_pct:.0f}%","Citizen reports":f"{r.report_count:.0f}","Response distance":f"{r.response_distance_km:.1f} km"}
        l,rr=st.columns(2)
        with l: st.dataframe(pd.DataFrame({"Signal":list(vals),"Value":list(vals.values())}),use_container_width=True,hide_index=True)
        with rr:
            for rec in generate_recommendations(r):st.markdown(f'<div class="card" style="margin:6px 0">{html.escape(rec)}</div>',unsafe_allow_html=True)
        comp=pd.DataFrame({"factor":["Rainfall","Elevation","Drainage","Roads","Citizen reports","Drain clearance","Response gap","Facilities","History"],"risk":[r.rainfall_component,r.elevation_component,r.drainage_component,r.road_component,r.citizen_component,r.clearance_component,r.response_component,r.facility_component,r.history_component]})
        fig=px.bar(comp,x="factor",y="risk",color="factor",text="risk");fig.update_traces(texttemplate="%{text:.1f}",textposition="outside");fig.update_layout(height=390,showlegend=False);st.plotly_chart(fig,use_container_width=True)

elif page=="Waterlogging Landscape":
    st.markdown("## Waterlogging-risk landscape")
    fig=px.scatter(s,x="rainfall_24h_mm",y="elevation_risk_pct",size="population_exposure",color="risk_band",hover_name="zone_name",hover_data=["area","top_driver","drainage_capacity_pct","road_blockage_pct","report_count"],labels={"rainfall_24h_mm":"24h rainfall (mm)","elevation_risk_pct":"Elevation exposure %"})
    fig.update_layout(height=520);st.plotly_chart(fig,use_container_width=True)
    st.dataframe(s.nlargest(25,"response_priority_score")[["zone_id","zone_name","area","response_priority_score","risk_band","top_driver"]],use_container_width=True,hide_index=True)

elif page=="Drainage & Clearing":
    st.markdown("## Drainage & clearing")
    q=build_signal_summary(s);l,r=st.columns(2)
    with l:
        fig=px.bar(q.sort_values("value_pct"),x="value_pct",y="signal",orientation="h",text="value_pct",color="value_pct");fig.update_traces(texttemplate="%{text:.0f}%",textposition="outside");fig.update_layout(height=460,showlegend=False);st.plotly_chart(fig,use_container_width=True)
    with r:
        cols=["zone_id","zone_name","area","drain_clearance_pct","drainage_capacity_pct","response_priority_score","risk_band","top_driver"];st.dataframe(s.sort_values("drain_clearance_pct")[cols],use_container_width=True,hide_index=True)

elif page=="Roads & Critical Facilities":
    st.markdown("## Roads & critical facilities")
    l,r=st.columns(2)
    with l:
        fig=px.scatter(s,x="road_importance_pct",y="road_blockage_pct",size="critical_facilities",color="risk_band",hover_name="zone_name",labels={"road_importance_pct":"Road importance %","road_blockage_pct":"Blockage %"})
        fig.update_layout(height=450);st.plotly_chart(fig,use_container_width=True)
    with r:
        st.dataframe(s.nlargest(25,"facility_component")[["zone_id","zone_name","area","critical_facilities","population_exposure","road_importance_pct","road_blockage_pct","response_priority_score","risk_band"]],use_container_width=True,hide_index=True)

elif page=="Team Dispatch":
    st.markdown("## Response team dispatch")
    l,r=st.columns(2);team=build_response_team_summary(s)
    with l:
        fig=px.bar(team.sort_values("priority"),x="priority",y="area",orientation="h",text="priority",color="readiness",labels={"priority":"Average priority","area":"Area","readiness":"Team readiness"});fig.update_traces(texttemplate="%{text:.1f}",textposition="outside");fig.update_layout(height=450);st.plotly_chart(fig,use_container_width=True)
    with r:
        st.dataframe(s.sort_values(["response_priority_score","response_distance_km"],ascending=[False,True])[["zone_id","zone_name","area","response_priority_score","response_readiness_pct","response_team_readiness_pct","response_distance_km","top_driver"]],use_container_width=True,hide_index=True)

elif page=="Scenario Lab":
    st.markdown("## Scenario Lab");st.caption("Planning simulation only — not an official flood forecast or emergency guarantee.")
    c=st.columns(3);rain=c[0].slider("Rainfall pressure",0,100,45);elev=c[1].slider("Low-elevation exposure",0,100,35);drain=c[2].slider("Drainage gap",0,100,35)
    c=st.columns(3);road=c[0].slider("Road/blockage",0,100,30);cit=c[1].slider("Citizen reports",0,100,25);clear=c[2].slider("Drain-clearance gap",0,100,30)
    c=st.columns(3);resp=c[0].slider("Response gap",0,100,20);fac=c[1].slider("Critical facilities",0,100,20);hist=c[2].slider("Historical signal",0,100,15)
    score=scenario_score(rain,elev,drain,road,cit,clear,resp,fac,hist)
    st.markdown(f'<div class="card"><div class="lab">Scenario output</div><div class="kpi">{score:.1f}/100</div><div class="small">{classify_score(score)} modeled response priority</div></div>',unsafe_allow_html=True)

elif page=="Citizen Report Log":
    ev=d["reports"].copy()
    if area!="All":ev=ev[ev.zone_id.isin(s.zone_id.tolist())]
    st.markdown("## Citizen report log");st.dataframe(ev,use_container_width=True,hide_index=True);st.download_button("Download citizen reports CSV",ev.to_csv(index=False).encode(),"floodops_citizen_reports.csv","text/csv")

else:
    st.markdown("## Data & export")
    tabs=st.tabs(["Screened results","Zones","History","Citizen reports"])
    with tabs[0]:
        st.dataframe(s,use_container_width=True,hide_index=True);st.download_button("Download screened results CSV",s.to_csv(index=False).encode(),"floodops_screened_results.csv","text/csv")
    with tabs[1]:st.dataframe(d["zones"],use_container_width=True,hide_index=True)
    with tabs[2]:st.dataframe(d["history"],use_container_width=True,hide_index=True)
    with tabs[3]:st.dataframe(d["reports"],use_container_width=True,hide_index=True)
