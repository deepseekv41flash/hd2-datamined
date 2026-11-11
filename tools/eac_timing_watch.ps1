<#
eac_timing_watch.ps1 -- 客观时间戳记录器（纯用户态，不接触游戏进程）

记录
  * helldivers2.exe 出现 / 消失的时刻
  * 期间出现的**新**顶层窗口（标题 + 所属 PID），用来抓 EAC 弹窗出现的精确时刻
  * EAC 启动器日志里 "game window has become visible" 首次出现的时刻（做时钟对齐）

用法
  powershell -NoProfile -ExecutionPolicy Bypass -File .\eac_timing_watch.ps1 -Seconds 600 -Out timing.log

输出每行：本地时间(毫秒) 事件 详情
#>
[CmdletBinding()]
param(
    [int]$Seconds = 600,
    [string]$Out = 'eac-timing.log',
    [string]$ProcessName = 'helldivers2'
)

$ErrorActionPreference = 'Continue'

Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class Win {
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassNameW(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);

    public static List<string> Snapshot() {
        var list = new List<string>();
        EnumWindows((h, l) => {
            if (!IsWindowVisible(h)) return true;
            var t = new StringBuilder(512);
            GetWindowTextW(h, t, 512);
            var c = new StringBuilder(256);
            GetClassNameW(h, c, 256);
            uint pid; GetWindowThreadProcessId(h, out pid);
            string title = t.ToString().Replace("\r", " ").Replace("\n", " ");
            if (title.Length == 0) return true;
            list.Add(pid + "\t" + c.ToString() + "\t" + title);
            return true;
        }, IntPtr.Zero);
        return list;
    }
}
"@

function Stamp { (Get-Date).ToString('HH:mm:ss.fff') }
function Note([string]$msg) { Add-Content -LiteralPath $Out -Value "$(Stamp) $msg" -Encoding UTF8 }

# EAC 保护进程时 [Diagnostics.Process] 会卡死（实测卡 2 分钟），改用 tasklist 子进程查询。
function Get-TargetPids {
    $raw = & tasklist.exe /nh /fo csv /fi "IMAGENAME eq $ProcessName.exe" 2>$null
    $ids = @()
    foreach ($line in @($raw)) {
        if ($line -match ('^"' + [regex]::Escape($ProcessName) + '\.exe","(\d+)"')) { $ids += [int]$Matches[1] }
    }
    return $ids
}

$eacLog = Get-ChildItem -Path "$env:APPDATA\EasyAntiCheat" -Recurse -Filter 'anticheatlauncher.log' -ErrorAction SilentlyContinue |
          Select-Object -First 1

Set-Content -LiteralPath $Out -Value "# start $(Get-Date -Format o)" -Encoding UTF8
Note "watching '$ProcessName' for $Seconds s"

$seenTitles = New-Object 'System.Collections.Generic.HashSet[string]'
$wasRunning = $false
$started = $null
$lastRun = $null
$launcherSaidVisible = $false
$appeared = $false
$deadline = (Get-Date).AddSeconds($Seconds)

while ((Get-Date) -lt $deadline) {
    $pids = @(Get-TargetPids)
    $running = $pids.Count -gt 0
    if ($running -and -not $wasRunning) {
        $started = Get-Date
        $appeared = $true
        Note "PROC START $ProcessName pid=$($pids -join ',')"
    }
    if (-not $running -and $wasRunning) {
        $lastRun = Get-Date
        Note "PROC EXIT  $ProcessName  session=$([math]::Round(($lastRun - $started).TotalSeconds,2))s"
        break
    }
    $wasRunning = $running

    foreach ($line in [Win]::Snapshot()) {
        if ($seenTitles.Add($line)) {
            $t = ($line -split "`t")[2]
            if ($t -match 'Easy Anti-Cheat|Anti-Cheat|未知|Unknown|Error|错误') { Note "POPUP?  $line" }
            else { Note "window  $line" }
        }
    }

    if ($eacLog -and -not $launcherSaidVisible) {
        $hit = Select-String -LiteralPath $eacLog.FullName -Pattern 'window has become visible' -ErrorAction SilentlyContinue | Select-Object -Last 1
        if ($hit) {
            $launcherSaidVisible = $true
            Note "EAC-LOG window-visible line present (log ts: $($hit.Line.Substring(0,[Math]::Min(24,$hit.Line.Length))))"
        }
    }

    Start-Sleep -Milliseconds 100
}

if (-not $appeared) { Note "never saw $ProcessName" }
Note 'done'
