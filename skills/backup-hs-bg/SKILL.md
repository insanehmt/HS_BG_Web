---
name: backup-hs-bg
description: "備份 HS_BattleGrounds：包含立即備份腳本與 Windows 排程安裝腳本，支援每日或每 3 天備份與保留策略。"
metadata:
  {
    "emoji": "💾",
  }
---

# Backup HS_BattleGrounds Skill

用途：透過內建 PowerShell 腳本完成備份，並提供註冊 Windows Scheduled Task 的 helper。

Commands / Examples:

- 立即備份：
  powershell -File .\\scripts\\backup_hs_bg.ps1 -SourcePaths @('.\\data', '.\\output') -DestRoot 'D:\\HS_BG_Backups' -Compress -RetentionDays 30

- 建立每日排程：
  powershell -File .\\scripts\\install_backup_task.ps1 -TaskName 'HS_BG_Backup_Daily' -Frequency Daily -DaysInterval 1 -ScriptPath "F:\\GitHub_Copilot\\HS_BattleGrounds\\scripts\\backup_hs_bg.ps1" -ScriptArgs "-SourcePaths @('F:\\GitHub_Copilot\\HS_BattleGrounds\\data','F:\\GitHub_Copilot\\HS_BattleGrounds\\output') -DestRoot 'D:\\HS_BG_Backups' -Compress -RetentionDays 30" -RunWithHighest

Notes:
- 建議目的地使用外接硬碟或另一顆磁碟以避免重啟/重部署遺失。
- 若使用 Linux/macOS，請自行以 tar/rsync 建立對應腳本。