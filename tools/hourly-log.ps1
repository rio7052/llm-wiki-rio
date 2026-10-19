# hourly-log.ps1 — 매 시간 세션에서 한 일을 뽑아 오늘 일일 리포트에 적재 (2026-08-22)
#
# CLAUDE.md §7.11 (Session capture) 의 무인 실행판. `/log` 를 사람이 안 쳐도 돌게 한다.
#
# 설계: 결정적인 부분(세션 digest 추출)은 PowerShell 이, 판단이 필요한 부분(합성·배치)만
#       Claude 가 한다. 덕분에 Claude 에게 파일 편집 권한만 주면 되고 Bash 권한이 필요 없다.
#
# 비용: 활동이 없는 시간대엔 **LLM 을 아예 호출하지 않는다**(digest 가 비면 즉시 종료).
#
# 사용:
#   powershell -File tools/hourly-log.ps1              # 커서 이후 (기본)
#   powershell -File tools/hourly-log.ps1 -SinceHours 6
#   powershell -File tools/hourly-log.ps1 -DryRun      # digest 만 보고 Claude 호출 안 함
#
# 설치(작업 스케줄러 등록): powershell -File tools/install-hourly-log.ps1

param(
    [double]$SinceHours = 0,
    [switch]$DryRun,
    [string]$ClaudeExe = "$env:USERPROFILE\.local\bin\claude.exe"
)

$ErrorActionPreference = 'Stop'

# PowerShell 5.1 은 native exe 로 파이프할 때 $OutputEncoding(기본 ASCII)으로 인코딩한다 —
# 고정하지 않으면 한글이 전부 '?' 로 유실된다 (2026-08-22 첫 실전 실행에서 실측).
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
$env:PYTHONIOENCODING = 'utf-8'

$wiki = Split-Path -Parent $PSScriptRoot
Set-Location $wiki

$cursor  = Join-Path $wiki '.log-cursor'
$runlog  = Join-Path $wiki '.log-runs.log'
$digest  = Join-Path $env:TEMP ("wiki-digest-{0}.md" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))

function Note($msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
    Write-Host $line
    Add-Content -Path $runlog -Value $line -Encoding utf8
}

# ── 1. digest 추출 (결정적, LLM 없음) ─────────────────────────────
$dargs = @('tools/session-digest.py')
if ($SinceHours -gt 0) { $dargs += @('--since-hours', $SinceHours) }
elseif (Test-Path $cursor) { $dargs += @('--since-file', $cursor) }
else { $dargs += @('--since-hours', '12') }   # 첫 실행
$dargs += @('--out', $digest)

& python @dargs | Out-Null
if ($LASTEXITCODE -ne 0) { Note "digest 실패 (exit $LASTEXITCODE)"; exit 1 }

$body = Get-Content $digest -Raw -Encoding utf8
if ($body -match '_이 구간에 활동 없음\._') {
    Note "활동 없음 — 건너뜀 (LLM 호출 안 함)"
    Remove-Item $digest -Force -ErrorAction SilentlyContinue
    [System.IO.File]::WriteAllText($cursor, (Get-Date).ToUniversalTime().ToString('o'), (New-Object System.Text.UTF8Encoding $false))
    exit 0
}

$sessions = ([regex]::Matches($body, '(?m)^## ')).Count
Note "digest: 세션 $sessions 개 / $($body.Length) chars"

if ($DryRun) { Write-Host $body; Note "DryRun — Claude 호출 안 함"; exit 0 }

# ── 2. Claude 에게 합성·적재만 시킨다 ─────────────────────────────
$today = Get-Date -Format 'yyyy-MM-dd'
$prompt = @"
아래는 마지막 기록 이후 내가 여러 레포에서 Claude Code 로 한 작업의 digest 다.
이것을 오늘 일일 리포트 ``raw/reports/daily/$today.md`` 에 적재하라.

규칙 (CLAUDE.md §7.11 · .claude/commands/log.md 의 A-2·A-3):
- 명령을 나열하지 말고 **작업 단위로 묶어 한 문장씩** 쓴다. 레포가 여럿이면 레포명을 접두로.
- 탐색·확인·실패 후 재시도 등 결과가 남지 않은 시행착오는 적지 않는다.
- 배치: 완료 작업·커밋 → ``## 한 일`` / 새 사실·실험 결과 → ``## 발견`` / 굳은 결정 → ``## 결정`` / 막힌 것 → ``## 막힘``.
- ``## 오늘 할 일`` 에 매칭되는 항목이 완료됐으면 ``- [ ]`` → ``- [x]``.
- **중복 금지**: 이미 있는 내용은 다시 적지 말고, 이어진 작업이면 기존 줄을 보강한다.
- **마스킹(§9)**: 고객·개체 식별 정보, 계정·토큰, 급여·계약액은 제거한다. digest 에는 마스킹이 안 돼 있다.
- 오늘 파일이 없으면 §7.3 골격(한 일/발견/결정/막힘/내일)으로 새로 만든다. 지난 날짜 파일은 절대 건드리지 않는다.
- 본문은 평어체.

digest 는 아래에 붙였다. 깨져 보이거나 더 필요하면 ``$digest`` 를 Read 로 직접 읽어라
(그래도 부족하면 ``~/.claude/projects/`` 의 세션 원문을 Read 로 확인해도 된다).

무인 실행이므로 **질문하지 말고** 판단해서 기록한 뒤, 마지막에 한 줄로만 보고하라: ``한 일 N줄 / 발견 M / 막힘 K``.

--- digest ($digest) ---
$body
"@

$promptFile = Join-Path $env:TEMP ("wiki-prompt-{0}.txt" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
# BOM 없는 UTF-8 로 — Set-Content -Encoding utf8 은 PS 5.1 에서 BOM 을 붙여 프롬프트 첫 글자를 오염시킨다
[System.IO.File]::WriteAllText($promptFile, $prompt, (New-Object System.Text.UTF8Encoding $false))

try {
    $out = Get-Content $promptFile -Raw -Encoding utf8 | & $ClaudeExe -p `
        --permission-mode acceptEdits `
        --allowedTools 'Read' 'Edit' 'Write' 'Glob' 'Grep' 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { Note "claude 실패 (exit $LASTEXITCODE): $($out.Trim())"; exit 1 }
    Note ("기록 완료 — " + ($out.Trim() -split "`n" | Select-Object -Last 1))
    # 성공했을 때만 커서 전진 — 실패하면 다음 실행이 같은 구간을 다시 훑는다(누락 방지)
    [System.IO.File]::WriteAllText($cursor, (Get-Date).ToUniversalTime().ToString('o'), (New-Object System.Text.UTF8Encoding $false))
}
finally {
    Remove-Item $promptFile -Force -ErrorAction SilentlyContinue
    Remove-Item $digest -Force -ErrorAction SilentlyContinue
}

exit 0
