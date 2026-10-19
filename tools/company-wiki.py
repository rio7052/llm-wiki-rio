#!/usr/bin/env python3
"""전사 위키(bodit-llm-wiki)를 내려받지 않고 읽고 쓰는 도구.

개인 위키의 /eod·/morning 이 부른다. 전사 위키를 로컬에 clone 하지 않고 GitHub API(`gh api`)로
파일을 직접 읽고 올린다. 로컬에 사본이 없으니 "충돌 상태" 에 빠질 자리가 없다.
올리다 거절되면 최신 상태를 다시 읽고 재시도한다. (전사 CLAUDE.md §8, docs/guide/contributing.md)

필요: GitHub CLI(`gh`) 로그인, 전사 위키 people/<내이름>.md 에 `github: <내 계정>`.
      Python 3.9+ 표준 라이브러리만 쓴다.

사용:
  python tools/company-wiki.py whoami                          # 전사 위키에서 내 이름·파트
  python tools/company-wiki.py daily-put <공유본.md> [--summary "한 줄"] [--dry-run]
                                                               # 내 일일 리포트 공유본을 main 에 바로 올린다
  python tools/company-wiki.py daily-get --date 2026-09-12     # 그날 팀 일일 리포트 전부 + 안 쓴 사람
  python tools/company-wiki.py log-put --op ops --title "..." --slug my-change --body-file body.md
                                                               # 활동 기록 항목 하나를 log/ 에 올린다
  python tools/company-wiki.py get <경로>                      # 파일 하나 읽기
  python tools/company-wiki.py check <파일>                    # 민감 정보 기계 검사만 (올리지 않음)

  지식 올리기 — 미리보기만 나오고, 사람이 승인하면 --yes 를 붙여 다시 실행
  python tools/company-wiki.py mine-put --file minutes.md:raw/meetings/2026-09-14-saebom-visit.md --slug saebom-visit --op meeting --title "새봄 방문 회의"
                                                               # 내 것(회의록·논문 원문·내 프로필·내 brain)은 main 에 바로
  python tools/company-wiki.py wiki-pr --file adr.md:wiki/decisions/2026-09-raw-data-aws.md --title "결정: raw data AWS 내부 처리" \
      --slug raw-data-aws --kind decision --op decision --reviewer mark --body-file pr.md
                                                               # 공용 지식·규칙은 브랜치 + PR + 리뷰어

  할 일 (GitHub issue + 보드 Bodit Tasks) — 토큰에 project 권한 필요: gh auth refresh -s project
  python tools/company-wiki.py task-new --title "..." --body-file body.md --due 2026-09-18 --priority High --assignee jeremy
                                                               # 미리보기만. 사람이 승인하면 --yes 를 붙여 다시 실행
  python tools/company-wiki.py task-list --mine                # 내가 담당인 끝나지 않은 할 일
  python tools/company-wiki.py task-list --part analysis --due-within 7
  python tools/company-wiki.py task-update 12 --status "In progress"   # 내 담당이면 바로, 아니면 --yes 필요
  python tools/company-wiki.py task-close 12 --comment "새봄에 공유함"  # 미리보기만. 승인 후 --yes

올리는 명령(daily-put·log-put·task-new)은 올리기 직전에 tools/sensitive-check.txt 로 기계 검사를 한다.
걸리면 멈추고 보여 준다. 사람이 확인하고 승인했을 때만 --confirm-sensitive 를 붙여 다시 실행한다.

전사 위키 저장소를 바꾸려면 환경변수 COMPANY_WIKI_REPO=<owner/repo>.
보드는 COMPANY_BOARD_OWNER·COMPANY_BOARD_NUMBER, 기본 할 일 저장소는 COMPANY_TASK_REPO.
"""
import argparse
import base64
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = os.environ.get("COMPANY_WIKI_REPO", "bodit-inc/bodit-llm-wiki")
BRANCH = "main"
WIKI_ROOT = Path(__file__).resolve().parent.parent
CACHE = WIKI_ROOT / ".company-wiki.json"
CHECK_FILE = Path(__file__).resolve().parent / "sensitive-check.txt"
SLUG_RX = r"[a-z0-9][a-z0-9-]*"
DATE_RX = r"\d{4}-\d{2}-\d{2}"


class GhError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def gh(args, body=None, tries=3):
    """gh api 호출. 네트워크 오류(HTTP 상태 없음)는 잠깐 쉬고 재시도한다."""
    cmd = ["gh", "api"] + args
    if body is not None:
        cmd += ["--input", "-"]
    for attempt in range(1, tries + 1):
        try:
            p = subprocess.run(cmd, input=json.dumps(body) if body is not None else None,
                               capture_output=True, text=True, encoding="utf-8")
        except FileNotFoundError:
            sys.exit("GitHub CLI(gh) 가 없다. 설치 후 `gh auth login` 을 한 번 한다.")
        if p.returncode == 0:
            return json.loads(p.stdout) if p.stdout.strip() else None
        err = (p.stderr or p.stdout or "").strip()
        m = re.search(r"HTTP (\d{3})", err)
        status = int(m.group(1)) if m else None
        if status == 401 or "auth login" in err:
            sys.exit("GitHub 에 로그인되어 있지 않다. `gh auth login` 을 한 번 한다.")
        if status is None and attempt < tries:
            time.sleep(attempt * 3)
            continue
        raise GhError(err, status)


def tree_texts(folder):
    """폴더 안 파일들의 (이름, 내용) 을 한 번의 요청으로 받는다."""
    owner, name = REPO.split("/", 1)
    q = ("query($o:String!,$n:String!,$e:String!){repository(owner:$o,name:$n){object(expression:$e){"
         "... on Tree{entries{name type object{... on Blob{text}}}}}}}")
    data = gh(["graphql", "-f", f"query={q}", "-F", f"o={owner}", "-F", f"n={name}", "-f", f"e={BRANCH}:{folder}"])
    obj = (data or {}).get("data", {}).get("repository", {}).get("object") or {}
    return [(e["name"], (e.get("object") or {}).get("text") or "")
            for e in obj.get("entries", []) if e["type"] == "blob"]


