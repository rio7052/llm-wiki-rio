"""커밋하려는 내용에 계정·비밀번호·키가 있으면 막는다(2차 방어선).

규칙은 `tools/sensitive-check.txt` 의 [credentials] 한 곳만 본다.
Slack 수집기는 이미 수집 단계에서 값을 지우므로, 여기서 걸리는 것은
손으로 적었거나 다른 경로로 들어온 것이다.
"""
import subprocess
import sys
from pathlib import Path

# Windows 콘솔(cp949)에서 한글·— 출력 시 UnicodeEncodeError 방지.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import secret_mask  # noqa: E402

SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".xlsx", ".pptx", ".docx",
               ".hwp", ".hwpx", ".parquet", ".jsonl", ".ico", ".woff", ".woff2"}
# 규칙 자체와 규칙을 설명하는 문서는 예시를 담고 있으므로 검사하지 않는다.
SKIP_PATHS = {"tools/sensitive-check.txt", "tools/secret_mask.py",
              "tools/hooks/check_staged.py", "tools/hooks/pre-commit"}


def staged_files():
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                         capture_output=True, text=True, encoding="utf-8")
    return [p for p in out.stdout.splitlines() if p.strip()]


def staged_text(path):
    out = subprocess.run(["git", "show", f":{path}"], capture_output=True)
    if out.returncode != 0:
        return None
    try:
        return out.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def main():
    patterns = secret_mask.load_credential_patterns(ROOT / "tools" / "sensitive-check.txt")
    if not patterns:
        return 0
    problems = []
    for path in staged_files():
        if path in SKIP_PATHS or Path(path).suffix.lower() in SKIP_SUFFIX:
            continue
        text = staged_text(path)
        if text is None:
            continue
        for no, name in secret_mask.find(text, patterns):
            problems.append((path, no, name))
    if not problems:
        return 0
    print("커밋하지 않았다 — 계정·비밀번호·키로 보이는 것이 있다:")
    for path, no, name in problems[:40]:
        print(f"  {path}:{no} · {name}")
    if len(problems) > 40:
        print(f"  … 그리고 {len(problems) - 40}건 더")
    print("\n고치는 법")
    print("  · Slack 원문이면: python tools/slack-ingest/fetch_slack.py --mask-existing")
    print("  · 그 밖의 파일이면: 값을 지우고 다시 add 한다")
    print("  · 값이 아니라 설명이라 괜찮다면: tools/sensitive-check.txt 의 규칙을 고치거나,")
    print("    이번만 넘기려면 git commit --no-verify (되도록 쓰지 않는다)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
