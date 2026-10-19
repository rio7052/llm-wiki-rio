#!/usr/bin/env python3
"""fetch_slack.py — Slack 채널 메시지를 raw/slack/ 로 수집하는 zero-dependency 스크립트.

표준 라이브러리만 사용(urllib). Slack Web API(conversations.history/replies,
conversations.list, users.list)를 호출해 지정 채널×기간의 메시지를 일자별 markdown
으로 raw/slack/<channel>/YYYY-MM-DD.md 에 저장한다. raw/** 는 .gitignore 처리되어
원문은 로컬에만 남는다(PII 보호).

사용 예:
  python fetch_slack.py --since 2026-06-12 --until 2026-06-17
  python fetch_slack.py --since 2026-06-16 --until 2026-06-16            # 특정 하루
  python fetch_slack.py --last-days 7                                    # 지난 7일
  python fetch_slack.py --since-cursor                                   # 지난번 이후~지금
  python fetch_slack.py --channels 개발자,분석-백엔드 --since 2026-06-12 --until 2026-06-17
  python fetch_slack.py --list-channels                                  # 워크스페이스 채널 목록만 출력

기간을 안 주면 --since-cursor 로 동작한다(커서 없으면 에러).

공개 채널은 전사 공용 아카이브(NAS wiki-share)가 이미 받아 개인정보를 가려 둔다. 그래서 이 수집기는
NAS 에 있는 채널을 **받지 않는다**(채널 ID 로 판정하므로 이름이 바뀌어도 맞는다). NAS 는
nas_slack.py 로 읽는다. 일부러 받아야 할 때만 --include-nas 를 붙인다.
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows 콘솔(cp949)에서 ⚠ 등 비-ASCII 출력 시 UnicodeEncodeError 방지.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
WIKI_ROOT = SCRIPT_DIR.parent.parent          # tools/slack-ingest -> tools -> wiki root
sys.path.insert(0, str(SCRIPT_DIR))           # 같은 폴더의 nas_slack
import nas_slack                              # noqa: E402  NAS 공용 아카이브에 있는 채널 판정
sys.path.insert(0, str(SCRIPT_DIR.parent))    # tools/ 의 공용 모듈(secret_mask)
import secret_mask                            # noqa: E402  자격 증명 가리기(계정·비밀번호·키)
OUT_ROOT = WIKI_ROOT / "raw" / "slack"
CHANNELS_FILE = SCRIPT_DIR / "channels.json"
CURSOR_FILE = SCRIPT_DIR / ".cursor.json"
USERS_CACHE = SCRIPT_DIR / ".users_cache.json"
# 시크릿 우선순위: 위키 루트 .env(공용) → 도구 로컬 .env(override). 둘 중 있는 걸 쓴다.
ROOT_ENV = WIKI_ROOT / ".env"
LOCAL_ENV = SCRIPT_DIR / ".env"
API = "https://slack.com/api/"


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
    """위키 루트 .env 를 먼저 읽고, 도구 로컬 .env 가 있으면 덮어쓴다."""
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
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- slack api
class Slack:
    def __init__(self, token):
        self.token = token

    def call(self, method, params):
        url = API + method + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": "Bearer " + self.token})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = int(e.headers.get("Retry-After", "5"))
                    sys.stderr.write(f"  rate-limited, {wait}s 대기...\n")
                    time.sleep(wait + 1)
                    continue
                raise
            if data.get("ok"):
                return data
            err = data.get("error", "unknown")
            if err == "ratelimited":
                time.sleep(5)
                continue
            raise RuntimeError(f"Slack API {method} 실패: {err}")
        raise RuntimeError(f"Slack API {method} 재시도 초과")

    def paginate(self, method, params, key):
        cursor = ""
        while True:
            p = dict(params)
            if cursor:
                p["cursor"] = cursor
            data = self.call(method, p)
            for item in data.get(key, []):
                yield item
            cursor = data.get("response_metadata", {}).get("next_cursor", "")
            if not cursor:
                break


# --------------------------------------------------------------------------- helpers
def to_ts(date_str, end_of_day=False):
    """YYYY-MM-DD (로컬) -> unix ts (float)."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    if end_of_day:
        d = d.replace(hour=23, minute=59, second=59, microsecond=999999)
    return d.timestamp()


def local_date(ts, tzinfo):
    return datetime.fromtimestamp(float(ts), tz=tzinfo).strftime("%Y-%m-%d")