def frontmatter(text):
    text = text.replace("\r\n", "\n").lstrip("﻿")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    fm = {}
    for line in text[4:end if end >= 0 else 4].split("\n"):
        if ":" in line and not line.lstrip().startswith("#"):
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def get_file(path, ref=BRANCH):
    """(내용, sha). 없으면 (None, None)."""
    try:
        data = gh([f"repos/{REPO}/contents/{path}?ref={ref}"])
    except GhError as e:
        if e.status == 404:
            return None, None
        raise
    return base64.b64decode(data["content"]).decode("utf-8"), data["sha"]


def put_file(path, text, message, tries=4, branch=BRANCH):
    """파일을 브랜치(기본 main)에 바로 올린다. 거절되면 최신 sha 를 다시 읽고 재시도한다."""
    # 올리는 파일은 늘 LF. raw 는 한 번 올리면 덮어쓸 수 없으므로 호출하는 쪽이 어떻게 읽었든 여기서 맞춘다.
    text = text.replace("\r\n", "\n")
    for attempt in range(1, tries + 1):
        _, sha = get_file(path, ref=branch)
        body = {"message": message, "branch": branch,
                "content": base64.b64encode(text.encode("utf-8")).decode("ascii")}
        if sha:
            body["sha"] = sha
        try:
            return gh(["-X", "PUT", f"repos/{REPO}/contents/{path}"], body)
        except GhError as e:
            if e.status in (409, 422) and attempt < tries:
                time.sleep(attempt * 2)
                continue
            raise


def tree_paths():
    data = gh([f"repos/{REPO}/git/trees/{BRANCH}?recursive=1"])
    return [t["path"] for t in data["tree"] if t["type"] == "blob"]


def whoami(refresh=False):
    login = gh(["user"])["login"]
    if CACHE.exists() and not refresh:
        try:
            c = json.loads(CACHE.read_text(encoding="utf-8"))
            if c.get("login") == login and c.get("repo") == REPO:
                return c
        except ValueError:
            pass
    for fname, text in tree_texts("people"):
        if not re.fullmatch(rf"{SLUG_RX}\.md", fname):
            continue
        fm = frontmatter(text)
        if fm.get("github", "").lower() == login.lower():
            info = {"login": login, "slug": fm.get("name") or Path(fname).stem,
                    "part": fm.get("part", ""), "repo": REPO}
            CACHE.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
            return info
    sys.exit(f"전사 위키 people/ 에서 `github: {login}` 을 찾지 못했다.\n"
             f"전사 위키 people/<내이름>.md 에 `github: {login}` 한 줄을 추가해야 한다 "
             f"(전사 docs/guide/contributing.md §3-3).")


def load_checks():
    """sensitive-check.txt 의 [words] 단어 목록과 [patterns]·[credentials] 정규식 목록."""
    words, patterns, section = [], [], None
    if not CHECK_FILE.exists():
        return words, patterns
    for raw in CHECK_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line
            continue
        if section == "[words]":
            words.append(line)
        elif section in ("[patterns]", "[credentials]") and "|" in line:
            name, rx = line.split("|", 1)
            try:
                patterns.append((name.strip(), re.compile(rx.strip())))
            except re.error as e:
                print(f"⚠ 검사 목록의 모양이 잘못 적혔다({name.strip()}): {e}", file=sys.stderr)
    return words, patterns


def _mask(text):
    return text if len(text) <= 2 else text[0] + "*" * (len(text) - 2) + text[-1]


def scan(text):
    """(줄 번호, 걸린 종류, 가린 미리보기) 목록. 미리보기에서 걸린 부분은 가려서 보여 준다."""
    words, patterns = load_checks()
    hits = []
    for no, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        for w in words:
            if w in line:
                hits.append((no, f"단어 '{w}'", line.strip()))
        for name, rx in patterns:
            found = list(rx.finditer(line))
            if found:
                preview = line
                for m in reversed(found):
                    preview = preview[:m.start()] + _mask(m.group()) + preview[m.end():]
                hits.append((no, name, preview.strip()))
    return hits


def report(hits):
    return "\n".join(f"  {no}번째 줄 · {kind}: {preview[:120]}" for no, kind, preview in hits)


def guard(text, confirmed, label):
    """올리기 직전 기계 검사. 걸렸는데 사람 승인이 없으면 멈춘다."""
    hits = scan(text)
    if not hits:
        return
    if confirmed:
        print(f"⚠ 민감 정보 검사에 {len(hits)}건이 걸렸지만, 사람이 확인하고 승인해서 올린다 ({label}):\n{report(hits)}",
              file=sys.stderr)
        return
    sys.exit(f"올리지 않았다 — 민감 정보 검사에 {len(hits)}건이 걸렸다 ({label}):\n{report(hits)}\n\n"
             f"가리거나 지운 뒤 다시 올린다. 확인해 보니 괜찮다면, 사람이 승인한 뒤에만 "
             f"--confirm-sensitive 를 붙여 다시 실행한다.")


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# ── commands ──────────────────────────────────────────────────────────────
def cmd_whoami(a):
    out(whoami(refresh=a.refresh))


