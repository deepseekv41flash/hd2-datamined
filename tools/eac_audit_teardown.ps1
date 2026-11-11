<#
teardown-audit.ps1 -- 还原审计策略与 SACL（管理员）

读 _audit-state.json：把 File System 子类恢复成采集到的原始设置，并移除我们加的 ReadData 审计规则。
#>
$ErrorActionPreference = 'Stop'
$Root  = 'D:\mod\work\eac-audit'
$State = Join-Path $Root '_audit-state.json'
if (-not (Test-Path $State)) { throw "state file missing: $State" }
$s = Get-Content -LiteralPath $State -Raw | ConvertFrom-Json

$sid = New-Object System.Security.Principal.SecurityIdentifier(
           [System.Security.Principal.WellKnownSidType]::WorldSid, $null)

$removed = 0
foreach ($f in $s.files) {
    if (-not (Test-Path -LiteralPath $f.path)) { continue }
    $acl = Get-Acl -LiteralPath $f.path -Audit
    $keep = @()
    foreach ($r in $acl.GetAuditRules($true, $false, [System.Security.Principal.SecurityIdentifier])) {
        if ($r.IdentityReference.Value -eq $sid.Value -and
            "$($r.FileSystemRights)" -eq 'ReadData' -and
            "$($r.AuditFlags)" -eq 'Success') {
            $keep += $r
        }
    }
    foreach ($r in $keep) { $acl.RemoveAuditRule($r) | Out-Null; $removed++ }
    Set-Acl -LiteralPath $f.path -AclObject $acl
}

$orig = $s.auditpol_before
$succ = if ($orig -match 'Success\s+and\s+Failure') { '/success:enable /failure:enable' }
        elseif ($orig -match 'Success') { '/success:enable /failure:disable' }
        elseif ($orig -match 'Failure') { '/success:disable /failure:enable' }
        else { '/success:disable /failure:disable' }
& auditpol.exe /set /subcategory:$($s.subcategory) $succ.Split(' ') | Out-Null

Write-Host "TEARDOWN OK: removed $removed audit rule(s); auditpol restored -> $succ"
Write-Host ((& auditpol.exe /get /subcategory:$($s.subcategory)) -join "`n")
