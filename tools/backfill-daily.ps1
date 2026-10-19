# backfill-daily.ps1 — 세션 기록에서 과거 일일 리포트를 사후 복원 (2026-08-22)
#
# 배경: 세션 미러·session-retro 가 멈춰 있던 동안(2026-07~08) 작업은 했는데 일일 리포트가
#       없는 날이 23일 생겼다. transcript 는 남아 있으므로 사실 기록은 복원할 수 있다.
#
# 한계(중요): **배운점·회고는 복원하지 않는다.** 그건 당시 Kevin 머릿속에만 있었고
#             세션 로그에 없다. 지어내면 거짓 기록이 되므로 빈 칸으로 두고 명시한다.
#
# 사용:
#   powershell -File tools/backfill-daily.ps1 -Dates 2026-08-14,2026-08-15
#   powershell -File tools/backfill-daily.ps1 -From 2026-07-07 -To 2026-08-17
#   powershell -File tools/backfill-daily.ps1 -From 2026-07-07 -To 2026-08-17 -DryRun
#
# 안전: 이미 있는 날짜 파일은 **건너뛴다**(§4.3 immutable). -Force 로도 덮어쓰지 않는다.

param(
    [string[]]$Dates,
    [string]$From,
    [string]$To,
    [switch]$DryRun,
    [string]$ClaudeExe = "$env:USERPROFILE\.local\bin\claude.exe"
)

$ErrorActionPreference = 'Stop'

# PS 5.1 은 native exe stdin 을 $OutputEncoding(기본 ASCII)으로 인코딩한다 — 고정 안 하면 한글 유실
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
$env:PYTHONIOENCODING = 'utf-8'

$wiki = Split-Path -Parent $PSScriptRoot
Set-Location $wiki
$runlog = Join-Path $wiki '.log-runs.log'

function Note($msg) {
    $line = "[{0}] backfill: {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Write-Host $line
    Add-Content -Path $runlog -Value $line -Encoding utf8
}

# ── 대상 날짜 확정 ────────────────────────────────────────────────
if (-not $Dates -and $From) {
    $d = [datetime]::ParseExact($From, 'yyyy-MM-dd', $null)
    $end = if ($To) { [datetime]::ParseExact($To, 'yyyy-MM-dd', $null) } else { (Get-Date).Date.AddDays(-1) }
    $Dates = @()
    while ($d -le $end) { $Dates += $d.ToString('yyyy-MM-dd'); $d = $d.AddDays(1) }
}
if (-not $Dates) { Write-Error "-Dates 또는 -From 을 지정하라"; exit 1 }

$made = 0; $skipExist = 0; $skipEmpty = 0; $failed = 0

foreach ($day in $Dates) {
    $target = Join-Path $wiki "raw\reports\daily\$day.md"
    if (Test-Path $target) { $skipExist++; continue }

    $digest = Join-Path $env:TEMP "backfill-$day.md"
    & python tools/session-digest.py --day $day --out $digest --max-user 30 | Out-Null
    if ($LASTEXITCODE -ne 0) { Note "$day digest 실패"; $failed++; continue }

    $body = Get-Content $digest -Raw -Encoding utf8
    if ($body -match '_이 구간에 활동 없음\._') {
        $skipEmpty++
        Remove-Item $digest -Force -ErrorAction SilentlyContinue
        continue
    }

    $dow = ([datetime]::ParseExact($day,'yyyy-MM-dd',$null)).ToString('ddd', [Globalization.CultureInfo]::GetCultureInfo('ko-KR'))
    Note "$day ($dow) — digest $($body.Length) chars"
    if ($DryRun) { Remove-Item $digest -Force -ErrorAction SilentlyContinue; continue }

    $prompt = @"
$day 에 여러 레포에서 Claude Code 로 한 작업의 digest 다. 이 날의 일일 리포트를
``raw/reports/daily/$day.md`` 로 **새로 만들어라**(백필 — 그날 리포트를 못 썼다).

frontmatter:
``type: report`` / ``report_kind: daily`` / ``period: $day`` / ``status: active`` /
``tags``(lowercase-kebab, 내용에 맞게) / ``last_updated: $day``

제목 다음 줄에 아래를 그대로 넣어라(사후 복원임을 밝히는 표시다):
> 세션 기록에서 사후 복원(백필). 당시 회고는 남아 있지 않아 사실 기록만 담았다.

본문 섹션: ``## 한 일`` / ``## 발견`` / ``## 결정`` / ``## 막힘``
- 명령을 나열하지 말고 **작업 단위로 묶어 한 문장씩**. 레포가 여럿이면 레포명을 접두로.
- 탐색·확인·실패 후 재시도 등 결과가 남지 않은 시행착오는 적지 않는다.
- 해당 섹션에 넣을 게 없으면 **그 섹션을 아예 만들지 마라**. 억지로 채우지 않는다.
- **마스킹(§9)**: 고객·개체 식별 정보, 계정·토큰, 급여·계약액 제거. digest 에는 마스킹이 안 돼 있다.
- 본문은 평어체.

**배운점·회고·내일은 쓰지 마라.** 그건 세션 로그에 없고 당시 사람 머릿속에만 있었다 —
추측해서 채우면 거짓 기록이 된다. 해당 섹션 자체를 만들지 않는다.

digest 가 부실하면 ``$digest`` 를 Read 로 직접 읽어라.
무인 실행이므로 **질문하지 말고** 판단해서 기록한 뒤 한 줄로만 보고하라.

--- digest ---
$body
"@

    $pf = Join-Path $env:TEMP "backfill-prompt-$day.txt"
    [System.IO.File]::WriteAllText($pf, $prompt, (New-Object System.Text.UTF8Encoding $false))

    try {
        $out = Get-Content $pf -Raw -Encoding utf8 | & $ClaudeExe -p `
            --permission-mode acceptEdits `
            --allowedTools 'Read' 'Edit' 'Write' 'Glob' 'Grep' 2>&1 | Out-String
        if (Test-Path $target) { $made++; Note "$day 생성됨" }
        else { $failed++; Note "$day 실패 — 파일 안 만들어짐: $($out.Trim() -split "`n" | Select-Object -Last 1)" }
    }
    catch { $failed++; Note "$day 예외: $_" }
    finally { Remove-Item $pf, $digest -Force -ErrorAction SilentlyContinue }
}

Note "완료 — 생성 $made / 이미있음 $skipExist / 활동없음 $skipEmpty / 실패 $failed"
exit 0