def cmd_daily_put(a):
    me = whoami()
    text = Path(a.file).read_text(encoding="utf-8").replace("\r\n", "\n").lstrip("﻿")
    fm = frontmatter(text)
    date = a.date or fm.get("period", "")
    problems = []
    if not re.fullmatch(DATE_RX, date):
        problems.append("날짜를 알 수 없다. frontmatter period: YYYY-MM-DD 가 필요하다")
    if fm.get("type") != "report" or fm.get("report_kind") != "daily":
        problems.append("frontmatter 에 type: report · report_kind: daily 가 필요하다")
    if fm.get("period") and fm.get("period") != date:
        problems.append(f"period({fm.get('period')}) 가 날짜({date})와 다르다")
    if fm.get("author") != me["slug"]:
        problems.append(f"author({fm.get('author') or '없음'}) 가 전사 위키의 내 이름({me['slug']})과 다르다")
    if problems:
        sys.exit("올리지 않았다:\n- " + "\n- ".join(problems))

    path = f"raw/reports/daily/{me['slug']}/{date}.md"
    guard(text, a.confirm_sensitive, path)
    existing, _ = get_file(path)
    today = dt.date.today().isoformat()
    if existing is not None and date != today:
        sys.exit(f"{path} 는 이미 있고 작성일({date})이 지났다. 지난 일일 리포트는 고치지 않는다(전사 §4.4).")
    action = "갱신" if existing is not None else "새로 올림"
    if a.dry_run:
        out({"dry_run": True, "repo": REPO, "path": path, "action": action})
        return
    if existing == text:
        out({"ok": True, "path": path, "action": "변경 없음 — 같은 내용이 이미 올라가 있다"})
        return

    put_file(path, text, f"daily: {me['slug']} {date}")
    log_path = f"log/{date[:7]}/{date}-{me['slug']}-daily.md"
    line = f"- raw: {path}" + (f" — {a.summary.strip()}" if a.summary else "")
    guard(line, a.confirm_sensitive, "활동 기록 요약")
    log_text = f"---\ndate: {date}\nop: daily\nauthor: {me['slug']}\ntitle: {me['slug']}\n---\n\n{line}\n"
    put_file(log_path, log_text, f"log: daily {me['slug']} {date}")
    out({"ok": True, "action": action, "path": path, "log": log_path,
         "url": f"https://github.com/{REPO}/blob/{BRANCH}/{path}"})


def cmd_daily_get(a):
    if not re.fullmatch(DATE_RX, a.date):
        sys.exit("--date YYYY-MM-DD 가 필요하다")
    paths = tree_paths()
    rx = re.compile(rf"raw/reports/daily/({SLUG_RX})/{re.escape(a.date)}\.md")
    found = sorted((m.group(1), p) for p in paths for m in [rx.fullmatch(p)] if m)
    people = sorted(Path(p).stem for p in paths if re.fullmatch(rf"people/{SLUG_RX}\.md", p))
    wrote = {slug for slug, _ in found}
    for slug, path in found:
        text, _ = get_file(path)
        print(f"===== {slug} · {a.date} · {path} =====")
        print((text or "").rstrip())
        print()
    print(f"===== 요약 · {a.date} =====")
    print("쓴 사람: " + (", ".join(sorted(wrote)) or "없음"))
    print("안 쓴 사람: " + (", ".join(p for p in people if p not in wrote) or "없음"))
    print("(전사 위키 기준. 자비스·팀 문서에만 쓰는 사람이 있을 수 있다)")


def cmd_log_put(a):
    me = whoami()
    date = a.date or dt.date.today().isoformat()
    if not re.fullmatch(DATE_RX, date):
        sys.exit("--date YYYY-MM-DD")
    if not re.fullmatch(SLUG_RX, a.slug):
        sys.exit("--slug 는 영어 소문자·숫자·하이픈(kebab-case)")
    body = Path(a.body_file).read_text(encoding="utf-8").strip() if a.body_file else ""
    title = a.title.replace('"', '\\"')
    path = f"log/{date[:7]}/{date}-{me['slug']}-{a.slug}.md"
    time_line = f'time: "{a.time}"\n' if a.time else ""
    text = f'---\ndate: {date}\n{time_line}op: {a.op}\nauthor: {me["slug"]}\ntitle: "{title}"\n---\n\n{body}\n'
    guard(text, a.confirm_sensitive, path)
    if a.dry_run:
        out({"dry_run": True, "repo": REPO, "path": path})
        print(text)
        return
    put_file(path, text, f"log: {a.op} {me['slug']} {a.slug}")
    out({"ok": True, "path": path, "url": f"https://github.com/{REPO}/blob/{BRANCH}/{path}"})


def cmd_check(a):
    text = Path(a.file).read_text(encoding="utf-8")
    hits = scan(text)
    if not hits:
        print("민감 정보 검사: 걸린 것 없음")
        return
    print(f"민감 정보 검사: {len(hits)}건\n{report(hits)}")
    sys.exit(2)


def cmd_get(a):
    text, _ = get_file(a.path)
    if text is None:
        sys.exit(f"없다: {a.path}")
    print(text)


# ── 지식 올리기 (전사 CLAUDE.md §8 · docs/guide/contributing.md) ─────────────
# 내 것은 main 에 바로(mine-put), 공용 지식·규칙은 PR + 리뷰어(wiki-pr).
# 둘 다 --yes 없이는 미리보기만 보여 주고 멈춘다.
AUTO_PATHS = ("index.md", "log.md", "log/", "wiki/people/", "wiki/tasks/board.md")
RULE_PATHS = ("CLAUDE.md", "org.md", "docs/", ".github/", ".claude/", "tools/")
ALLOWED_EXT = (".md", ".yml", ".yaml")


def mine_prefixes(slug):
    return (f"raw/reports/daily/{slug}/", "raw/meetings/", "raw/papers/", f"people/{slug}.md", f"brain/{slug}/")


def parse_pairs(pairs):
    """'로컬파일:전사경로' 목록을 [(로컬, 전사경로, 내용)] 로. 경로 모양이 틀리면 멈춘다."""
    out_list = []
    for pair in pairs:
        # 전사 경로에는 콜론이 없으므로 마지막 콜론으로 나눈다(C:\... 같은 로컬 경로도 그대로 된다)
        local, _, remote = pair.rpartition(":")
        if not local or re.fullmatch(r"[A-Za-z]", local):
            sys.exit(f"--file 은 '로컬파일:전사경로' 모양이다: {pair}")
        remote = remote.strip().lstrip("/")
        if ".." in remote.split("/") or not remote:
            sys.exit(f"전사 경로가 잘못됐다: {remote}")
        if not remote.endswith(ALLOWED_EXT):
            sys.exit(f"전사 위키에는 md(또는 .ref.yml)만 올린다: {remote}")
        if any(remote == p or remote.startswith(p) for p in AUTO_PATHS):
            sys.exit(f"{remote} 는 봇이 만드는 파일이라 사람이 올리지 않는다(전사 §8·§10).")
        text = Path(local).read_text(encoding="utf-8").replace("\r\n", "\n").lstrip("﻿")
        out_list.append((local, remote, text))
    return out_list


