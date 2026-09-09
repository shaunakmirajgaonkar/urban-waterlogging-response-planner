# FloodOps — Urban Waterlogging Response Planner

100% local-first Streamlit dashboard for waterlogging-response prioritization, drainage-clearing, citizen-report triage, road exposure, critical-facility exposure, team dispatch, scenario analysis, and CSV export.

## Run on macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 validate_project.py
python3 -m pytest -q
python3 run.py
```
Open http://localhost:8501.

All sample records are synthetic. Scores are operational screening signals, not official flood forecasts or emergency guarantees.
