<#
setup-audit.ps1 -- 打开 Windows 文件系统审计 + 给 data\game\*.dl_bin 挂 SACL（管理员）

目的：拿到「引擎/EAC 什么时候打开并读取哪些表」的客观时间线。
只做两件事：auditpol 打开 File System 的成功/失败审计；给 55 个 .dl_bin 加 ReadData 审计规则。
原始状态写入 _audit-state.json，teardown-audit.ps1 用它还原。
#>
$ErrorActionPreference = 'Stop'
$Game   = 'D:\SteamLibrary\steamapps\common\Helldivers 2'
$Root   = 'D:\mod\work\eac-audit'
$State  = Join-Path $Root '_audit-state.json'
$SubCat = '{0CCE921D-69AE-11D9-BED3-505054503030}'   # File System

New-Item -ItemType Directory -Force -Path $Root | Out-Null

# --- 1. 记录并打开审计策略 --------------------------------------------------
$before = (& auditpol.exe /get /subcategory:$SubCat) -join "`n"
Write-Host "=== auditpol BEFORE ==="
Write-Host $before
& auditpol.exe /set /subcategory:$SubCat /success:enable /failure:enable | Out-Null
$after = (& auditpol.exe /get /subcategory:$SubCat) -join "`n"
Write-Host "=== auditpol AFTER ==="
Write-Host $after

# --- 2. 给每个 .dl_bin 加 SACL -------------------------------------------------
$sid = New-Object System.Security.Principal.SecurityIdentifier(
           [System.Security.Principal.WellKnownSidType]::WorldSid, $null)
$files = Get-ChildItem (Join-Path $Game 'data\game') -Filter '*.dl_bin' | Sort-Object Name
$saved = @()
$ok = 0
foreach ($f in $files) {
    $acl = Get-Acl -LiteralPath $f.FullName -Audit
    $existing = @()
    foreach ($r in $acl.GetAuditRules($true, $false, [System.Security.Principal.SecurityIdentifier])) {
        $existing += @{ identity = $r.IdentityReference.Value; rights = "$($r.FileSystemRights)"; flags = "$($r.AuditFlags)" }
    }
    $saved += @{ path = $f.FullName; rules = $existing }

    $rule = New-Object System.Security.AccessControl.FileSystemAuditRule(
                $sid,
                [System.Security.AccessControl.FileSystemRights]::ReadData,
                [System.Security.AccessControl.InheritanceFlags]::None,
                [System.Security.AccessControl.PropagationFlags]::None,
                [System.Security.AccessControl.AuditFlags]::Success)
    $acl.AddAuditRule($rule)
    Set-Acl -LiteralPath $f.FullName -AclObject $acl
    $ok++
}

@{ auditpol_before = $before; auditpol_after = $after; subcategory = $SubCat
   files_audited = $ok; files = $saved
   created = (Get-Date).ToString('o') } |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $State -Encoding UTF8

# --- 3. 安全检查日志容量 -------------------------------------------------------
$log = Get-WinEvent -ListLog Security
Write-Host ("Security log: max {0:N0} KB, current {1:N0} KB, records {2:N0}" -f `
    ($log.MaximumSizeInBytes/1KB), ($log.FileSize/1KB), $log.RecordCount)

Write-Host "AUDIT SETUP OK: $ok file(s) with ReadData SACL; state -> $State"