def check_page(remote, text):
    """wiki/ 페이지의 최소 형식(전사 §5). 문제 목록을 돌려준다."""
    problems = []
    if remote.startswith("wiki/") and remote.endswith(".md") and not remote.endswith("README.md"):
        fm = frontmatter(text)
        for key in ("type", "last_updated", "tags"):
            if not fm.get(key):
                problems.append(f"{remote}: frontmatter `{key}` 가 없다")
        body = text.split("\n---", 2)[-1] if text.startswith("---") else text
        if not re.search(r"^# ", body, re.M):
            problems.append(f"{remote}: `# 제목` 이 없다(봇이 목록을 만들 때 제목과 바로 아래 요약 한 줄을 읽는다)")
    return problems


def log_entry_text(date, me, op, title, lines):
    title = title.replace('"', '\\"')
    return f'---\ndate: {date}\nop: {op}\nauthor: {me}\ntitle: "{title}"\n---\n\n' + "\n".join(lines) + "\n"


def cmd_mine_put(a):
    me = whoami()
    files = parse_pairs(a.file)
    mine = mine_prefixes(me["slug"])
    for _, remote, _ in files:
        if not remote.startswith(mine):
            sys.exit(f"{remote} 는 '내 것' 경로가 아니다. main 에 바로 올릴 수 있는 곳: {', '.join(mine)}\n"
                     f"공용 지식·규칙은 wiki-pr 로 PR 을 연다. 일일 리포트는 daily-put 을 쓴다.")
        if remote.startswith("raw/reports/daily/"):
            sys.exit("일일 리포트는 형식 검사와 지난 날짜 보호가 있는 daily-put 을 쓴다.")
    if not re.fullmatch(SLUG_RX, a.slug):
        sys.exit("--slug 는 영어 소문자·숫자·하이픈(kebab-case)")
    date = dt.date.today().isoformat()
    for _, remote, text in files:
        guard(text, a.confirm_sensitive, remote)
    rows = []
    for _, remote, text in files:
        existing, _ = get_file(remote)
        if existing is not None and remote.startswith(("raw/meetings/", "raw/papers/")):
            sys.exit(f"{remote} 는 이미 있다. raw 원문은 올린 뒤 고치지 않는다(전사 §4.4). 기존 캡처를 쓴다.")
        rows.append({"path": remote, "action": "갱신" if existing is not None else "새로 올림",
                     "same": existing == text})
    log_path = f"log/{date[:7]}/{date}-{me['slug']}-{a.slug}.md"
    if not a.yes:
        out({"uploaded": False, "repo": REPO, "branch": BRANCH, "files": rows, "log": log_path,
             "next": "올라갈 내용과 마스킹 결과를 사람에게 보여 주고 승인받은 뒤에만 --yes 를 붙여 다시 실행한다."})
        return
    for _, remote, text in files:
        put_file(remote, text, f"{a.op}: {me['slug']} {Path(remote).stem}")
    lines = [f"- raw: {r['path']}" for r in rows] + ([f"- {a.summary.strip()}"] if a.summary else [])
    put_file(log_path, log_entry_text(date, me["slug"], a.op, a.title, lines), f"log: {a.op} {me['slug']} {a.slug}")
    out({"uploaded": True, "files": [f"https://github.com/{REPO}/blob/{BRANCH}/{r['path']}" for r in rows], "log": log_path})


