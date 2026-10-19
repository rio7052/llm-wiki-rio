# sync-sessions.ps1 — Claude Code 세션 transcript 를 raw/sessions/ 로 미러
#
# Claude Code 는 모든 세션 대화 원문을 ~/.claude/projects/<project-slug>/<session-id>.jsonl
# 로 남기지만, 이 위치는 PC 교체 시 유실된다. 이 스크립트가 위키 raw/sessions/ 로 미러해
# /session-retro 가 읽을 수 있게 한다.
#
# 주의: .jsonl 은 md 가 아니므로 **커밋되지 않는다**(CLAUDE.md §4.3 md-only, .gitignore).
#       로컬 작업용 캐시이며, 회고 결과물(md)만 위키에 남는다.
#
# 사용 (Windows PowerShell):
#   powershell -File tools/sync-sessions.ps1            # 기본: %USERPROFILE%\.claude\projects → raw/sessions
#   (PS 프롬프트에서 직접:  .\tools\sync-sessions.ps1 )
#
# 동작: robocopy *.jsonl /S (추가·갱신만 — 미러본에서 삭제하지 않음).
#       진행 중 세션 파일은 계속 자라므로 재실행 시 최신본으로 덮어쓴다.
#       memory/ 하위(auto-memory .md)는 transcript 가 아니므로 제외.
#
# raw/sessions/ 는 수집기 관리 캐시 — 사람이 수동 편집하지 않는다 (CLAUDE.md §4.3 예외 3).

param(
    [string]$Source = (Join-Path $env:USERPROFILE '.claude\projects'),
    [string]$Dest
)

$ErrorActionPreference = 'Stop'
$wikiRoot = Split-Path -Parent $PSScriptRoot   # tools/ 의 부모 = wiki root
if (-not $Dest) { $Dest = Join-Path $wikiRoot 'raw\sessions' }

if (-not (Test-Path $Source)) { Write-Error "source not found: $Source"; exit 1 }
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

robocopy $Source $Dest *.jsonl /S /XD memory /R:2 /W:3 /NFL /NDL /NJH /NP
$code = $LASTEXITCODE   # robocopy: 0~7 성공계열, 8+ 실패

if ($code -ge 8) { Write-Error "robocopy failed (exit $code)"; exit $code }
Write-Host "session transcript 미러 완료 → $Dest (robocopy exit $code)"
exit 0
