"""자격 증명 가리기 — `tools/sensitive-check.txt` 의 [credentials] 규칙 한 곳만 본다.

쓰는 곳:
- `tools/slack-ingest/fetch_slack.py` — Slack 원문을 파일로 쓰기 전에 값을 지운다(수집 단계 차단).
- `tools/hooks/pre-commit` — 그래도 새어 들어온 것이 있으면 커밋을 막는다(2차 방어선).
- `tools/company-wiki.py` — 전사 업로드 직전 검사에 같은 규칙을 함께 쓴다.

규칙을 고치려면 코드가 아니라 `tools/sensitive-check.txt` 를 고친다.
"""
import re
from pathlib import Path

CHECK_FILE = Path(__file__).resolve().parent / "sensitive-check.txt"
PLACEHOLDER = "[자격증명 가림]"


def load_credential_patterns(check_file=CHECK_FILE):
    """[(이름, 정규식), ...] — sensitive-check.txt 의 [credentials] 절."""
    out, section = [], None
    if not Path(check_file).exists():
        return out
    for raw in Path(check_file).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line
            continue
        if section == "[credentials]" and "|" in line:
            name, rx = line.split("|", 1)
            try:
                out.append((name.strip(), re.compile(rx.strip())))
            except re.error as e:
                print(f"⚠ [credentials] 규칙의 모양이 잘못 적혔다({name.strip()}): {e}")
    return out


def _replace(m):
    label = m.group(1) if m.re.groups else None
    return f"{label}: {PLACEHOLDER}" if label else PLACEHOLDER


def mask(text, patterns=None):
    """자격 증명으로 보이는 부분의 값을 지운 문자열. 이름표는 남겨 무엇이 가려졌는지 보이게 한다."""
    for _, rx in (patterns if patterns is not None else load_credential_patterns()):
        text = rx.sub(_replace, text)
    return text


def find(text, patterns=None):
    """[(줄 번호, 이름), ...] — 가리지 않고 찾기만 한다(커밋 훅용)."""
    hits = []
    pats = patterns if patterns is not None else load_credential_patterns()
    for no, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if PLACEHOLDER in line:
            continue
        for name, rx in pats:
            if rx.search(line):
                hits.append((no, name))
    return hits
