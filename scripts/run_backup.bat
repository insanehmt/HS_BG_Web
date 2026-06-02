@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "F:\GitHub_Copilot\HS_BattleGrounds\scripts\backup_hs_bg.ps1" -SourcePaths @('F:\GitHub_Copilot\HS_BattleGrounds\data','F:\GitHub_Copilot\HS_BattleGrounds\output') -DestRoot 'D:\HS_BG_Backups' -Compress -RetentionDays 30
