<#
install_backup_task.ps1

用途：在 Windows 上註冊一個排程工作執行 backup_hs_bg.ps1
參數：
 -TaskName       : 工作名稱
 -Frequency      : 'Daily'（目前僅支援 Daily）
 -DaysInterval   : 每 N 天執行（1 = 每日，3 = 每三天）
 -ScriptPath     : 要執行的 backup script 完整路徑
 -ScriptArgs     : 傳給 script 的參數字串（可選）
 -RunAsUser      : 執行帳戶（預設：當前使用者）
 -RunWithHighest : 是否以最高權限執行（需管理員）
#>
param(
    [Parameter(Mandatory=$true)][string] $TaskName,
    [Parameter(Mandatory=$true)][ValidateSet('Daily')][string] $Frequency,
    [int] $DaysInterval = 1,
    [Parameter(Mandatory=$true)][string] $ScriptPath,
    [string] $ScriptArgs = "",
    [string] $RunAsUser = "$env:USERNAME",
    [switch] $RunWithHighest
)

function Write-Log { param($m) Write-Host "[task] $m" }

try {
    if (-not (Test-Path $ScriptPath)) { throw "Script not found: $ScriptPath" }

    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File \"$ScriptPath\" $ScriptArgs"
    $trigger = New-ScheduledTaskTrigger -Daily -DaysInterval $DaysInterval -At 03:00AM
    $principal = New-ScheduledTaskPrincipal -UserId $RunAsUser -LogonType Interactive
    if ($RunWithHighest) { $principal.RunLevel = 'Highest' }

    $task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries)

    Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force
    Write-Log "Registered scheduled task: $TaskName (Every $DaysInterval day(s))"
    exit 0
} catch {
    Write-Host "[task] ERROR: $($_.Exception.Message)"
    exit 1
}
