#!/usr/bin/env python3
"""nas_slack.py — 전사 공용 슬랙 아카이브(NAS wiki-share)를 읽는 zero-dependency 스크립트.

공개 채널은 분석파트 워크스테이션이 매시 정각에 받아 개인정보를 가린 사본을 NAS 에 쌓는다
(전사 위키 wiki/playbooks/slack-archive.md). 이 스크립트는 그 사본을 **읽기만** 하고 NAS 에
쓰지 않는다. 개인 토큰 수집기(fetch_slack.py)는 여기 있는 채널을 받지 않는다.

사용 예:
  python nas_slack.py --check                          # 연결·채널·마지막 갱신 시각
  python nas_slack.py --pending --stats                # 지식화 대기 분량만
  python nas_slack.py --pending                        # 지식화 대기 메시지 (원문 링크 포함)
  python nas_slack.py --mark                           # 방금 --pending 으로 본 데까지 지식화 완료
  python nas_slack.py --since 2026-09-10 --until 2026-09-12 --channels issue,개발자
  python nas_slack.py --last-days 3
  python nas_slack.py --mark --at "2026-09-17 09:00"   # 커서를 특정 시각으로 맞춘다

커서는 둘이다. ingest 는 /slack-ingest 가, digest 는 무인 다이제스트(slack-fetch.ps1)가 쓴다.
커서는 채널 ID 기준이라 슬랙에서 채널 이름이 바뀌어도 이어진다.

NAS 위치: .env 의 SLACK_NAS_ROOT → channels.json 의 nas_root → OS 기본값
  Windows //192.168.0.225/wiki-share · macOS /Volumes/wiki-share · Linux /mnt/wiki-share
종료 코드: 0 정상 · 2 사용법 오류 · 3 NAS 에 닿지 않음(사내망·VPN 확인)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
WIKI_ROOT = SCRIPT_DIR.parent.parent
CHANNELS_FILE = SCRIPT_DIR / "channels.json"
CURSOR_FILE = SCRIPT_DIR / ".nas-cursor.json"
ROOT_ENV = WIKI_ROOT / ".env"
LOCAL_ENV = SCRIPT_DIR / ".env"

DEFAULT_ROOTS = {"win32": "//192.168.0.225/wiki-share", "darwin": "/Volumes/wiki-share"}
LINUX_ROOT = "/mnt/wiki-share"
CURSORS = ("ingest", "digest")
LOOKBACK_DAYS = 4        # 답글은 부모 날짜 파일에 붙고, 아카이브는 지난 3일치를 다시 쓴다
FIRST_RUN_DAYS = 7       # 커서가 없을 때 거슬러 볼 기간
TOKEN_WARN = 20000       # 이보다 많으면 채널을 좁힐지 먼저 묻는다
STALE_HOURS = 2          # 매시 갱신이므로 이보다 오래되면 수집이 멈춘 것

SOURCE_RE = re.compile(r"^> source: (https?://[^/\s]+)/archives/([A-Z0-9]+)/", re.M)
HEAD_RE = re.compile(
    r"^\s*(↳\s*)?\*\*(\d{1,2}:\d{2})\s+(.*?)\s*\*\*\s*(?:`p(\d{10})(\d{6})`)?\s*$")
ANCHOR_RE = re.compile(r"`p\d{16}`")
ATTACH_RE = re.compile(r"^📎\s*\*\*(.+?)\*\*\s*(\([^)]*\))?.*$")
DATE_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")


# --------------------------------------------------------------------------- env / io
def _read_env(path, env):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")


def load_env():
    env = {}
    _read_env(ROOT_ENV, env)
    _read_env(LOCAL_ENV, env)
    return env


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return default


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- nas
def nas_root(config=None):
    config = load_json(CHANNELS_FILE, {}) if config is None else config
    root = load_env().get("SLACK_NAS_ROOT") or config.get("nas_root")
    return Path(root or DEFAULT_ROOTS.get(sys.platform, LINUX_ROOT))


def reachable(root):
    try:
        return root.is_dir() and any(True for _ in os.scandir(root))
    except OSError:
        return False


def _date_files(path):
    try:
        return sorted(e.name for e in os.scandir(path) if DATE_FILE_RE.match(e.name))
    except OSError:
        return []


def list_channels(root):
    """NAS 의 채널 폴더 → {이름: 채널 ID}. 파일 머리의 source 줄에서 ID 를 읽는다."""
    out = {}
    for e in sorted(os.scandir(root), key=lambda e: e.name):
        if not e.is_dir() or e.name.startswith(("_", "#", ".", "@")):
            continue
        cid = None
        for name in reversed(_date_files(e.path)):      # 최신 파일부터 본다
            try:
                with open(os.path.join(e.path, name), encoding="utf-8") as fh:
                    m = SOURCE_RE.search(fh.read(800))
            except OSError:
                continue
            if m:
                cid = m.group(2)
                break
        out[e.name] = cid
    return out


def covered_channels(config, save=True):
    """개인 토큰 수집에서 뺄 채널을 낸다: (이름 집합, ID 집합, NAS 에 닿았는지).

    NAS 에 닿으면 목록을 새로 읽어 channels.json 의 _nas_channels 에 캐시한다. 재택이거나 VPN 이
    끊겨 닿지 않으면 마지막 캐시를 쓴다. 그 채널들은 NAS 가 계속 받고 있으므로, 연결되지 않았다고
    개인 토큰으로 받을 이유가 없다.
    """
    root = nas_root(config)
    live = reachable(root)
    chans = config.get("_nas_channels", {})
    if live:
        fresh = list_channels(root)
        if fresh and fresh != chans:
            chans = fresh
            config["_nas_channels"] = fresh
            if save:
                disk = load_json(CHANNELS_FILE, {})
                disk["_nas_channels"] = fresh
                save_json(CHANNELS_FILE, disk)
    return set(chans), {v for v in chans.values() if v}, live


def last_update(root):
    stamps = []
    for p in [root / "README.md"] + [Path(e.path) for e in os.scandir(root) if e.is_dir()]:
        try:
            stamps.append(p.stat().st_mtime)
        except OSError:
            pass
    return max(stamps) if stamps else None


# --------------------------------------------------------------------------- parse
class Msg:
    __slots__ = ("channel", "cid", "domain", "day", "time", "who", "ts", "anchor",
                 "reply", "parent", "body")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def link(self):
        if not (self.anchor and self.domain and self.cid):
            return None
        return f"{self.domain}/archives/{self.cid}/{self.anchor}"

    def when(self):
        """답글은 부모 날짜 파일에 들어가므로, 날짜가 다르면 날짜까지 보인다."""
        real = datetime.fromtimestamp(self.ts).strftime("%Y-%m-%d")
        return self.time if real == self.day else f"{real[5:]} {self.time}"


def _approx_ts(day, hhmm):
    return datetime.strptime(f"{day} {hhmm}", "%Y-%m-%d %H:%M").timestamp()


def _clean_body(lines, reply):
    out = []
    for line in lines:
        s = line[6:] if reply and line.startswith("      ") else line
        s = s.rstrip()
        if not s.strip():
            continue
        m = ATTACH_RE.match(s.strip())
        if m:      # 첨부 파일 주소는 옮기지 않는다. 메시지 링크로 가면 파일도 보인다.
            s = f"📎 {m.group(1)} {m.group(2) or ''}".rstrip()
        out.append(s)
    return out


def parse_file(path, channel, cid_hint):
    text = path.read_text(encoding="utf-8")
    src = SOURCE_RE.search(text)
    domain, cid = (src.group(1), src.group(2)) if src else (None, cid_hint)
    strict = bool(ANCHOR_RE.search(text))   # 앵커가 있는 파일은 앵커 달린 줄만 메시지 머리로 본다
    day = path.stem
    msgs, cur, parent, buf = [], None, None, []

    def close():
        if cur is not None:
            cur.body = _clean_body(buf, cur.reply)

    for line in text.splitlines():
        h = HEAD_RE.match(line)
        if h and (h.group(4) or not strict):
            close()
            buf = []
            reply = bool(h.group(1))
            if h.group(4):
                ts, anchor = float(f"{h.group(4)}.{h.group(5)}"), f"p{h.group(4)}{h.group(5)}"
            else:
                ts, anchor = _approx_ts(day, h.group(2)), None
            cur = Msg(channel=channel, cid=cid, domain=domain, day=day, time=h.group(2),
                      who=h.group(3), ts=ts, anchor=anchor, reply=reply,
                      parent=parent if reply else None)
            if not reply:
                parent = cur
            msgs.append(cur)
        elif cur is not None:
            buf.append(line)
    close()
    return msgs


# --------------------------------------------------------------------------- select
def _day(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def _key(name, cid):
    return cid or f"name:{name}"


def collect(root, channels, wanted, since_day, until_day, after=None):
    """조건에 맞는 메시지를 채널별로 모은다. after 가 있으면 채널별 커서 이후 메시지만."""
    picked = []
    for name, cid in channels.items():
        if wanted and name not in wanted:
            continue
        start = after(name, cid) if after else None
        lo = _day(start - LOOKBACK_DAYS * 86400) if start else since_day
        for fname in _date_files(root / name):
            day = fname[:10]
            if (lo and day < lo) or (until_day and day > until_day):
                continue
            try:
                msgs = parse_file(root / name / fname, name, cid)
            except (OSError, UnicodeDecodeError) as e:
                sys.stderr.write(f"  ⚠ {name}/{fname} 을 읽지 못함: {e}\n")
                continue
            picked += [m for m in msgs if start is None or m.ts > start]
    return picked


def render(msgs, title, note):
    chosen = {id(m) for m in msgs}
    by_ch = {}
    for m in msgs:
        by_ch.setdefault(m.channel, {}).setdefault(m.day, []).append(m)
    lines = [f"# {title}", f"> {note}",
             "> 기계가 가린 미검증 사본이다. 숫자·결론은 [↗] 링크로 슬랙 원문을 확인한 뒤 확정한다."
             " `{SECRET}`·`{TEL_…}` 같은 토큰은 복원할 수 없다.", ""]
    per_ch = {}
    for ch in sorted(by_ch):
        start = len(lines)
        lines.append(f"## #{ch}")
        for day in sorted(by_ch[ch]):
            lines.append(f"### {day}")
            for m in by_ch[ch][day]:
                link = m.link()
                tail = f" [↗]({link})" if link else " (원문 링크 없음)"
                if m.reply:
                    ctx = ""
                    if m.parent is not None and id(m.parent) not in chosen:
                        first = (m.parent.body or [""])[0][:60]
                        ctx = f" — 스레드 원글: {m.parent.time} {m.parent.who} \"{first}\""
                    lines.append(f"  - ↳ {m.when()} **{m.who}**{tail}{ctx}")
                    lines += [f"    {b}" for b in m.body]
                else:
                    lines.append(f"- {m.when()} **{m.who}**{tail}")
                    lines += [f"  {b}" for b in m.body]
        lines.append("")
        per_ch[ch] = (sum(1 for d in by_ch[ch].values() for _ in d),
                      len("\n".join(lines[start:]).encode("utf-8")) // 3)
    return "\n".join(lines), per_ch


def print_stats(per_ch):
    total_m = sum(v[0] for v in per_ch.values())
    total_t = sum(v[1] for v in per_ch.values())
    for ch, (n, t) in sorted(per_ch.items(), key=lambda kv: -kv[1][1]):
        print(f"  #{ch}: {n}건 · 약 {t:,} 토큰")
    print(f"합계: {total_m}건 / {len(per_ch)}개 채널 · 약 {total_t:,} 토큰")
    if total_t > TOKEN_WARN:
        print(f"⚠ {TOKEN_WARN:,} 토큰을 넘는다. 읽기 전에 채널을 좁힐지(--channels) 먼저 정한다.")


# --------------------------------------------------------------------------- cursor
def load_cursor():
    data = load_json(CURSOR_FILE, {})
    for c in CURSORS:
        data.setdefault(c, {})
    data.setdefault("_pending", {})
    return data


def cursor_getter(cur, which):
    default = cur[which].get("_default")
    if default is None:
        default = (datetime.now() - timedelta(days=FIRST_RUN_DAYS)).timestamp()

    def get(name, cid):
        return cur[which].get(_key(name, cid), default)
    return get


def mark(cur, which, at=None, channels=None):
    if at:
        ts = datetime.strptime(at, "%Y-%m-%d %H:%M").timestamp()
        for name, cid in (channels or {}).items():
            cur[which][_key(name, cid)] = ts
        cur[which]["_default"] = ts
        cur["_pending"].pop(which, None)
        save_json(CURSOR_FILE, cur)
        print(f"{which} 커서를 {at} 로 맞췄다 (채널 {len(channels or {})}개)")
        return 0
    snap = cur["_pending"].pop(which, None)
    if snap is None:
        print(f"먼저 --pending --cursor {which} 로 대기분을 보세요. "
              "본 적 없는 메시지를 건너뛰지 않으려고, 본 데까지만 전진시킵니다.")
        return 2
    moved = 0
    for k, ts in snap.get("upto", {}).items():
        if ts > cur[which].get(k, 0):
            cur[which][k] = ts
            moved += 1
    save_json(CURSOR_FILE, cur)
    print(f"{which} 커서 전진: 채널 {moved}개 ({snap.get('at', '?')} 에 본 데까지)")
    return 0


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="전사 공용 슬랙 아카이브(NAS)를 읽는다")
    ap.add_argument("--check", action="store_true", help="연결·채널·마지막 갱신 시각 확인")
    ap.add_argument("--pending", action="store_true", help="커서 이후 메시지")
    ap.add_argument("--mark", action="store_true", help="--pending 으로 본 데까지 커서 전진")
    ap.add_argument("--cursor", choices=CURSORS, default="ingest",
                    help="ingest(/slack-ingest, 기본) 또는 digest(무인 다이제스트)")
    ap.add_argument("--at", help='--mark 와 함께: 커서를 "YYYY-MM-DD HH:MM" 로 맞춘다')
    ap.add_argument("--since", help="시작일 YYYY-MM-DD (날짜 파일 기준)")
    ap.add_argument("--until", help="종료일 YYYY-MM-DD (포함)")
    ap.add_argument("--last-days", type=int, help="최근 N일 (오늘 포함)")
    ap.add_argument("--channels", help="쉼표로 구분한 채널 이름")
    ap.add_argument("--stats", action="store_true", help="메시지 대신 분량만 출력")
    ap.add_argument("--out", help="본문을 이 파일에 쓰고 요약만 출력")
    args = ap.parse_args()

    config = load_json(CHANNELS_FILE, {})
    root = nas_root(config)
    if not reachable(root):
        print(f"NAS 에 닿지 않는다: {root}\n"
              "사내망인지(재택이면 VPN) 확인하고, Windows 는 탐색기에서 \\\\192.168.0.225\\wiki-share,"
              " macOS 는 Finder ⌘K 로 smb://192.168.0.225/wiki-share 에 한 번 로그인한다."
              " 경로가 다르면 .env 에 SLACK_NAS_ROOT 를 적는다.")
        return 3

    channels = list_channels(root)
    if channels != config.get("_nas_channels") and CHANNELS_FILE.exists():
        config["_nas_channels"] = channels
        save_json(CHANNELS_FILE, config)
    wanted = {c.strip().lstrip("#") for c in (args.channels or "").split(",") if c.strip()}
    unknown = wanted - set(channels)
    if unknown:
        sys.stderr.write(f"  ⚠ NAS 에 없는 채널: {', '.join(sorted(unknown))}"
                         " (비공개 채널이거나 아직 수집 대상이 아니다)\n")

    if args.check:
        upd = last_update(root)
        age = (datetime.now().timestamp() - upd) / 3600 if upd else None
        print(f"NAS: {root} (연결됨)")
        if upd:
            flag = "  ⚠ 수집이 멈춘 것 같다 — 분석파트에 알린다" if age > STALE_HOURS else ""
            print(f"마지막 갱신: {datetime.fromtimestamp(upd):%Y-%m-%d %H:%M} ({age:.1f}시간 전){flag}")
        print(f"채널 {len(channels)}개:")
        for name, cid in channels.items():
            files = _date_files(root / name)
            span = f"{files[0][:10]}..{files[-1][:10]}" if files else "-"
            print(f"  #{name}  {cid or '(ID 없음)'}  파일 {len(files)}  {span}")
        ids = config.get("_id_cache", {})
        cids = {v for v in channels.values() if v}
        dup = [c for c in config.get("include", []) if c in channels or ids.get(c) in cids]
        if dup:
            print(f"\n개인 토큰 수집(fetch_slack.py)이 건너뛰는 include 채널 {len(dup)}개: {', '.join(dup)}")
        return 0

    cur = load_cursor()
    if args.mark:
        return mark(cur, args.cursor, args.at, channels)

    if args.pending:
        get = cursor_getter(cur, args.cursor)
        msgs = collect(root, channels, wanted, None, None, after=get)
        title = f"슬랙 공용 아카이브 — 대기분 ({args.cursor} 커서 이후)"
    else:
        if args.last_days:
            since = (datetime.now() - timedelta(days=args.last_days - 1)).strftime("%Y-%m-%d")
            until = datetime.now().strftime("%Y-%m-%d")
        elif args.since:
            since, until = args.since, args.until or args.since
        else:
            print("--pending, --since, --last-days, --check, --mark 중 하나를 주세요.")
            return 2
        msgs = collect(root, channels, wanted, since, until)
        title = f"슬랙 공용 아카이브 — {since}..{until}"
    msgs.sort(key=lambda m: (m.channel, m.day, m.parent.ts if m.parent else m.ts, m.ts))

    note = f"NAS {root} · 메시지 {len(msgs)}건 · 읽은 시각 {datetime.now():%Y-%m-%d %H:%M}"
    text, per_ch = render(msgs, title, note)

    if args.pending and not args.stats:
        upto = {}
        for m in msgs:
            k = _key(m.channel, m.cid)
            upto[k] = max(upto.get(k, 0), m.ts)
        cur["_pending"][args.cursor] = {"at": f"{datetime.now():%Y-%m-%d %H:%M}", "upto": upto}
        save_json(CURSOR_FILE, cur)

    if not msgs:
        print("(새 메시지 없음)" if args.pending else "(해당 기간 메시지 없음)")
        return 0
    if args.stats:
        print_stats(per_ch)
        return 0
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        kind = "대기" if args.pending else "메시지"
        print(f"NAS {kind} {len(msgs)}건 / {len(per_ch)}개 채널 → {args.out}")
        return 0
    print(text)
    if args.pending:
        print(f"→ 다 반영했으면 `python tools/slack-ingest/nas_slack.py --mark"
              f"{'' if args.cursor == 'ingest' else ' --cursor ' + args.cursor}` 로 커서를 전진시킨다."
              " 중간에 끊었으면 전진시키지 않는다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
