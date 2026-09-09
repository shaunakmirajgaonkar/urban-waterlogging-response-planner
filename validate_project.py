from pathlib import Path
import pandas as pd
from waterlog_engine import build_response_screening, scenario_score, BANDS
D=Path(__file__).resolve().parent/'data'
o=build_response_screening(pd.read_csv(D/'sample_waterlogging_zones.csv'),pd.read_csv(D/'sample_waterlogging_history.csv'),pd.read_csv(D/'sample_citizen_reports.csv'))
assert len(o)==28
assert o.response_priority_score.between(0,100).all()
assert o.response_readiness_pct.between(0,100).all()
assert set(o.risk_band).issubset(set(BANDS))
assert 0<=scenario_score(100,100,100,100,100,100,100,100,100)<=100
print('PASS: FloodOps validation')
print(f'Zones: {len(o)}')
print(f'Areas: {o.area.nunique()}')
print(f'Average priority score: {o.response_priority_score.mean():.1f}')
print(f'High/Critical: {int(o.risk_band.isin(["High","Critical"]).sum())}')
