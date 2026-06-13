@echo off
echo ===== Push to GitHub (SSH) =====
cd /d F:\GitHub_Copilot\HS_BattleGrounds
if exist .git\index.lock del .git\index.lock
if exist .git\HEAD.lock del .git\HEAD.lock
if exist .git\refs\heads\main.lock del .git\refs\heads\main.lock
git add web\templates\admin.html
git commit -m "fix: pin Alpine.js version, add button fallback text"
git push insanehmt HEAD:main
echo Exit code: %ERRORLEVEL%
pause