def cmd_wiki_pr(a):
    me = whoami()
    files = parse_pairs(a.file)
    if not re.fullmatch(SLUG_RX, a.slug):
        sys.exit("--slug 는 영어 소문자·숫자·하이픈(kebab-case)")
    kind = a.kind
    branch = f"{kind}/{me['slug']}-{a.slug}"
    date = dt.date.today().isoformat()
    body = Path(a.body_file).read_text(encoding="utf-8").strip() if a.body_file else ""
    reviewers = [x for x in to_logins(a.reviewer)]
    warnings, problems = [], []
    if any(x.lower() == me["login"].lower() for x in reviewers):
        reviewers = [x for x in reviewers if x.lower() != me["login"].lower()]
        warnings.append("자기 자신은 리뷰어가 될 수 없어 목록에서 뺐다(GitHub 규칙)")
    rules = [r for _, r, _ in files if r.startswith(RULE_PATHS)]
    knowledge = [r for _, r, _ in files if r.startswith("wiki/")]
    mine = [r for _, r, _ in files if r.startswith(mine_prefixes(me["slug"]))]
    if knowledge and not reviewers:
        problems.append("공용 지식(wiki/)은 리뷰어를 1명 이상 지정한다(--reviewer). 당사자 → 주제 파트장 → 파트별 1명 순으로 고른다")
    if rules:
        warnings.append(f"규칙 문서({', '.join(rules)})는 CODEOWNERS 가 Kevin 을 리뷰어로 자동 지정한다")
    if mine and len(mine) == len(files):
        warnings.append("모두 '내 것' 경로다. PR 없이 mine-put 으로 main 에 바로 올려도 된다")
    for _, remote, text in files:
        problems += check_page(remote, text)
    if problems:
        sys.exit("PR 을 열지 않았다:\n- " + "\n- ".join(problems))
    guard(f"{a.title}\n{body}", a.confirm_sensitive, "PR 제목·설명")
    for _, remote, text in files:
        guard(text, a.confirm_sensitive, remote)

    try:
        gh([f"repos/{REPO}/git/ref/heads/{branch}"])
        branch_exists = True
    except GhError as e:
        if e.status != 404:
            raise
        branch_exists = False
    open_prs = gh([f"repos/{REPO}/pulls?head={REPO.split('/')[0]}:{branch}&state=open"]) if branch_exists else []
    if branch_exists and not open_prs and not a.reuse_branch:
        sys.exit(f"브랜치 {branch} 가 이미 있고 열린 PR 이 없다. --slug 를 바꾸거나 --reuse-branch 를 붙인다.")
    rows = []
    for _, remote, text in files:
        on_main, _ = get_file(remote)
        rows.append({"path": remote, "action": "수정" if on_main is not None else "새 파일"})
    log_path = f"log/{date[:7]}/{date}-{me['slug']}-{a.slug}.md"
    preview = {"repo": REPO, "branch": branch, "pr": (open_prs[0]["html_url"] if open_prs else "새로 연다"),
               "title": a.title, "files": rows, "log": log_path, "reviewers": reviewers,
               "draft": a.draft, "warnings": warnings}
    if not a.yes:
        out({"opened": False, "preview": preview, "body": body,
             "next": "사람에게 파일 내용·리뷰어·마스킹 결과를 보여 주고 승인받은 뒤에만 --yes 를 붙여 다시 실행한다."})
        return

    if not branch_exists:
        base = gh([f"repos/{REPO}/git/ref/heads/{BRANCH}"])["object"]["sha"]
        gh(["-X", "POST", f"repos/{REPO}/git/refs"], {"ref": f"refs/heads/{branch}", "sha": base})
    for _, remote, text in files:
        put_file(remote, text, f"{kind}: {Path(remote).stem}", branch=branch)
    lines = [f"- {r['action']}: {r['path']}" for r in rows] + ([f"- {a.summary.strip()}"] if a.summary else [])
    put_file(log_path, log_entry_text(date, me["slug"], a.op, a.title, lines), f"log: {a.op} {me['slug']} {a.slug}", branch=branch)
    if open_prs:
        pr = open_prs[0]
    else:
        pr = gh(["-X", "POST", f"repos/{REPO}/pulls"],
                {"title": a.title, "head": branch, "base": BRANCH, "body": body, "draft": a.draft})
    if reviewers:
        try:
            gh(["-X", "POST", f"repos/{REPO}/pulls/{pr['number']}/requested_reviewers"], {"reviewers": reviewers})
        except GhError as e:
            warnings.append(f"리뷰어 지정 실패({e}). PR 화면에서 직접 지정한다")
    out({"opened": True, "pr": pr["html_url"], "number": pr["number"], "branch": branch,
         "reviewers": reviewers, "warnings": warnings})


# ── 할 일 (GitHub issue + 보드 Bodit Tasks) ────────────────────────────────
# 공유 할 일은 GitHub issue 가 원본이다(전사 docs/guide/task-policy.md §5).
# 만들기·닫기는 되돌릴 수 없으므로 --yes 없이는 미리보기만 보여 주고 멈춘다.
# 보드 번호·필드는 전사 docs/guide/github-integration.md "보드 정보" 와 같다.
BOARD_OWNER = os.environ.get("COMPANY_BOARD_OWNER", "bodit-inc")
BOARD_NUMBER = os.environ.get("COMPANY_BOARD_NUMBER", "7")
TASK_REPO = os.environ.get("COMPANY_TASK_REPO", "bodit-inc/bodit-ops-tasks")
API_V = ["-H", "X-GitHub-Api-Version: 2026-03-10"]
BOARD_API = f"orgs/{BOARD_OWNER}/projectsV2/{BOARD_NUMBER}"
REF_RX = re.compile(r"(?:https://github\.com/)?(?:([\w.-]+/[\w.-]+)(?:#|/issues/))?#?(\d+)")


def board_meta():
    """보드 필드와 조직 이슈 필드. {이름: {id, issue_field_id, options{이름: id}}}"""
    meta = {}
    for f in gh([f"{BOARD_API}/fields"] + API_V):
        opts = {}
        for o in f.get("options") or []:
            name = o["name"]["raw"] if isinstance(o["name"], dict) else o["name"]
            opts[name] = o["id"]
        meta[f["name"]] = {"id": f["id"], "issue_field_id": f.get("issue_field_id"), "options": opts}
    for f in gh([f"orgs/{BOARD_OWNER}/issue-fields"] + API_V):
        entry = meta.setdefault(f["name"], {"id": None, "options": {}})
        entry["issue_field_id"] = f["id"]
        if f.get("options"):
            entry["issue_options"] = [o["name"] for o in f["options"]]
    return meta


def people_logins():
    """전사 위키 people/ 의 {이름: github 계정}."""
    table = {}
    for fname, text in tree_texts("people"):
        if re.fullmatch(rf"{SLUG_RX}\.md", fname):
            fm = frontmatter(text)
            if fm.get("github"):
                table[fm.get("name") or Path(fname).stem] = fm["github"]
    return table


def to_logins(names):
    """'kevin,bley' 나 '@choiyc89' 를 GitHub 계정 목록으로."""
    if not names:
        return []
    table, logins = None, []
    for raw in names.split(","):
        name = raw.strip()
        if not name:
            continue
        if name.startswith("@"):
            logins.append(name[1:])
            continue
        table = table if table is not None else people_logins()
        if name not in table:
            sys.exit(f"'{name}' 의 GitHub 계정을 전사 위키 people/{name}.md 에서 찾지 못했다. "
                     f"계정을 알면 @계정 으로 적는다.")
        logins.append(table[name])
    return logins


def parse_ref(ref):
    m = REF_RX.fullmatch(ref.strip())
    if not m:
        sys.exit(f"이슈를 알아볼 수 없다: {ref} (예: 12, bodit-inc/bodit-ops-tasks#12, 이슈 주소)")
    return (m.group(1) or TASK_REPO), int(m.group(2))


