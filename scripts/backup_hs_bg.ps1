<#
backup_hs_bg.ps1

用途：備份指定資料夾到目標資料夾，會建立以時間標記的壓縮檔或目錄，並自動刪除超過保留天數的備份。
參數：
 -SourcePaths    : array of paths to back up
 -DestRoot       : root folder to store backups (required)
 -RetentionDays  : keep backups for N days (default 30)
 -Compress       : switch, if set create .zip archives; otherwise copy folders
 -Verbose        : show more logs
#>
param(
    [Parameter(Mandatory=$true)] [string[]] $SourcePaths,
    [Parameter(Mandatory=$true)] [string] $DestRoot,
    [int] $RetentionDays = 30,
    [switch] $Compress
)

function Write-Log { param($m) Write-Host "[backup] $m" }

try {
    $timestamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
    if (-not (Test-Path $DestRoot)) { New-Item -ItemType Directory -Path $DestRoot -Force | Out-Null }

    $backupName = "hs_bg_backup_$timestamp"
    if ($Compress) {
        $tempDir = Join-Path $Env:TEMP $backupName
        if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
        New-Item -ItemType Directory -Path $tempDir | Out-Null

        foreach ($p in $SourcePaths) {
            if (Test-Path $p) {
                $dest = Join-Path $tempDir (Split-Path $p -Leaf)
                Write-Log "Copying $p -> $dest"
                Copy-Item -Path $p -Destination $dest -Recurse -Force -ErrorAction Stop
            } else {
                Write-Log "Source not found: $p"
            }
        }

        $zipPath = Join-Path $DestRoot ("$backupName.zip")
        Write-Log "Creating archive: $zipPath"
        if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
        Compress-Archive -Path (Join-Path $tempDir '*') -DestinationPath $zipPath -Force
        Remove-Item $tempDir -Recurse -Force
        Write-Log "Backup created: $zipPath"
    } else {
        $outDir = Join-Path $DestRoot $backupName
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
        foreach ($p in $SourcePaths) {
            if (Test-Path $p) {
                $dest = Join-Path $outDir (Split-Path $p -Leaf)
                Write-Log "Copying $p -> $dest"
                Copy-Item -Path $p -Destination $dest -Recurse -Force -ErrorAction Stop
            } else {
                Write-Log "Source not found: $p"
            }
        }
        Write-Log "Backup folder created: $outDir"
    }

    # 刪除舊備份
    if ($RetentionDays -gt 0) {
        Write-Log "Pruning backups older than $RetentionDays days..."
        $cutoff = (Get-Date).AddDays(-$RetentionDays)
        Get-ChildItem -Path $DestRoot -File -Filter 'hs_bg_backup_*.zip' -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt $cutoff} | ForEach-Object {
            Write-Log "Deleting old archive: $($_.FullName)"; Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
        }
        Get-ChildItem -Path $DestRoot -Directory -Filter 'hs_bg_backup_*' -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -lt $cutoff} | ForEach-Object {
            Write-Log "Deleting old folder: $($_.FullName)"; Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Log "Done."
    exit 0
} catch {
    Write-Host "[backup] ERROR: $($_.Exception.Message)"
    exit 1
}
