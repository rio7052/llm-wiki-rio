# install-hourly-log.ps1 — hourly-log.ps1 을 Windows 작업 스케줄러에 등록 (2026-08-22)
#
# CLAUDE.md §7.11. 세션 로그 적재를 매 시간 무인 실행한다.
# Claude Code 내장 cron 은 **세션이 살아있는 동안만** 돌고 7일 후 만료되므로,
# 상시 동작하려면 OS 스케줄러에 걸어야 한다.
#
# 사용:
#   powershell -File tools/install-hourly-log.ps1            # 등록 (매 정각, 24시간)
#   powershell -File tools/install-hourly-log.ps1 -WorkHours # 08~23시만
#   powershell -File tools/install-hourly-log.ps1 -Remove    # 등록 해제
#   powershell -File tools/install-hourly-log.ps1 -Status    # 상태·최근 실행 확인
#
# 주의: 로그온 상태에서만 실행된다(Claude CLI 가 사용자 프로필의 인증을 쓰므로).
#       비밀번호를 저장하지 않으려는 의도적 선택이다.

param(
    [switch]$Remove,
    [switch]$Status,
    [switch]$WorkHours,
    [int]$Minute = 0             # 매 정각 (2026-08-22 Kevin 지정). -Minute 으로 조정 가능
)

$ErrorActionPreference = 'Stop'
$wiki   = Split-Path -Parent $PSScriptRoot
$script = Join-Path $wiki 'tools\hourly-log.ps1'
$name   = 'LlmWiki-HourlyLog'

if ($Status) {
    $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if (-not $t) { Write-Host "등록 안 됨 ($name)"; exit 0 }
    $i = Get-ScheduledTaskInfo -TaskName $name
    Write-Host "작업: $name / 상태: $($t.State)"
    Write-Host "마지막 실행: $($i.LastRunTime)  결과: $($i.LastTaskResult)  다음: $($i.NextRunTime)"
    $runlog = Join-Path $wiki '.log-runs.log'
    if (Test-Path $runlog) {
        Write-Host "`n--- 최근 실행 로그 ---"
        Get-Content $runlog -Tail 10
    }
    exit 0
}

if ($Remove) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "등록 해제: $name"
    exit 0
}

if (-not (Test-Path $script)) { Write-Error "not found: $script"; exit 1 }

# 매시 $Minute 분에 실행. 하루 종일 도는 게 기본 — 활동이 없으면 LLM 호출 없이 즉시 끝나므로
# 밤·주말에 돌아도 비용이 들지 않는다. 새벽·주말 작업도 놓치지 않는 게 설계 의도다.
$startHour = if ($WorkHours) { 8 } else { 0 }
$span      = if ($WorkHours) { (New-TimeSpan -Hours 16) } else { (New-TimeSpan -Days 1) }

$trigger = New-ScheduledTaskTrigger -Once -At ([datetime]::Today.AddHours($startHour).AddMinutes($Minute)) `
    -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration $span

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$script`"" `
    -WorkingDirectory $wiki

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -MultipleInstances IgnoreNew          # 이전 실행이 안 끝났으면 건너뛴다

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName $name -Trigger $trigger -Action $action `
    -Settings $settings -Principal $principal -Force `
    -Description '개인 LLM wiki — 매 시간 Claude Code 세션에서 한 일을 일일 리포트에 적재 (CLAUDE.md §7.11)' | Out-Null

$scope = if ($WorkHours) { "08~23시" } else { "24시간" }
$when = if ($Minute -eq 0) { "매 정각" } else { "매시 ${Minute}분" }
Write-Host "등록 완료: $name — $when / $scope / 로그온 중일 때만"
Write-Host "상태 확인: powershell -File tools/install-hourly-log.ps1 -Status"
Write-Host "해제:      powershell -File tools/install-hourly-log.ps1 -Remove"
