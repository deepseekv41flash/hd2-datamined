<#
cleanup-audit-sacl.ps1 -- 移除我们加的 ReadData/ListDirectory 审计规则（管理员）

teardown 时用的是 .NET 的枚举字符串 "ReadData"，实际回读出来是 "ListDirectory"（同值 0x1 的别名），
所以那一轮没删掉。这里按 SID + Success + 两者之一来匹配，删完回读确认。
#>
$ErrorActionPreference = 'Stop'
$Root = 'D:\mod\work\eac-audit'
$Out  = Join-Path $Root 'audit-sacl-cleanup.txt'
$sid  = New-Object System.Security.Principal.SecurityIdentifier(
            [System.Security.Principal.WellKnownSidType]::WorldSid, $null)
$rights = @('ReadData', 'ListDirectory')

$lines = New-Object System.Collections.Generic.List[string]
$files = Get-ChildItem 'D:\SteamLibrary\steamapps\common\Helldivers 2\data\game' -Filter '*.dl_bin'
$removed = 0
foreach ($f in $files) {
    $acl = Get-Acl -LiteralPath $f.FullName -Audit
    $drop = @()
    foreach ($r in $acl.GetAuditRules($true, $false, [System.Security.Principal.SecurityIdentifier])) {
        if ($r.IdentityReference.Value -eq $sid.Value -and
            $rights -contains "$($r.FileSystemRights)" -and
            "$($r.AuditFlags)" -eq 'Success') {
            $drop += $r
        }
    }
    if ($drop.Count -eq 0) { continue }
    foreach ($r in $drop) { $acl.RemoveAuditRule($r) | Out-Null; $removed++ }
    Set-Acl -LiteralPath $f.FullName -AclObject $acl
}
$lines.Add("removed audit rule(s): $removed")

$sample = @('generated_zone_data.dl_bin', 'generated_entities.dl_bin')
foreach ($n in $sample) {
    $p = "D:\SteamLibrary\steamapps\common\Helldivers 2\data\game\$n"
    $acl = Get-Acl -LiteralPath $p -Audit
    $left = @()
    foreach ($r in $acl.GetAuditRules($true, $false, [System.Security.Principal.SecurityIdentifier])) {
        $left += ("{0} {1} {2}" -f $r.IdentityReference.Value, $r.FileSystemRights, $r.AuditFlags)
    }
    $summary = '<none>'
    if ($left.Count -gt 0) { $summary = $left -join '; ' }
    $lines.Add("$n -> $summary")
}
$lines | Set-Content -LiteralPath $Out -Encoding UTF8
Write-Host "wrote $Out"
