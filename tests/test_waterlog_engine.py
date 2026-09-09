import pandas as pd
from waterlog_engine import *
def load():
    D='data'
    return pd.read_csv(f'{D}/sample_waterlogging_zones.csv'),pd.read_csv(f'{D}/sample_waterlogging_history.csv'),pd.read_csv(f'{D}/sample_citizen_reports.csv')
def test_bands():
    assert classify_score(0)=='Low'; assert classify_score(25)=='Moderate'; assert classify_score(50)=='High'; assert classify_score(75)=='Critical'
def test_screening():
    z,h,r=load();o=build_response_screening(z,h,r);assert len(o)==28;assert o.response_priority_score.between(0,100).all();assert o.response_readiness_pct.between(0,100).all();assert o.top_driver.notna().all()
def test_scenario_bounds():
    assert 0<=scenario_score(100,100,100,100,100,100,100,100,100)<=100
def test_missing_column_rejected():
    z,h,r=load();z=z.drop(columns=['road_importance_pct'])
    try: build_response_screening(z,h,r)
    except ValueError as e: assert 'road_importance_pct' in str(e)
    else: raise AssertionError('Expected validation error')
