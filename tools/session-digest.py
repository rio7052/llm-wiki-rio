#!/usr/bin/env python3
"""session-digest.py — Claude Code 세션 transcript 를 압축 digest 로 뽑는다 (2026-08-22)

목적: `/log` 가 "내가 뭘 했는지" 를 사람에게 묻지 않고 **세션에서 직접 읽어** 쓰게 한다.
transcript 원본은 세션당 수백 KB~수십 MB 라 LLM 컨텍스트에 못 싣는다 — 이 스크립트가
사용자 발화 + 실제 수행 액션(파일 편집·명령·커밋)만 남겨 수십 KB 로 줄인다.

사용:
  python tools/session-digest.py --since 2026-08-22T09:00:00      # 시각 이후
  python tools/session-digest.py --since-hours 3                  # 최근 N시간
  python tools/session-digest.py --since-file .log-cursor         # 커서 파일 이후 (기본)
  python tools/session-digest.py --since-hours 24 --out digest.md # 파일로

원칙:
- **읽기 전용**. ~/.claude/projects 도 raw/sessions 도 수정하지 않는다.
- 시간 창이 아니라 **커서 기준** — 6시간 만에 돌려도 6시간분을 전부 훑는다(누락 없음).
- 모든 레포를 가로지른다. 어느 워크스페이스에서 작업했든 한 번에 잡힌다.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 잡음 툴 — 무엇을 했는지 알려주지 않는다
SKIP_TOOLS = {"TodoWrite", "Read", "Glob", "Grep", "ToolSearch", "NotebookRead", "ListAgents"}
# 액션 툴 — 파일/시스템을 실제로 바꾼 것
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
RUN_TOOLS = {"Bash", "PowerShell"}


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def as_text(content):
    """message.content(str | list[block]) → (본문 텍스트, 툴사용 리스트)"""
    if isinstance(content, str):
        return content, []
    text_parts, tools = [], []
    if isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "text":
                text_parts.append(b.get("text", ""))
            elif t == "tool_use":
                tools.append((b.get("name", ""), b.get("input", {}) or {}))
            elif t == "thinking":
                pass  # 생각은 digest 에 안 넣는다
    return "\n".join(text_parts), tools


# 사람이 친 말이 아닌 것 — 자동 주입 블록
NOISE_RE = re.compile(
    r"<task-notification>|<system-reminder>|\[Request interrupted|"
    r"^\s*<local-command-std|^\s*Caveat:", re.M)
# 대화 내용이 아닌 메타 커맨드 — 로그에 남길 가치가 없다
META_CMDS = {"compact", "clear", "cost", "status", "model", "resume", "exit", "help"}


def clean_user_text(txt):
    """슬래시커맨드 래퍼·시스템 리마인더·훅 출력 제거. 사람이 실제로 친 말만."""
    if not txt:
        return ""
    # 자동 주입 알림(task-notification 등)은 사람 발화가 아니다
    if NOISE_RE.search(txt) and "<command-name>" not in txt:
        return ""
    # 슬래시 커맨드는 이름만 남긴다
    m = re.search(r"<command-name>([^<]+)</command-name>", txt)
    cmd = m.group(1).strip().lstrip("/") if m else None
    if cmd and cmd in META_CMDS:
        return ""
    # 컴팩트 이후 자동 주입되는 요약 — 사람 발화가 아니다
    if txt.lstrip().startswith("This session is being continued from"):
        return ""
    # 래퍼 없이 그대로 남은 메타 커맨드
    if txt.strip().lstrip("/").split()[0:1] and txt.strip().lstrip("/").split()[0] in META_CMDS and len(txt.strip()) < 20:
        return ""
    args = None
    m2 = re.search(r"<command-args>([^<]*)</command-args>", txt)
    if m2 and m2.group(1).strip():
        args = m2.group(1).strip()
    if cmd:
        return f"[{cmd}{' ' + args if args else ''}]"
    txt = re.sub(r"<system-reminder>.*?</system-reminder>", "", txt, flags=re.S)
    txt = re.sub(r"<local-command-[a-z]+>.*?</local-command-[a-z]+>", "", txt, flags=re.S)
    txt = re.sub(r"<command-message>.*?</command-message>", "", txt, flags=re.S)
    txt = re.sub(r"<[a-z-]+-caveat>.*?</[a-z-]+-caveat>", "", txt, flags=re.S)
    return txt.strip()


def short(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def repo_of(cwd, slug):
    if cwd:
        return Path(cwd).name
    return slug


def scan(path, since, until, max_user, user_chars):
    """jsonl 1개 → 세션 요약 dict (창 안에 활동 없으면 None)"""
    users, edits, cmds, commits = [], [], [], []
    title, cwd, branch, slug = None, None, None, path.parent.name
    first_ts = last_ts = None
    n_sidechain = 0

    try:
        fh = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return None

    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue

            if o.get("aiTitle") and not title:
                title = o["aiTitle"]
            if o.get("cwd") and not cwd:
                cwd = o["cwd"]
            if o.get("gitBranch") and not branch:
                branch = o["gitBranch"]

            ts = parse_ts(o.get("timestamp"))
            if ts is None or ts < since:
                continue
            if until is not None and ts >= until:
                continue
            first_ts = ts if first_ts is None else min(first_ts, ts)
            last_ts = ts if last_ts is None else max(last_ts, ts)

            typ = o.get("type")
            msg = o.get("message") or {}
            side = bool(o.get("isSidechain"))

            if typ == "user" and not o.get("isMeta"):
                if side:
                    n_sidechain += 1
                    continue
                txt, _ = as_text(msg.get("content"))
                txt = clean_user_text(txt)
                if txt and len(txt) > 1:
                    users.append((ts, short(txt, user_chars)))

            elif typ == "assistant":
                _, tools = as_text(msg.get("content"))
                for name, inp in tools:
                    if name in SKIP_TOOLS:
                        continue
                    if name in EDIT_TOOLS:
                        fp = inp.get("file_path") or inp.get("notebook_path") or ""
                        if fp:
                            edits.append(Path(fp).name if len(fp) > 60 else fp)
                    elif name in RUN_TOOLS:
                        c = (inp.get("command") or "").strip()
                        head = c.splitlines()[0] if c else ""
                        if "git commit" in c:
                            m = re.search(r"-m\s+['\"]?([^'\"\n]{4,120})", c)
                            commits.append(m.group(1).strip() if m else "git commit")
                        elif head:
                            cmds.append(short(head, 90))
                    elif name == "Agent":
                        d = inp.get("description") or ""
                        if d:
                            cmds.append(f"[subagent] {short(d, 70)}")

    if first_ts is None:
        return None

    # 사용자 발화는 앞뒤를 살린다 — 중간은 접는다
    if len(users) > max_user:
        keep = max_user // 2
        users = users[:keep] + [(None, f"…({len(users) - max_user}줄 생략)…")] + users[-keep:]

    return {
        "slug": slug,
        "repo": repo_of(cwd, slug),
        "branch": branch,
        "title": title,
        "first": first_ts,
        "last": last_ts,
        "users": users,
        "edits": edits,
        "cmds": cmds,
        "commits": commits,
        "sidechain": n_sidechain,
        "path": str(path),
    }


def dedup_keep_order(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--since", help="ISO 시각 (예: 2026-08-22T09:00:00)")
    ap.add_argument("--until", help="ISO 시각 — 이 시각 이전까지만 (백필용 구간 지정)")
    ap.add_argument("--day", help="특정 하루만 (YYYY-MM-DD). --since/--until 을 그날 00:00~24:00 으로 설정")
    ap.add_argument("--since-hours", type=float, help="최근 N시간")
    ap.add_argument("--since-file", help="이 파일에 적힌 ISO 시각 이후 (커서)")
    ap.add_argument("--out", help="결과를 이 파일에 쓴다 (기본 stdout)")
    ap.add_argument("--max-user", type=int, default=40, help="세션당 사용자 발화 최대 줄수")
    ap.add_argument("--user-chars", type=int, default=300, help="발화 1줄 최대 글자수")
    ap.add_argument("--exclude-session", help="제외할 session-id (진행 중인 회고 세션 자신)")
    ap.add_argument("--write-cursor", help="완료 후 이 파일에 현재 시각을 커서로 기록")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    local_tz = datetime.now().astimezone().tzinfo
    if args.day:
        d = datetime.strptime(args.day, "%Y-%m-%d").replace(tzinfo=local_tz)
        args.since, args.until = d.isoformat(), (d + timedelta(days=1)).isoformat()

    since = None
    if args.since:
        since = parse_ts(args.since)
        if since and since.tzinfo is None:
            since = since.astimezone()
    elif args.since_hours:
        since = now - timedelta(hours=args.since_hours)
    elif args.since_file and Path(args.since_file).exists():
        # utf-8-sig: PowerShell 의 Set-Content -Encoding utf8 은 BOM 을 붙인다.
        # 그냥 utf-8 로 읽으면 '﻿' 가 남아 fromisoformat 이 실패한다.
        raw_cursor = Path(args.since_file).read_text(encoding="utf-8-sig").strip()
        since = parse_ts(raw_cursor)
        if since is None:
            # 조용히 24시간으로 떨어지면 커서가 무시된 걸 아무도 모른다 — 반드시 알린다
            print(f"warn: 커서를 못 읽었다 ({args.since_file!r}: {raw_cursor[:40]!r}) — 기본 창으로 대체",
                  file=sys.stderr)
    if since is None:
        since = now - timedelta(hours=24)
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)

    until = parse_ts(args.until) if args.until else None
    if until is not None and until.tzinfo is None:
        until = until.replace(tzinfo=local_tz)

    src = Path(args.source)
    if not src.exists():
        print(f"source not found: {src}", file=sys.stderr)
        return 1

    sessions = []
    for p in src.rglob("*.jsonl"):
        if "memory" in p.parts:
            continue
        if args.exclude_session and args.exclude_session in p.name:
            continue
        try:
            if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) < since:
                continue  # 창 이후 안 건드려진 파일은 파싱조차 안 한다
        except OSError:
            continue
        s = scan(p, since, until, args.max_user, args.user_chars)
        if s and (s["users"] or s["edits"] or s["cmds"] or s["commits"]):
            sessions.append(s)

    sessions.sort(key=lambda s: s["first"])

    L = []
    local_since = since.astimezone()
    if until is not None:
        L.append(f"# 세션 digest — {local_since:%Y-%m-%d %H:%M} ~ {until.astimezone():%Y-%m-%d %H:%M}")
    else:
        L.append(f"# 세션 digest — {local_since:%Y-%m-%d %H:%M} 이후 (생성 {now.astimezone():%Y-%m-%d %H:%M})")
    L.append("")
    if not sessions:
        L.append("_이 구간에 활동 없음._")
    else:
        repos = dedup_keep_order([s["repo"] for s in sessions])
        L.append(f"세션 {len(sessions)}개 · 레포 {len(repos)}개: {', '.join(repos)}")
        L.append("")

    for s in sessions:
        head = f"## {s['repo']}"
        if s["branch"] and s["branch"] not in ("main", "master"):
            head += f" ({s['branch']})"
        L.append(head)
        f_lo, l_lo = s["first"].astimezone(), s["last"].astimezone()
        if f_lo.date() == l_lo.date():
            meta = f"{f_lo:%m-%d %H:%M}–{l_lo:%H:%M}"
        else:
            meta = f"{f_lo:%m-%d %H:%M}–{l_lo:%m-%d %H:%M}"
        if s["title"]:
            meta += f" · {s['title']}"
        if s["sidechain"]:
            meta += f" · subagent {s['sidechain']}회"
        L.append(f"_{meta}_")
        L.append("")

        if s["users"]:
            L.append("**내가 시킨 것**")
            tfmt = "%H:%M" if f_lo.date() == l_lo.date() else "%m-%d %H:%M"
            for ts, t in s["users"]:
                L.append(f"- {ts.astimezone():{tfmt}} {t}" if ts else f"- {t}")
            L.append("")
        if s["commits"]:
            L.append("**커밋**")
            for c in dedup_keep_order(s["commits"]):
                L.append(f"- {c}")
            L.append("")
        edits = dedup_keep_order(s["edits"])
        if edits:
            L.append(f"**편집한 파일** ({len(edits)})")
            for e in edits[:25]:
                L.append(f"- {e}")
            if len(edits) > 25:
                L.append(f"- …외 {len(edits) - 25}개")
            L.append("")
        cmds = dedup_keep_order(s["cmds"])
        if cmds:
            L.append(f"**실행** ({len(cmds)})")
            for c in cmds[:15]:
                L.append(f"- `{c}`")
            if len(cmds) > 15:
                L.append(f"- …외 {len(cmds) - 15}개")
            L.append("")

    out = "\n".join(L) + "\n"
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8", newline="\n")
        print(f"digest → {args.out} ({len(sessions)} sessions, {len(out)} chars)")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(out)

    if args.write_cursor:
        Path(args.write_cursor).write_text(now.isoformat(), encoding="utf-8", newline="\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