def issue_board_item(repo, number):
    """(issue, 보드 항목 id 또는 None). issue 에는 databaseId·담당·상태가 들어 있다."""
    owner, name = repo.split("/", 1)
    q = ("query($o:String!,$n:String!,$i:Int!){repository(owner:$o,name:$n){issue(number:$i){"
         "databaseId title state url assignees(first:10){nodes{login}}"
         "projectItems(first:20){nodes{fullDatabaseId project{number owner{...on Organization{login}}}}}}}}")
    data = gh(["graphql", "-f", f"query={q}", "-F", f"o={owner}", "-F", f"n={name}", "-F", f"i={number}"])
    issue = ((data or {}).get("data", {}).get("repository") or {}).get("issue")
    if not issue:
        sys.exit(f"이슈가 없다: {repo}#{number}")
    item = None
    for node in issue["projectItems"]["nodes"]:
        p = node.get("project") or {}
        if str(p.get("number")) == str(BOARD_NUMBER) and (p.get("owner") or {}).get("login", "").lower() == BOARD_OWNER.lower():
            item = node["fullDatabaseId"]
    return issue, item


def pick(meta, field, value):
    """보드 단일 선택 값의 option id. 없는 값이면 고를 수 있는 값을 보여 주고 멈춘다."""
    opts = meta.get(field, {}).get("options", {})
    if value not in opts:
        sys.exit(f"{field} 값 '{value}' 가 없다. 고를 수 있는 값: {', '.join(opts)}")
    return opts[value]


def set_values(meta, repo, number, issue_db_id, item_id, status=None, part=None, due=None, priority=None):
    """issue 필드(마감·우선순위)는 issue 에, Status·Part 는 보드 항목에 쓴다."""
    values = []
    if due is not None:
        values.append({"field_id": meta["Target date"]["issue_field_id"], "value": due})
    if priority is not None:
        allowed = meta.get("Priority", {}).get("issue_options") or list(meta.get("Priority", {}).get("options", {}))
        if allowed and priority not in allowed:
            sys.exit(f"Priority 값 '{priority}' 가 없다. 고를 수 있는 값: {', '.join(allowed)}")
        values.append({"field_id": meta["Priority"]["issue_field_id"], "value": priority})
    if values:
        gh(["-X", "POST", f"repos/{repo}/issues/{number}/issue-field-values"] + API_V, {"issue_field_values": values})
    if item_id is None:
        item_id = gh(["-X", "POST", f"{BOARD_API}/items"] + API_V, {"type": "Issue", "id": issue_db_id})["id"]
    fields = []
    if status is not None:
        fields.append({"id": meta["Status"]["id"], "value": pick(meta, "Status", status)})
    if part is not None:
        fields.append({"id": meta["Part"]["id"], "value": pick(meta, "Part", part)})
    if fields:
        gh(["-X", "PATCH", f"{BOARD_API}/items/{item_id}"] + API_V, {"fields": fields})
    return item_id


def check_task_args(meta, a):
    if a.due and not re.fullmatch(DATE_RX, a.due):
        sys.exit("--due 는 YYYY-MM-DD")
    for field, value in (("Status", getattr(a, "status", None)), ("Part", getattr(a, "part", None))):
        if value is not None:
            pick(meta, field, value)


def cmd_task_new(a):
    me = whoami()
    meta = board_meta()
    part = a.part or me.get("part") or None
    check_task_args(meta, argparse.Namespace(due=a.due, status=a.status, part=part))
    body = Path(a.body_file).read_text(encoding="utf-8").strip() if a.body_file else ""
    assignees = to_logins(a.assignee)
    parent = parse_ref(a.parent) if a.parent else None
    if parent:
        issue_board_item(*parent)  # 상위 이슈가 없으면 여기서 멈춘다
    guard(f"{a.title}\n{body}", a.confirm_sensitive, "할 일 제목·본문")

    warnings = []
    if "끝났다고 보는 기준" not in body:
        warnings.append("본문에 '끝났다고 보는 기준' 이 없다. 언제 닫을지 적어 두는 것이 좋다")
    if not a.due:
        warnings.append("마감(--due)이 없다")
    others = [x for x in assignees if x.lower() != me["login"].lower()]
    if others:
        warnings.append(f"담당자 {', '.join('@' + x for x in others)} 에게 만드는 즉시 알림 메일이 간다")
    found = gh(["search/issues", "-X", "GET", "-f", f"q=repo:{a.repo} is:issue is:open in:title \"{a.title}\""])
    same = [i["html_url"] for i in found.get("items", []) if i["title"].strip() == a.title.strip()]
    if same and not a.allow_duplicate:
        sys.exit("만들지 않았다 — 같은 제목의 열린 이슈가 이미 있다:\n  " + "\n  ".join(same) +
                 "\n다른 일이면 제목을 바꾸거나 --allow-duplicate 를 붙인다.")

    preview = {"repo": a.repo, "title": a.title, "type": a.type, "assignees": assignees,
               "status": a.status, "part": part, "due": a.due, "priority": a.priority,
               "parent": f"{parent[0]}#{parent[1]}" if parent else None, "warnings": warnings}
    if not a.yes:
        out({"created": False, "preview": preview, "body": body,
             "next": "사람에게 이 내용을 보여 주고 승인을 받은 뒤에만 같은 명령에 --yes 를 붙여 다시 실행한다."})
        return

    payload = {"title": a.title, "body": body, "type": a.type}
    if assignees:
        payload["assignees"] = assignees
    issue = gh(["-X", "POST", f"repos/{a.repo}/issues"], payload)
    item_id = set_values(meta, a.repo, issue["number"], issue["id"], None,
                         status=a.status, part=part, due=a.due, priority=a.priority)
    if parent:
        gh(["-X", "POST", f"repos/{parent[0]}/issues/{parent[1]}/sub_issues"], {"sub_issue_id": issue["id"]})
    out({"created": True, "url": issue["html_url"], "ref": f"{a.repo}#{issue['number']}",
         "board_item": item_id, "warnings": warnings})


