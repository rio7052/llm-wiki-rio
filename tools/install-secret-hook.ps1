# 계정·비밀번호·키 커밋 차단 훅 등록/해제.
#   powershell -File tools/install-secret-hook.ps1            # 등록
#   powershell -File tools/install-secret-hook.ps1 -Status    # 상태
#   powershell -File tools/install-secret-hook.ps1 -Remove    # 해제
param([switch]$Status, [switch]$Remove)

$root = (git rev-parse --show-toplevel)
if (-not $root) { Write-Host "git 저장소 안에서 실행한다."; exit 1 }
Set-Location $root

if ($Status) {
    $path = (git config --get core.hooksPath)
    if ($path -eq "tools/hooks") { Write-Host "등록됨 — core.hooksPath = tools/hooks" }
    else { Write-Host "등록 안 됨 (현재 core.hooksPath = '$path')" }
    exit 0
}
if ($Remove) {
    git config --unset core.hooksPath | Out-Null
    Write-Host "해제했다. 이제 커밋 전 검사를 하지 않는다."
    exit 0
}
git config core.hooksPath tools/hooks
Write-Host "등록했다 — 커밋 전에 tools/hooks/pre-commit 이 계정·비밀번호·키를 검사한다."
Write-Host "규칙은 tools/sensitive-check.txt 의 [credentials] 에 있다."
