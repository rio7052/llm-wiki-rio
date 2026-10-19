#!/usr/bin/env python3
"""template-sync.py — 개인 위키 템플릿의 새 판을 내 위키에 반영한다.

템플릿(Use this template)으로 만든 위키는 템플릿과 git 이력이 이어져 있지 않아 git merge 가 안 된다.
그래서 파일마다 세 판을 비교한다: 마지막으로 받은 템플릿 판(base) · 내 파일(local) · 새 템플릿 판(new).

  내가 안 고친 파일 (local == base)   → 새 판으로 바꾼다
  내가 고친 파일                      → git merge-file 로 3방향으로 합친다
  합치다 충돌                         → 내 파일은 그대로 두고 .template-sync/conflicts/ 에 모은다 (Claude 가 합친다)
  템플릿에 새로 생긴 파일             → 추가한다. 내가 지운 파일은 다시 받지 않는다
  템플릿에서 지워진 파일              → 내가 안 고쳤으면 같이 지운다
  me.md·brain/·raw/·wiki/·index·log   → 건드리지 않는다 (규칙: tools/template-sync-rules.txt)

마지막으로 받은 판은 .template-version 에 적고 커밋한다. 이 파일이 없으면(처음 실행) 파일마다 템플릿
이력에서 내 파일과 똑같은 판을 찾아 base 로 삼는다.

사용:
  python tools/template-sync.py --check              # 새 판이 있는지 한 줄 (/morning 이 부른다)
  python tools/template-sync.py                      # 미리보기 — 바뀌는 파일과 사람이 할 일
  python tools/template-sync.py --yes                # 적용
  python tools/template-sync.py --yes --skip <경로>  # 그 파일만 이번에 받지 않는다(여러 번 줄 수 있다)
  python tools/template-sync.py --resolved <경로>    # 충돌을 합친 뒤 표시를 지운다
  python tools/template-sync.py --source <폴더>      # 템플릿 대신 로컬 git 저장소를 쓴다(시험용)

필요: git, gh(로그인). 템플릿 저장소가 private 이라 gh 인증으로 받는다.
종료 코드: 0 정상 · 1 실패 · 2 사용법 · 3 템플릿을 받지 못함
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

REPO = os.environ.get("TEMPLATE_REPO", "bodit-inc/llm-wiki-template")
BRANCH = os.environ.get("TEMPLATE_BRANCH", "main")
ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / ".template-version"
WORK = ROOT / ".template-sync"
CLONE = WORK / "repo"
RULES_PATH = "tools/template-sync-rules.txt"
CHANGELOG_PATH = "CHANGELOG.md"
DEFAULT_RULES = """
keep me.md
keep index.md
keep log.md
keep .env
keep .template-version
keep tools/slack-ingest/channels.json
sync brain/README.md
sync brain/TEMPLATE.md
keep brain/**
keep raw/**
keep wiki/**
sync **
"""
GH_CRED = ["-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]
ENTRY_RE = re.compile(r"^## (v(\d+)) · (\d{4}-\d{2}-\d{2}) · (.+?)\s*$", re.M)


class Fail(Exception):
    pass


# --------------------------------------------------------------------------- 실행 보조
def run(cmd, cwd=None, check=True, data=None, timeout=300):
    try:
        r = subprocess.run(cmd, cwd=cwd, input=data, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        raise Fail(f"{cmd[0]} 을 찾지 못했다. 설치돼 있는지 확인한다")
    except subprocess.TimeoutExpired:
        raise Fail(f"시간 초과: {' '.join(cmd[:3])}")
    if check and r.returncode != 0:
        raise Fail(r.stderr.decode("utf-8", "replace").strip() or f"실패: {' '.join(cmd[:4])}")
    return r


def git(repo, *args, check=True):
    return run(["git", "-C", str(repo), *args], check=check).stdout


def show(repo, commit, path):
    """그 판의 파일 내용(bytes). 없으면 None."""
    r = run(["git", "-C", str(repo), "show", f"{commit}:{path}"], check=False)
    return r.stdout if r.returncode == 0 else None


def norm(b):
    return None if b is None else b.replace(b"\r\n", b"\n")


def read_local(path):
    p = ROOT / path
    return p.read_bytes() if p.is_file() else None


# --------------------------------------------------------------------------- 템플릿 받기
def fetch(source):
    """(저장소 경로, 최신 커밋) — 템플릿 전체 이력을 .template-sync/repo 에 받아 둔다."""
    if source:
        repo = Path(source).resolve()
        return repo, git(repo, "rev-parse", "HEAD").decode().strip()
    WORK.mkdir(exist_ok=True)
    if not (CLONE / ".git").exists():
        if CLONE.exists():
            shutil.rmtree(CLONE)
        run(["gh", "repo", "clone", REPO, str(CLONE), "--", "--quiet", "--no-checkout"], timeout=600)
    else:
        run(["git", *GH_CRED, "-C", str(CLONE), "fetch", "--quiet", "origin", BRANCH], timeout=600)
    ref = f"origin/{BRANCH}"
    return CLONE, git(CLONE, "rev-parse", ref).decode().strip()


# --------------------------------------------------------------------------- 규칙·변경 기록
def glob_re(pat):
    out, i = "", 0
    while i < len(pat):
        if pat.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pat.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pat[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(pat[i]), i + 1
    return re.compile(f"^{out}$")


def load_rules(text):
    rules = []
    for line in (text or DEFAULT_RULES).splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        action, _, pat = line.partition(" ")
        if action in ("keep", "sync") and pat.strip():
            rules.append((action, glob_re(pat.strip())))
    return rules


def action_for(path, rules):
    for action, rx in rules:
        if rx.match(path):
            return action
    return "keep"


def parse_changelog(text):
    """[(판 번호, 'vN', 날짜, 제목, 사람이 할 일 줄들)] 최신이 앞."""
    if not text:
        return []
    heads = list(ENTRY_RE.finditer(text))
    out = []
    for i, m in enumerate(heads):
        body = text[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        todo = []
        sec = re.search(r"^### 사람이 할 일\s*$(.*?)(?=^##|\Z)", body, re.M | re.S)
        if sec:
            todo = [l.rstrip() for l in sec.group(1).strip().splitlines() if l.strip()]
        out.append((int(m.group(2)), m.group(1), m.group(3), m.group(4), todo))
    return out


# --------------------------------------------------------------------------- 상태
def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def save_state(state):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------- 판정
def start_commit(repo, latest):
    """처음 실행일 때 쓰는 기준: 내 위키 첫 커밋 날짜 직전의 템플릿 판."""
    r = run(["git", "-C", str(ROOT), "log", "--reverse", "--format=%cI"], check=False)
    first = r.stdout.decode().split("\n", 1)[0].strip() if r.returncode == 0 else ""
    if first:
        c = git(repo, "rev-list", "-1", f"--before={first}", latest, check=False).decode().strip()
        if c:
            return c
    return None


def infer_base(repo, latest, path, local, fallback):
    """처음 실행: 템플릿 이력에서 내 파일과 똑같은 가장 최근 판을 찾는다."""
    commits = git(repo, "log", "--format=%H", "--full-history", latest, "--", path).decode().split()
    if local is not None:
        want = norm(local)
        for c in commits:
            if norm(show(repo, c, path)) == want:
                return show(repo, c, path), c
    if fallback:
        return show(repo, fallback, path), fallback
    return None, None


def merge3(local, base, new):
    """(합친 내용, 충돌 수). git merge-file 을 쓴다."""
    with tempfile.TemporaryDirectory() as d:
        paths = []
        for name, content in (("local", local), ("base", base), ("new", new)):
            p = Path(d) / name
            p.write_bytes(norm(content) or b"")
            paths.append(str(p))
        r = run(["git", "merge-file", "-p", "-L", "내 위키", "-L", "이전 템플릿", "-L", "새 템플릿", *paths],
                check=False)
        if r.returncode < 0 or r.returncode > 127:
            raise Fail("git merge-file 실패: " + r.stderr.decode("utf-8", "replace"))
        return r.stdout, r.returncode


def plan(repo, latest, state):
    rules = load_rules((show(repo, latest, RULES_PATH) or b"").decode("utf-8"))
    new_files = set(git(repo, "ls-tree", "-r", "--name-only", latest).decode().splitlines())
    recorded = state.get("commit")
    pending = state.get("pending", {})
    if recorded and git(repo, "cat-file", "-t", recorded, check=False).decode().strip() != "commit":
        recorded = None                      # 템플릿 이력에 없는 판(강제 푸시 등) → 처음처럼 추정
    fallback = None if recorded else start_commit(repo, latest)

    paths = set(new_files)
    if recorded:
        paths |= set(git(repo, "ls-tree", "-r", "--name-only", recorded).decode().splitlines())
    else:
        # 템플릿에서 지워진 파일 가운데 내 위키에 남은 것
        gone = git(repo, "log", "--format=", "--name-only", "--diff-filter=D", latest).decode().split()
        paths |= {p for p in gone if (ROOT / p).is_file()}
    paths |= set(pending)

    items, base_dates = [], []
    for path in sorted(paths):
        if action_for(path, rules) != "sync":
            continue
        local = read_local(path)
        new = show(repo, latest, path) if path in new_files else None
        if path in pending:
            base, bc = show(repo, pending[path], path), pending[path]
        elif recorded:
            base, bc = show(repo, recorded, path), recorded
        else:
            base, bc = infer_base(repo, latest, path, local, fallback)
        if bc:
            base_dates.append(git(repo, "show", "-s", "--format=%cs", bc).decode().strip())
        kind, merged, conflicts = decide(local, base, new)
        items.append({"path": path, "kind": kind, "local": local, "base": base, "new": new,
                      "merged": merged, "conflicts": conflicts, "base_commit": bc})
    return items, (min(base_dates) if base_dates else "")


def decide(local, base, new):
    L, B, N = norm(local), norm(base), norm(new)
    if L == N:
        return "same", None, 0
    if L is None:
        if N is None:
            return "same", None, 0
        return ("add", None, 0) if B is None else ("skip-deleted", None, 0)
    if B is not None and L == B:
        return ("delete", None, 0) if N is None else ("replace", None, 0)
    if N is None:
        return "keep-modified", None, 0
    if B is not None and N == B:
        return "same", None, 0            # 템플릿은 그대로고 내가 고친 것만 있다
    if B is None:
        return "conflict", None, 0        # 기준 판을 모른다 — Claude 가 합친다
    merged, n = merge3(local, base, new)
    return ("merge", merged, 0) if n == 0 else ("conflict", merged, n)


# --------------------------------------------------------------------------- 출력
LABELS = [
    ("replace", "새 판으로 바꿈 (내가 안 고친 파일)"),
    ("add", "새로 추가"),
    ("merge", "합침 (내가 고친 파일, 충돌 없음)"),
    ("conflict", "충돌 — Claude 와 함께 합쳐야 함 (내 파일은 그대로 둔다)"),
    ("delete", "템플릿에서 지워져 같이 지움"),
    ("keep-modified", "템플릿에서 지워졌지만 내가 고쳐서 남김"),
    ("skip-deleted", "내가 지운 파일이라 다시 받지 않음"),
]


def report(items, entries, since_desc, skip):
    print(since_desc)
    if entries:
        print("\n■ 바뀐 것 (CHANGELOG.md)")
        for _, v, date, title, todo in entries:
            print(f"  {v} · {date} · {title}")
            for line in todo:
                print(f"      {line}")
    changed = False
    for kind, label in LABELS:
        rows = [it for it in items if it["kind"] == kind]
        if not rows:
            continue
        changed = changed or kind not in ("skip-deleted", "keep-modified")
        print(f"\n■ {label} {len(rows)}개")
        for it in rows:
            note = " (이번에 받지 않음 --skip)" if it["path"] in skip else ""
            extra = f" · 충돌 {it['conflicts']}곳" if kind == "conflict" and it["conflicts"] else ""
            print(f"  {it['path']}{extra}{note}")
    if not changed:
        print("\n받을 파일 변경이 없다.")
    return changed


def write_file(path, content, like):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    data = norm(content)
    if like is not None and b"\r\n" in like:
        data = data.replace(b"\n", b"\r\n")
    p.write_bytes(data)


def apply(items, latest, repo, entries, state, skip):
    pending = dict(state.get("pending", {}))
    conflict_dir = WORK / "conflicts"
    for it in items:
        path, kind = it["path"], it["kind"]
        if path in skip:
            continue
        if kind in ("replace", "add"):
            write_file(path, it["new"], it["local"])
        elif kind == "merge":
            write_file(path, it["merged"], it["local"])
        elif kind == "delete":
            (ROOT / path).unlink()
        if kind == "conflict":
            for sub, content in (("conflicts", it["merged"] or it["new"]), ("base", it["base"]), ("new", it["new"])):
                if content is None:
                    continue
                dst = WORK / sub / path
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(norm(content))
            pending[path] = it["base_commit"] or latest
        elif path in pending and kind in ("replace", "merge", "same", "delete"):
            pending.pop(path, None)
            for sub in ("conflicts", "base", "new"):
                (WORK / sub / path).unlink(missing_ok=True)
    top = entries[0] if entries else None
    state.update({
        "repo": REPO,
        "commit": latest,
        "version": top[1] if top else state.get("version", ""),
        "applied": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "pending": pending,
    })
    save_state(state)
    ensure_ignored()
    return conflict_dir, pending


def ensure_ignored():
    gi = ROOT / ".gitignore"
    text = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if ".template-sync/" not in text:
        with gi.open("a", encoding="utf-8", newline="\n") as f:
            f.write(("" if text.endswith("\n") or not text else "\n")
                    + "\n# 템플릿 동기화 작업 폴더 (tools/template-sync.py)\n.template-sync/\n")


# --------------------------------------------------------------------------- 명령
def cmd_check():
    state = load_state()
    try:
        text = run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                    f"repos/{REPO}/contents/{CHANGELOG_PATH}?ref={BRANCH}"], timeout=20).stdout.decode("utf-8")
        head = run(["gh", "api", f"repos/{REPO}/commits/{BRANCH}", "--jq", ".sha"], timeout=20).stdout.decode().strip()
    except Fail:
        print("템플릿 새 판 확인 못 함 (gh 로그인·네트워크)")
        return 0
    entries = parse_changelog(text)
    latest_v = entries[0][1] if entries else "?"
    if not state.get("commit"):
        print(f"템플릿 {latest_v} — 이 위키는 아직 템플릿 동기화 기록이 없다. /template-update 로 한 번 맞춘다")
        return 0
    mine = int(str(state.get("version", "v0")).lstrip("v") or 0)
    newer = [e for e in entries if e[0] > mine]
    pending = state.get("pending", {})
    parts = []
    if newer:
        names = ", ".join(f"{e[1]} {e[3]}" for e in newer[:3]) + (" 외" if len(newer) > 3 else "")
        parts.append(f"템플릿 새 판 {len(newer)}개 — {names}")
    elif head and head != state.get("commit"):
        parts.append("템플릿에 작은 수정이 있다")
    if pending:
        parts.append(f"아직 합치지 못한 파일 {len(pending)}개")
    if not parts:
        print(f"템플릿 최신 ({state.get('version')})")
        return 0
    print(" · ".join(parts) + " → /template-update")
    return 0


def cmd_resolved(paths):
    state = load_state()
    pending = state.get("pending", {})
    for path in paths:
        path = path.replace("\\", "/")
        if path not in pending:
            print(f"{path}: 합칠 목록에 없다")
            continue
        pending.pop(path)
        for sub in ("conflicts", "base", "new"):
            (WORK / sub / path).unlink(missing_ok=True)
        print(f"{path}: 합침 완료로 표시")
    state["pending"] = pending
    save_state(state)
    return 0


def main():
    ap = argparse.ArgumentParser(description="개인 위키 템플릿의 새 판을 반영한다")
    ap.add_argument("--check", action="store_true", help="새 판이 있는지 한 줄")
    ap.add_argument("--yes", action="store_true", help="미리보기 대신 적용")
    ap.add_argument("--skip", action="append", default=[], help="이번에 받지 않을 파일")
    ap.add_argument("--resolved", nargs="+", help="충돌을 합친 파일을 완료로 표시")
    ap.add_argument("--source", help="템플릿 대신 쓸 로컬 git 저장소(시험용)")
    args = ap.parse_args()

    if args.check:
        return cmd_check()
    if args.resolved:
        return cmd_resolved(args.resolved)

    state = load_state()
    try:
        repo, latest = fetch(args.source)
    except Fail as e:
        print(f"템플릿을 받지 못했다: {e}\n`gh auth status` 로 로그인을 확인하고, bodit-inc 조직에 접근할 수 있는지 본다.")
        return 3
    try:
        items, oldest_base = plan(repo, latest, state)
    except Fail as e:
        print(f"비교하지 못했다: {e}")
        return 1

    entries = parse_changelog((show(repo, latest, CHANGELOG_PATH) or b"").decode("utf-8"))
    if state.get("version"):
        mine = int(str(state["version"]).lstrip("v") or 0)
        shown = [e for e in entries if e[0] > mine]
        since = f"템플릿 {state['version']} ({state.get('commit', '')[:7]}) → {entries[0][1] if entries else '?'} ({latest[:7]})"
    else:
        shown = [e for e in entries if not oldest_base or e[2] >= oldest_base]
        since = (f"처음 동기화 — 내 파일과 같은 템플릿 판을 파일마다 찾았다(가장 오래된 것 {oldest_base or '모름'}). "
                 f"새 판 {entries[0][1] if entries else '?'} ({latest[:7]})")
    skip = {s.replace("\\", "/") for s in args.skip}
    changed = report(items, shown, since, skip)

    if not args.yes:
        if changed or not state.get("commit"):
            print("\n→ 적용하려면 --yes 를 붙인다. 특정 파일을 빼려면 --skip <경로>.")
        return 0

    _, pending = apply(items, latest, repo, entries, state, skip)
    print(f"\n적용했다. .template-version = {state.get('version')} ({latest[:7]})")
    if pending:
        print(f"합칠 파일 {len(pending)}개가 .template-sync/conflicts/ 에 있다. 내 파일을 고친 뒤 "
              "`python tools/template-sync.py --resolved <경로>` 로 표시를 지운다.")
    print("바뀐 파일과 .template-version 을 커밋한다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