def local_time(ts, tzinfo):
    return datetime.fromtimestamp(float(ts), tz=tzinfo).strftime("%H:%M")


MENTION_RE = re.compile(r"<@([A-Z0-9]+)>")
CHAN_RE = re.compile(r"<#[A-Z0-9]+\|([^>]+)>")
SUBTEAM_LBL_RE = re.compile(r"<!subteam\^[^>|]+\|([^>]+)>")
SUBTEAM_RE = re.compile(r"<!subteam\^[^>]+>")
SPECIAL_RE = re.compile(r"<!(here|channel|everyone)>")
LINK_LBL_RE = re.compile(r"<(https?://[^|>]+)\|([^>]+)>")
LINK_RE = re.compile(r"<(https?://[^>]+)>")


def clean_text(text, users):
    if not text:
        return ""
    text = MENTION_RE.sub(lambda m: "@" + users.get(m.group(1), m.group(1)), text)
    text = CHAN_RE.sub(lambda m: "#" + m.group(1), text)
    text = SUBTEAM_LBL_RE.sub(lambda m: "@" + m.group(1).lstrip("@"), text)
    text = SUBTEAM_RE.sub("@group", text)
    text = SPECIAL_RE.sub(lambda m: "@" + m.group(1), text)
    text = LINK_LBL_RE.sub(lambda m: m.group(2), text)   # 라벨만 남기고 URL 제거
    text = LINK_RE.sub(lambda m: m.group(1), text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text


def author(msg, users):
    if msg.get("user"):
        return users.get(msg["user"], msg["user"])
    return msg.get("username") or msg.get("bot_id") or "?"


# --------------------------------------------------------------------------- main flow
def resolve_channels(slack, wanted, cache):
    """채널명 리스트를 ID 로 해석. cache 미스만 conversations.list 로 채우고 _id_cache 만 영속화."""
    missing = [c for c in wanted if c not in cache]
    if missing:
        sys.stderr.write("채널 목록 조회 중(conversations.list)...\n")
        name_to_id = {}
        for ch in slack.paginate(
            "conversations.list",
            {"types": "public_channel,private_channel", "limit": 1000, "exclude_archived": "false"},
            "channels",
        ):
            name_to_id[ch["name"]] = ch["id"]
        for c in missing:
            if c in name_to_id:
                cache[c] = name_to_id[c]
            else:
                sys.stderr.write(f"  ⚠ 채널 '{c}' 를 워크스페이스에서 못 찾음(이름 확인 또는 봇 초대 필요)\n")
        # 디스크의 channels.json 은 _id_cache 만 갱신(include/exclude 보존)
        cfg = load_json(CHANNELS_FILE, {})
        cfg["_id_cache"] = cache
        save_json(CHANNELS_FILE, cfg)
    return [(c, cache[c]) for c in wanted if c in cache]


def load_users(slack, refresh=False):
    users = load_json(USERS_CACHE, {})
    if users and not refresh:
        return users
    sys.stderr.write("유저 목록 조회 중(users.list)...\n")
    users = {}
    for u in slack.paginate("users.list", {"limit": 500}, "members"):
        prof = u.get("profile", {})
        name = prof.get("display_name") or prof.get("real_name") or u.get("name") or u["id"]
        users[u["id"]] = name
    save_json(USERS_CACHE, users)
    return users


def fetch_channel(slack, ch_id, oldest, latest, inclusive, include_threads):
    params = {"channel": ch_id, "limit": 200}
    if oldest is not None:
        params["oldest"] = f"{oldest:.6f}"
    if latest is not None:
        params["latest"] = f"{latest:.6f}"
    params["inclusive"] = "true" if inclusive else "false"
    msgs = list(slack.paginate("conversations.history", params, "messages"))
    msgs.sort(key=lambda m: float(m["ts"]))
    if include_threads:
        for m in list(msgs):
            if m.get("reply_count", 0) and m.get("thread_ts") == m.get("ts"):
                replies = list(slack.paginate(
                    "conversations.replies", {"channel": ch_id, "ts": m["ts"], "limit": 200}, "messages"))
                for r in replies:
                    if r.get("ts") != m.get("ts"):
                        r["_reply_to"] = m["ts"]
                        msgs.append(r)
        msgs.sort(key=lambda m: (float(m.get("_reply_to", m["ts"])), float(m["ts"])))
    return msgs


def parent_date(m, tzinfo):
    """답글은 원글 날짜 파일에 둔다. 그래야 기간을 지정해 받을 때 범위 밖 날짜 파일을 덮어쓰지 않는다."""
    return local_date(m.get("_reply_to", m["ts"]), tzinfo)


def complete_days(slack, ch_id, name, msgs, oldest, tzinfo, include_threads):
    """커서 모드는 커서 이후 메시지만 받지만, 날짜 파일은 통째로 다시 쓴다.

    그래서 이미 파일이 있고 커서가 그날 중간에 걸려 있으면, 그날 전체를 다시 받아 앞서 받은
    메시지가 지워지지 않게 한다(2026-09-17 수정 — 전에는 같은 날 앞부분이 사라졌다).
    """
    days = {parent_date(m, tzinfo) for m in msgs}
    redo = sorted(d for d in days
                  if oldest and to_ts(d) < oldest and (OUT_ROOT / name / f"{d}.md").exists())
    if not redo:
        return msgs
    keep = [m for m in msgs if parent_date(m, tzinfo) not in redo]
    for d in redo:
        full = fetch_channel(slack, ch_id, to_ts(d), to_ts(d, end_of_day=True), True, include_threads)
        keep += [m for m in full if parent_date(m, tzinfo) == d]
    keep.sort(key=lambda m: (float(m.get("_reply_to", m["ts"])), float(m["ts"])))
    return keep


def write_channel(name, msgs, users, tzinfo, fetched_at, sensitive):
    """일자별 markdown 파일로 저장. 반환: [(date, path, count)]. 내용이 같으면 파일을 건드리지 않는다."""
    by_day = {}
    for m in msgs:
        if m.get("subtype") in ("channel_join", "channel_leave"):
            continue
        by_day.setdefault(parent_date(m, tzinfo), []).append(m)
    written = []
    for day, day_msgs in sorted(by_day.items()):
        d = OUT_ROOT / name
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{day}.md"
        lines = [f"# slack #{name} — {day}"]
        flag = "  ⚠ SENSITIVE(마스킹 필요)" if sensitive else ""
        lines.append(f"> fetched: {fetched_at} | messages: {len(day_msgs)}{flag}\n")
        for m in day_msgs:
            t = local_time(m["ts"], tzinfo)
            who = author(m, users)
            txt = clean_text(m.get("text", ""), users).rstrip()
            indent = "    ↳ " if m.get("_reply_to") else ""
            head = f"{indent}**{t} {who}**"
            if not txt:
                txt = "_(첨부/빈 메시지)_"
            block = txt.replace("\n", "\n" + ("      " if m.get("_reply_to") else ""))
            lines.append(f"{head}\n{('      ' if m.get('_reply_to') else '')}{block}\n")
        # 원문이라도 계정·비밀번호·키는 파일에 남기지 않는다. 가린 채로 저장한다.
        text = secret_mask.mask("\n".join(lines))
        if path.exists():
            old = path.read_text(encoding="utf-8").split("\n")
            if old[:1] + old[2:] == text.split("\n")[:1] + text.split("\n")[2:]:
                continue      # 받은 시각 줄만 다르다
        path.write_text(text, encoding="utf-8")
        written.append((day, path, len(day_msgs)))
    return written


def mask_existing(dry_run=False):
    """이미 쌓인 raw/slack 원문에서 계정·비밀번호·키를 가린다(제자리 덮어쓰기)."""
    patterns = secret_mask.load_credential_patterns()
    changed = []
    for path in sorted(OUT_ROOT.rglob("*.md")):
        # 줄바꿈을 그대로 둔다(newline=""). 안 그러면 가린 줄 말고 파일 전체가 바뀐 것처럼 보인다.
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        masked = secret_mask.mask(text, patterns)
        if masked == text:
            continue
        changed.append((path, len(secret_mask.find(text, patterns))))
        if not dry_run:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(masked)
    if not changed:
        print("가릴 것이 없다 — raw/slack 원문에 계정·비밀번호·키가 보이지 않는다.")
        return changed
    print(("가릴 대상(고치지 않음)" if dry_run else "가렸다") + f": 파일 {len(changed)}개")
    for path, hits in changed:
        print(f"  {path.relative_to(WIKI_ROOT)} · {hits}줄")
    return changed


def main():
    ap = argparse.ArgumentParser(description="Slack 채널 메시지를 raw/slack/ 로 수집")
    ap.add_argument("--channels", help="쉼표구분 채널명(생략 시 channels.json include 전체)")
    ap.add_argument("--since", help="시작일 YYYY-MM-DD")
    ap.add_argument("--until", help="종료일 YYYY-MM-DD(포함)")
    ap.add_argument("--last-days", type=int, help="최근 N일(오늘 포함)")
    ap.add_argument("--since-cursor", action="store_true", help="채널별 마지막 수집 지점~지금")
    ap.add_argument("--no-threads", action="store_true", help="스레드 답글 제외")
    ap.add_argument("--lookback-days", type=int, default=3,
                    help="커서 수집 때 최근 N일 원글을 다시 훑어 늦게 달린 답글을 잡는다(기본 3, 0 이면 끔)")
    ap.add_argument("--list-channels", action="store_true", help="워크스페이스 채널 목록만 출력")
    ap.add_argument("--mask-existing", action="store_true",
                    help="이미 쌓인 raw/slack 원문에서 계정·비밀번호·키를 가린다(제자리 덮어쓰기)")
    ap.add_argument("--dry-run", action="store_true", help="--mask-existing 과 함께: 고치지 않고 대상만 본다")
    ap.add_argument("--refresh-users", action="store_true", help="유저 캐시 갱신")
    ap.add_argument("--include-nas", action="store_true",
                    help="NAS 공용 아카이브에 있는 채널도 받는다(기본은 건너뜀)")
    args = ap.parse_args()

    # 로컬 파일만 보는 모드 — Slack 토큰이 필요 없다.
    if args.mask_existing:
        mask_existing(dry_run=args.dry_run)
        return

    env = load_env()
    token = env.get("SLACK_TOKEN")
    if not token or token.startswith("xox") is False:
        sys.exit("SLACK_TOKEN 이 없다. 위키 루트 .env (권장) 또는 tools/slack-ingest/.env 에 작성. 템플릿: tools/slack-ingest/.env.example")
    tzname = env.get("SLACK_TZ", "").strip()
    try:
        from zoneinfo import ZoneInfo
        tzinfo = ZoneInfo(tzname) if tzname else datetime.now().astimezone().tzinfo
    except Exception:
        tzinfo = datetime.now().astimezone().tzinfo

    slack = Slack(token)
    config = load_json(CHANNELS_FILE, {"include": [], "exclude": [], "sensitive": []})

    if args.list_channels:
        for ch in slack.paginate(
            "conversations.list",
            {"types": "public_channel,private_channel", "limit": 1000, "exclude_archived": "false"},
            "channels"):
            priv = "🔒" if ch.get("is_private") else "  "
            print(f"{priv} {ch['name']}")
        return

    # 기간 모드 결정
    cursors = load_json(CURSOR_FILE, {})
    mode_cursor = args.since_cursor or (not args.since and not args.last_days)
    oldest = latest = None
    if args.last_days:
        start = (datetime.now(tzinfo) - timedelta(days=args.last_days - 1)).strftime("%Y-%m-%d")
        oldest, latest = to_ts(start), to_ts(datetime.now(tzinfo).strftime("%Y-%m-%d"), end_of_day=True)
        period = f"{start}..{datetime.now(tzinfo).strftime('%Y-%m-%d')}"
    elif args.since:
        until = args.until or args.since
        oldest, latest = to_ts(args.since), to_ts(until, end_of_day=True)
        period = f"{args.since}..{until}"
    else:
        period = "since-cursor"   # oldest 는 채널별로 다름

    # 채널 선택
    exclude = set(config.get("exclude", []))
    if args.channels:
        wanted = [c.strip() for c in args.channels.split(",") if c.strip() and c.strip() not in exclude]
    else:
        wanted = [c for c in config.get("include", []) if c not in exclude]

    # 공개 채널은 NAS 공용 아카이브가 받는다. 같은 채널을 개인 토큰으로 또 받지 않는다.
    on_nas = []
    if not args.include_nas:
        nas_names, nas_ids, nas_live = nas_slack.covered_channels(config)
        id_cache = config.get("_id_cache", {})
        on_nas = [c for c in wanted if c in nas_names or id_cache.get(c) in nas_ids]
        wanted = [c for c in wanted if c not in on_nas]
    targets = resolve_channels(slack, wanted, config.get("_id_cache", {}))
    if not args.include_nas:
        late = [n for n, cid in targets if cid in nas_ids]      # 이름이 바뀐 채널
        on_nas += late
        targets = [(n, cid) for n, cid in targets if cid not in nas_ids]
    if on_nas:
        basis = "" if nas_live else " (NAS 에 닿지 않아 마지막으로 본 목록 기준)"
        print(f"NAS 공용 아카이브에 있는 채널 {len(on_nas)}개는 받지 않는다{basis}: "
              + ", ".join(on_nas) + "  → nas_slack.py 로 읽는다")

    if not targets:
        if on_nas:
            print("\n총 0건 수집. 개인 토큰으로 받을 채널이 없다.")
            return
        sys.exit("수집할 채널이 없다. channels.json include 또는 --channels 확인.")

    users = load_users(slack, refresh=args.refresh_users)
    sensitive_set = set(config.get("sensitive", []))
    fetched_at = datetime.now(tzinfo).strftime("%Y-%m-%d %H:%M")

    print(f"\n=== Slack 수집: {period} | 채널 {len(targets)}개 ===\n")
    manifest, total = [], 0
    for name, ch_id in targets:
        if mode_cursor:
            ch_oldest = cursors.get(name)
            ch_oldest = float(ch_oldest) if ch_oldest else None
            if ch_oldest is None:
                sys.stderr.write(f"  · #{name}: 커서 없음 → 최근 7일로 대체\n")
                ch_oldest = (datetime.now(tzinfo) - timedelta(days=7)).timestamp()
            ch_latest, inclusive = None, False
        else:
            ch_oldest, ch_latest, inclusive = oldest, latest, True
        fetch_from, fetch_inclusive = ch_oldest, inclusive
        if mode_cursor and args.lookback_days > 0 and not args.no_threads:
            # 옛 원글에 늦게 달린 답글은 커서 이후 원글만 봐서는 안 들어온다.
            # 최근 N일 원글과 그 답글을 다시 받고, 커서 이후 것이 있는 날만 다시 쓴다.
            day = (datetime.now(tzinfo) - timedelta(days=args.lookback_days - 1)).strftime("%Y-%m-%d")
            if to_ts(day) < ch_oldest:
                fetch_from, fetch_inclusive = to_ts(day), True
        try:
            msgs = fetch_channel(slack, ch_id, fetch_from, ch_latest, fetch_inclusive,
                                 include_threads=not args.no_threads)
            real = [m for m in msgs if m.get("subtype") not in ("channel_join", "channel_leave")]
            if mode_cursor:
                real = [m for m in real if float(m["ts"]) > ch_oldest]
                touched = {parent_date(m, tzinfo) for m in real}
                msgs = [m for m in msgs if parent_date(m, tzinfo) in touched]
                if real:
                    msgs = complete_days(slack, ch_id, name, msgs, fetch_from, tzinfo,
                                         include_threads=not args.no_threads)
        except RuntimeError as e:
            sys.stderr.write(f"  ⚠ #{name}: {e} (봇 미초대일 수 있음, 건너뜀)\n")
            continue
        written = write_channel(name, msgs, users, tzinfo, fetched_at, name in sensitive_set)
        if real:
            top = max(float(m["ts"]) for m in real)
            old = float(cursors.get(name) or 0)
            if mode_cursor:
                cursors[name] = max(old, top)
            elif old and ch_oldest <= old:
                # 기간 수집은 커서와 이어질 때만, 그 기간 끝까지만 커서를 옮긴다. 범위 밖 답글 시각까지
                # 옮기면 그 사이 원글을 다음 커서 수집이 건너뛴다. 커서는 뒤로 가지 않는다.
                cursors[name] = max(old, min(top, ch_latest))
        total += len(real)
        tag = " ⚠SENS" if name in sensitive_set else ""
        print(f"  #{name}{tag}: {len(real)}건" + (f" ({len(written)}일)" if written else " (없음)"))
        for day, path, cnt in written:
            manifest.append(str(path.relative_to(WIKI_ROOT)).replace("\\", "/"))

    save_json(CURSOR_FILE, cursors)
    print(f"\n총 {total}건 수집. 저장 경로(읽을 파일):")
    for p in manifest:
        print(f"  {p}")
    if not manifest:
        print("  (새 메시지 없음)")
    print("\n→ 위 파일들을 읽어 /slack-ingest 지식화·태스크 추출을 진행하세요.")


if __name__ == "__main__":
    main()