def cmd_task_list(a):
    meta = board_meta()
    ids = ",".join(str(meta[n]["id"]) for n in ("Status", "Part", "Target date", "Priority") if meta.get(n, {}).get("id"))
    items = gh([f"{BOARD_API}/items?per_page=100&fields={ids}", "--paginate"] + API_V) or []
    login = whoami()["login"].lower() if a.mine else None
    who = [x.lower() for x in to_logins(a.assignee)] if a.assignee else None
    statuses = [s.strip() for s in a.status.split(",")] if a.status else None
    today = dt.date.today()
    rows = []
    for it in items:
        c = it.get("content") or {}
        vals = {}
        for f in it.get("fields", []):
            v = f.get("value")
            if isinstance(v, dict):
                v = v["name"]["raw"] if isinstance(v.get("name"), dict) else v.get("name")
            vals[f["name"]] = v
        people = [x["login"] for x in c.get("assignees") or []]
        status = vals.get("Status") or "-"
        if not a.all and (status == "Done" or c.get("state") == "closed"):
            continue
        if statuses and status not in statuses:
            continue
        if a.part and vals.get("Part") != a.part:
            continue
        if login and login not in [p.lower() for p in people]:
            continue
        if who and not set(who) & {p.lower() for p in people}:
            continue
        due = vals.get("Target date")
        if a.due_within is not None:
            if not due or (dt.date.fromisoformat(due) - today).days > a.due_within:
                continue
        repo = (c.get("repository_url") or "").split("/repos/")[-1] or "draft"
        rows.append({"ref": f"{repo}#{c.get('number')}" if c.get("number") else "draft", "status": status,
                     "part": vals.get("Part"), "due": due, "priority": vals.get("Priority"),
                     "assignees": people, "title": c.get("title"), "url": c.get("html_url")})
    rows.sort(key=lambda r: (r["due"] or "9999-12-31", r["ref"]))
    if a.json:
        out(rows)
        return
    for r in rows:
        overdue = " ⚠지남" if r["due"] and r["due"] < today.isoformat() else ""
        print(f"{r['ref']} · {r['status']} · {r['part'] or '-'} · 마감 {r['due'] or '-'}{overdue} · "
              f"{r['priority'] or '-'} · {', '.join('@' + p for p in r['assignees']) or '담당 없음'} · {r['title']}")
    print(f"({len(rows)}건 · 보드 {BOARD_OWNER}#{BOARD_NUMBER})")


def cmd_task_update(a):
    me = whoami()
    meta = board_meta()
    check_task_args(meta, a)
    repo, number = parse_ref(a.ref)
    issue, item_id = issue_board_item(repo, number)
    mine = me["login"].lower() in [n["login"].lower() for n in issue["assignees"]["nodes"]]
    if not mine and not a.yes:
        out({"updated": False, "ref": f"{repo}#{number}", "title": issue["title"],
             "change": {k: v for k, v in (("status", a.status), ("part", a.part), ("due", a.due), ("priority", a.priority)) if v},
             "next": "내가 담당이 아닌 이슈다. 담당자나 사람의 승인을 받은 뒤에만 --yes 를 붙여 다시 실행한다."})
        return
    set_values(meta, repo, number, issue["databaseId"], item_id,
               status=a.status, part=a.part, due=a.due, priority=a.priority)
    out({"updated": True, "ref": f"{repo}#{number}", "url": issue["url"]})


