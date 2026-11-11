<#
collect-audit.ps1 -- 从安全日志里抽出 .dl_bin 的访问事件（管理员）

输出
  access-events.csv   每行：EventTime, EventId, ObjectName, ProcessId, ProcessName, AccessMask, AccessReason
  access-summary.txt  按「文件 × 进程 × 秒」聚合的读取时间线

用法
  .\collect-audit.ps1 [-Since '2026-11-11 21:20:00'] [-Minutes 10]
#>
[CmdletBinding()]
param(
    [string]$Since,
    [int]$Minutes = 15,
    [string]$Root = 'D:\mod\work\eac-audit'
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $Root | Out-Null

if ($Since) { $start = [datetime]::Parse($Since) } else { $start = (Get-Date).AddMinutes(-$Minutes) }
Write-Host "window: $($start.ToString('HH:mm:ss.fff')) -> now"

$pattern = 'generated_[A-Za-z0-9_]+\.dl_bin'
$rows = New-Object System.Collections.Generic.List[object]

$events = Get-WinEvent -FilterHashtable @{ LogName = 'Security'; Id = 4663, 4656; StartTime = $start } -ErrorAction SilentlyContinue
Write-Host "raw events fetched: $(@($events).Count)"

foreach ($e in @($events)) {
    if ($e.Message -notmatch $pattern) { continue }
    $xml = [xml]$e.ToXml()
    $d = @{}
    foreach ($n in $xml.Event.EventData.Data) { $d[$n.Name] = $n.'#text' }
    $obj = $d['ObjectName']
    if ($obj -notmatch $pattern) { continue }
    $rows.Add([pscustomobject]@{
        Time         = $e.TimeCreated.ToString('HH:mm:ss.fff')
        EventId      = $e.Id
        ObjectName   = $obj
        ProcessId    = $d['ProcessId']
        ProcessName  = $d['ProcessName']
        AccessMask   = $d['AccessMask']
        AccessReason = $d['AccessReason']
        Subject      = $d['SubjectUserName']
    })
}

$rows | Sort-Object Time | Export-Csv -LiteralPath (Join-Path $Root 'access-events.csv') -NoTypeInformation -Encoding UTF8
Write-Host "kept events: $($rows.Count) -> access-events.csv"

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("window $($start.ToString('HH:mm:ss.fff')) -> now")
[void]$sb.AppendLine("total kept: $($rows.Count)")
[void]$sb.AppendLine('')
[void]$sb.AppendLine('time         evt pid    process                 wmask   file')
foreach ($r in ($rows | Sort-Object Time)) {
    $file = [System.IO.Path]::GetFileName($r.ObjectName)
    [void]$sb.AppendLine(("{0}  {1} {2,-6} {3,-22} {4,-7} {5}" -f $r.Time, $r.EventId, $r.ProcessId, $r.ProcessName, $r.AccessMask, $file))
}
Set-Content -LiteralPath (Join-Path $Root 'access-summary.txt') -Value $sb.ToString() -Encoding UTF8
Write-Host 'wrote access-summary.txt'
