```bash
cd ~/Downloads/UrbanWaterloggingResponsePlanner_FloodOps_Local
rm -rf .git
git init
git branch -M main
git add -A
git status
git commit -m "feat: add FloodOps urban waterlogging response planner"
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/shaunakmirajgaonkar/urban-waterlogging-response-planner.git
git push -u origin main --force
```
