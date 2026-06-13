@echo off
echo ===== SSH Test & Push =====
cd /d F:\GitHub_Copilot\HS_BattleGrounds

echo [1] SSH auth test:
ssh -T git@github.com
echo SSH exit code: %ERRORLEVEL%

echo.
echo [2] Updating remote URL to SSH...
git remote set-url insanehmt git@github.com:insanehmt/HS_BG_Web.git
git remote -v

echo.
echo [3] Test push (should say "Everything up-to-date" or succeed):
git push insanehmt HEAD:main
echo Push exit code: %ERRORLEVEL%

pause