def cmd_task_close(a):
    repo, number = parse_ref(a.ref)
    issue, _ = issue_board_item(repo, number)
    if issue["state"] == "CLOSED":
        out({"closed": True, "ref": f"{repo}#{number}", "note": "이미 닫혀 있다"})
        return
    reason = "not_planned" if a.not_planned else "completed"
    if a.comment:
        guard(a.comment, a.confirm_sensitive, "닫으며 남길 댓글")
    if not a.yes:
        out({"closed": False, "ref": f"{repo}#{number}", "title": issue["title"], "reason": reason,
             "comment": a.comment, "next": "사람의 승인을 받은 뒤에만 --yes 를 붙여 다시 실행한다."})
        return
    if a.comment:
        gh(["-X", "POST", f"repos/{repo}/issues/{number}/comments"], {"body": a.comment})
    gh(["-X", "PATCH", f"repos/{repo}/issues/{number}"], {"state": "closed", "state_reason": reason})
    out({"closed": True, "ref": f"{repo}#{number}", "reason": reason, "url": issue["url"]})


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description="전사 위키를 내려받지 않고 읽고 쓴다")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("whoami", help="전사 위키에서 내 이름·파트")
    p.add_argument("--refresh", action="store_true", help="캐시 무시")
    p.set_defaults(fn=cmd_whoami)

    p = sub.add_parser("daily-put", help="내 일일 리포트 공유본을 main 에 바로 올린다")
    p.add_argument("file")
    p.add_argument("--date", help="기본: frontmatter period")
    p.add_argument("--summary", help="활동 기록에 남길 한 줄 요약")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--confirm-sensitive", action="store_true",
                   help="기계 검사에 걸린 것을 사람이 확인하고 승인했을 때만")
    p.set_defaults(fn=cmd_daily_put)

    p = sub.add_parser("daily-get", help="그날 팀 일일 리포트 전부 + 안 쓴 사람")
    p.add_argument("--date", required=True)
    p.set_defaults(fn=cmd_daily_get)

    p = sub.add_parser("log-put", help="활동 기록 항목 하나를 log/ 에 올린다")
    p.add_argument("--op", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--slug", required=True, help="파일 이름용 kebab-case 영어")
    p.add_argument("--body-file")
    p.add_argument("--date")
    p.add_argument("--time", help='같은 날 순서용 "HH:MM"')
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--confirm-sensitive", action="store_true",
                   help="기계 검사에 걸린 것을 사람이 확인하고 승인했을 때만")
    p.set_defaults(fn=cmd_log_put)

    p = sub.add_parser("check", help="민감 정보 기계 검사만 (올리지 않음)")
    p.add_argument("file")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("get", help="파일 하나 읽기")
    p.add_argument("path")
    p.set_defaults(fn=cmd_get)

    p = sub.add_parser("mine-put", help="내 것(회의록·논문 원문·내 프로필·내 brain)을 main 에 바로 올린다 (--yes 없으면 미리보기)")
    p.add_argument("--file", action="append", required=True, help="'로컬파일:전사경로'. 여러 번 줄 수 있다")
    p.add_argument("--slug", required=True, help="활동 기록 파일 이름용 kebab-case 영어")
    p.add_argument("--op", default="ingest", help="활동 기록 op (ingest·meeting·profile 등)")
    p.add_argument("--title", required=True, help="활동 기록 제목")
    p.add_argument("--summary", help="활동 기록에 남길 한 줄")
    p.add_argument("--yes", action="store_true", help="사람이 미리보기를 보고 승인했을 때만")
    p.add_argument("--confirm-sensitive", action="store_true",
                   help="기계 검사에 걸린 것을 사람이 확인하고 승인했을 때만")
    p.set_defaults(fn=cmd_mine_put)

    p = sub.add_parser("wiki-pr", help="공용 지식·규칙 문서를 PR 로 올리고 리뷰어를 지정한다 (--yes 없으면 미리보기)")
    p.add_argument("--file", action="append", required=True, help="'로컬파일:전사경로'. 여러 번 줄 수 있다")
    p.add_argument("--title", required=True, help="PR 제목(활동 기록 제목으로도 쓴다)")
    p.add_argument("--body-file", help="PR 설명: 무엇을 / 왜 / 리뷰어가 볼 곳")
    p.add_argument("--slug", required=True, help="브랜치·활동 기록 이름용 kebab-case 영어")
    p.add_argument("--kind", default="ingest", choices=["ingest", "edit", "decision", "feature"],
                   help="브랜치 앞머리 (전사 §8)")
    p.add_argument("--op", default="ingest", help="활동 기록 op")
    p.add_argument("--reviewer", help="위키 이름(bley,jeremy) 또는 @계정. 공용 지식은 1명 이상")
    p.add_argument("--summary", help="활동 기록에 남길 한 줄")
    p.add_argument("--draft", action="store_true", help="초안 PR 로 연다")
    p.add_argument("--reuse-branch", action="store_true", help="같은 이름의 브랜치가 있고 PR 이 닫혀 있어도 이어서 쓴다")
    p.add_argument("--yes", action="store_true", help="사람이 미리보기를 보고 승인했을 때만")
    p.add_argument("--confirm-sensitive", action="store_true",
                   help="기계 검사에 걸린 것을 사람이 확인하고 승인했을 때만")
    p.set_defaults(fn=cmd_wiki_pr)

    p = sub.add_parser("task-new", help="공유 할 일을 GitHub issue 로 만들고 보드에 넣는다 (--yes 없으면 미리보기)")
    p.add_argument("--title", required=True)
    p.add_argument("--body-file", help="본문: 무엇을·왜 / 끝났다고 보는 기준 / 출처")
    p.add_argument("--repo", default=TASK_REPO, help=f"기본 {TASK_REPO}. 코드 PR 로 끝나는 일은 그 코드 저장소")
    p.add_argument("--part", help="ops·analysis·embedded·frontend·backend·org. 기본: 내 파트")
    p.add_argument("--status", default="Inbox", help="Idea·Inbox·Backlog·This week·In progress·Blocked·Done")
    p.add_argument("--due", help="마감 YYYY-MM-DD")
    p.add_argument("--priority", help="Urgent·High·Medium·Low")
    p.add_argument("--assignee", help="위키 이름(kevin,bley) 또는 @계정. 쉼표로 여럿")
    p.add_argument("--parent", help="상위 이슈 (12, owner/repo#12, 주소)")
    p.add_argument("--type", default="Task", help="Task·Bug·Feature")
    p.add_argument("--allow-duplicate", action="store_true", help="같은 제목의 열린 이슈가 있어도 만든다")
    p.add_argument("--yes", action="store_true", help="사람이 미리보기를 보고 승인했을 때만")
    p.add_argument("--confirm-sensitive", action="store_true",
                   help="기계 검사에 걸린 것을 사람이 확인하고 승인했을 때만")
    p.set_defaults(fn=cmd_task_new)

    p = sub.add_parser("task-list", help="보드의 할 일 목록 (기본: 끝나지 않은 것)")
    p.add_argument("--mine", action="store_true", help="내가 담당인 것만")
    p.add_argument("--assignee", help="위키 이름 또는 @계정. 쉼표로 여럿")
    p.add_argument("--part")
    p.add_argument("--status", help="쉼표로 여럿. 예: \"This week,In progress\"")
    p.add_argument("--due-within", type=int, help="오늘부터 N일 안에 마감(지난 것 포함)")
    p.add_argument("--all", action="store_true", help="Done·닫힌 것도 포함")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_task_list)

    p = sub.add_parser("task-update", help="상태·파트·마감·우선순위 바꾸기 (내 담당이 아니면 --yes 필요)")
    p.add_argument("ref")
    p.add_argument("--status")
    p.add_argument("--part")
    p.add_argument("--due")
    p.add_argument("--priority")
    p.add_argument("--yes", action="store_true", help="남의 이슈를 승인받고 바꿀 때")
    p.set_defaults(fn=cmd_task_update)

    p = sub.add_parser("task-close", help="할 일 닫기 (--yes 없으면 미리보기)")
    p.add_argument("ref")
    p.add_argument("--not-planned", action="store_true", help="하지 않기로 했을 때")
    p.add_argument("--comment", help="닫으며 남길 한 줄")
    p.add_argument("--yes", action="store_true", help="사람이 승인했을 때만")
    p.add_argument("--confirm-sensitive", action="store_true")
    p.set_defaults(fn=cmd_task_close)

    a = ap.parse_args()
    try:
        a.fn(a)
    except GhError as e:
        sys.exit(f"GitHub 요청 실패: {e}")


if __name__ == "__main__":
    main()
