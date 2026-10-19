# slack-ingest — Slack 대화를 읽는 도구

`/slack-ingest` slash command 가 쓰는 도구 둘이다(2026-09-17 개정).

| 도구 | 읽는 채널 | 어디서 | 필요한 것 |
|---|---|---|---|
| `nas_slack.py` | **공개 채널** (NAS 에 있는 것) | 전사 공용 아카이브 NAS `\\192.168.0.225\wiki-share`. 분석파트 워크스테이션이 매시 받아 개인정보를 가린 사본이다. 읽기만 한다 | 사내망(재택은 VPN) + NAS 계정 |
| `fetch_slack.py` | **비공개 채널** + NAS 에 없는 공개 채널 (선택) | 개인 Slack 토큰으로 `raw/slack/<channel>/YYYY-MM-DD.md` 에 받는다. md 는 git 에 커밋된다(CLAUDE.md §4.3) | Slack 토큰 + `channels.json` |

**대부분은 `nas_slack.py` 만으로 충분하다.** 비공개 채널까지 챙겨야 하는 사람만 토큰을 연결한다.
`fetch_slack.py` 는 NAS 에 있는 채널을 **받지 않는다**(채널 ID 로 판정). 같은 공개 채널을 가리기 전 원문으로 따로 읽으면
NAS 마스킹이라는 관문이 무의미해지기 때문이다. 위키·brain 에는 합성·마스킹된 지식만 올린다.

> 필요: Python 3.9+ (표준 라이브러리만 사용, 추가 설치 불필요).

## 0. NAS 공용 아카이브 — `nas_slack.py` (토큰 필요 없음)

### 0.1 연결 (한 번만)

- **Windows**: 탐색기 주소창에 `\\192.168.0.225\wiki-share` → NAS 계정(FarmersHands 열 때 쓰던 계정)으로 로그인 → **자격 증명 저장** 체크.
- **macOS**: Finder 에서 `⌘K` → `smb://192.168.0.225/wiki-share` → 로그인. `/Volumes/wiki-share` 에 붙는다.
- 사내망에서만 열린다. 재택이면 VPN 을 먼저 연결한다. 익명 접근은 막혀 있어 로그인 전에는 공유 목록에도 안 보인다.
- 경로가 기본값(Windows `//192.168.0.225/wiki-share`, macOS `/Volumes/wiki-share`, Linux `/mnt/wiki-share`)과 다르면
  위키 루트 `.env` 에 `SLACK_NAS_ROOT=<경로>` 를 적는다.

### 0.2 사용

```bash
python tools/slack-ingest/nas_slack.py --check                 # 연결·채널·마지막 갱신 시각
python tools/slack-ingest/nas_slack.py --pending --stats       # 지식화 대기 분량 (2만 토큰 넘으면 채널을 좁힌다)
python tools/slack-ingest/nas_slack.py --pending --channels issue,개발자
python tools/slack-ingest/nas_slack.py --mark                  # 방금 --pending 으로 본 데까지 커서 전진
python tools/slack-ingest/nas_slack.py --since 2026-09-10 --until 2026-09-12
python tools/slack-ingest/nas_slack.py --last-days 3
python tools/slack-ingest/nas_slack.py --mark --at "2026-09-17 09:00"   # 커서를 특정 시각으로 맞춘다
```

- 출력은 채널 → 날짜 → 메시지 순이고, 메시지마다 슬랙 원문 링크 `[↗](…/archives/<채널ID>/p…)` 가 붙는다.
  첨부 파일은 이름·형식·크기만 남기고 주소는 뺀다.
- **커서**(`.nas-cursor.json`, 커밋 안 됨): `ingest` 는 `/slack-ingest` 가 쓴다(`digest` 는 무인 다이제스트용).
  채널 ID 기준이라 슬랙에서 채널 이름이 바뀌어도 이어진다. 커서가 없으면 최근 7일을 본다.
- `--mark` 는 **마지막 `--pending` 이 본 데까지만** 옮긴다. 그 사이 새로 들어온 메시지를 건너뛰지 않기 위해서다.
- 답글은 원글 날짜 파일에 들어 있다. 워크스테이션이 지난 3일치를 다시 쓰므로, 도구는 커서보다 4일 앞 파일부터 훑는다.
- 종료 코드 3 = NAS 에 닿지 않음(사내망·VPN·로그인 확인).
- **NAS 사본의 원칙**(전사 위키 `wiki/playbooks/slack-archive.md`): 사람이 검토하지 않은 기계 가공본이다.
  출처 링크 없는 문장을 쓰지 않고, 숫자·결론은 원문을 확인한 뒤 확정하며, `{SECRET}`·`{TEL_…}` 같은 토큰은 복원하지 않는다.
  사본을 외부로 내보내지 않는다.
- 분석파트가 배포하는 `/slack-compile`(NAS `_skills/`)과 역할이 같다. 이 템플릿을 쓰면 `/slack-ingest` 가 그 일을 하므로 따로 설치하지 않는다.

## 1. 개인 토큰 수집 — `fetch_slack.py` (비공개 채널이 필요할 때만)

### 1.1 Slack 앱 만들고 토큰 발급

1. https://api.slack.com/apps → **Create New App** → From scratch → 워크스페이스 선택.
2. **OAuth & Permissions** → Scopes 추가:
   - 비공개 채널까지 *본인이 보는 그대로* 받으려면 **User Token Scopes** (권장):
     `channels:history`, `groups:history`, `channels:read`, `groups:read`, `users:read`
     DM 권한(`im:history`·`mpim:history`)은 넣지 않는다 — 토큰이 새면 DM 까지 열린다.
   - 봇을 각 채널에 초대해 운영할 거면 **Bot Token Scopes** 에 같은 권한.
3. **Install to Workspace** → 발급된 토큰 복사 (User: `xoxp-…`, Bot: `xoxb-…`).
   > 🚨 **앱의 Distribution(공개 배포)을 켜지 않는다.** Marketplace 승인 없이 외부 배포된 앱은
   > `conversations.history`·`replies` 가 **1분당 1요청·건당 15개**로 묶인다(2025-05-29 발표, 기존 설치분도 2026-03-03 부터).
   > 워크스페이스에 설치만 한 사내 앱은 예외라 지금은 영향이 없지만, 켜는 순간 여러 채널 수집이 사실상 멈춘다.
4. Bot 토큰을 쓰면 수집할 각 채널에서 `/invite @앱이름` 으로 봇을 초대해야 한다.
   User 토큰은 본인이 이미 멤버인 채널이면 초대 불필요.

### 1.2 .env 작성

시크릿은 **위키 루트 `.env` (권장, 모든 위키 도구 공용)** 또는 도구 로컬 `tools/slack-ingest/.env` 에 둔다.
스크립트는 루트 → 로컬 순으로 읽어 로컬이 있으면 override 한다.

```bash
cp tools/slack-ingest/.env.example .env   # 위키 루트에 두는 경우 (권장). SLACK_TOKEN 채우기
```

루트 `.env`, 로컬 `tools/slack-ingest/.env`, `.cursor.json`, `.nas-cursor.json`, `.users_cache.json`, `channels.json` 모두 `.gitignore` 처리됨(커밋 안 됨).

## 2. 채널 설정 — `channels.json`

```bash
cp tools/slack-ingest/channels.json.example tools/slack-ingest/channels.json
```

- `include`: 개인 토큰으로 받을 채널명(슬랙 표시명 그대로). **본인이 속한 비공개 채널**과 NAS 에 없는 공개 채널만 적는다.
  NAS 에 있는 채널을 적어도 받지 않는다(남겨 두면 나중에 NAS 에서 빠질 때 다시 받는다).
- `exclude`: 제외(예: 인사·채용 채널).
- `sensitive`: 수집은 하되 지식화 시 **강한 마스킹** 표시(예: contract). 출력 파일에 `⚠SENSITIVE` 마커가 붙는다.
- `_id_cache`: 스크립트가 이름→채널ID 를 자동 해석해 캐시. 직접 건드릴 필요 없음.
  슬랙에서 채널 이름이 바뀌면 `include` 와 여기 키를 새 이름으로 바꾼다(ID 는 그대로다).
- `_nas_channels`: NAS 에 있는 채널 이름→ID. 수집기가 NAS 에 닿을 때마다 자동으로 갱신하고, 닿지 않을 때는 마지막 목록으로 판정한다.
- `nas_root`(선택): NAS 경로. `.env` 의 `SLACK_NAS_ROOT` 가 우선한다.

채널명이 헷갈리면: `python fetch_slack.py --list-channels` 로 워크스페이스 채널 목록 확인(🔒 = 비공개).

## 3. 사용 (보통은 `/slack-ingest` 가 대신 호출)

```bash
python fetch_slack.py --since 2026-06-12 --until 2026-06-17   # 기간
python fetch_slack.py --since 2026-06-16 --until 2026-06-16   # 특정 하루
python fetch_slack.py --last-days 7                           # 최근 7일
python fetch_slack.py --since-cursor                          # 지난번 수집 이후~지금 (기본)
python fetch_slack.py --channels my-private-channel --since 2026-06-12 --until 2026-06-17
python fetch_slack.py --list-channels                         # 채널 목록만
```

- 인자 없이 실행하면 `--since-cursor`. 채널별 마지막 수집 지점(`.cursor.json`)부터 지금까지. 커서가 없는 채널은 최근 7일로 대체.
- **날짜 파일은 통째로 다시 쓴다.** 그래서 커서가 하루 중간에 걸려 있고 그날 파일이 이미 있으면 그날 전체를 다시 받아,
  앞서 받은 메시지가 지워지지 않게 한다. 답글은 원글 날짜 파일에 들어간다.
- 기간을 지정해 받으면 커서는 그 기간이 커서와 이어질 때만, 기간 끝까지만 옮긴다. 과거를 다시 받아도 커서가 뒤로 가거나 건너뛰지 않는다.
- 스레드 답글은 기본 포함(`--no-threads` 로 제외).
- 커서 수집은 **최근 3일 원글과 그 답글을 다시 훑어**, 옛 원글에 늦게 달린 답글도 잡는다(`--lookback-days N`, 0 이면 끔). 커서 이후 메시지가 있는 날만 다시 쓴다.
- NAS 채널을 일부러 받아야 할 때만 `--include-nas` 를 붙인다.
- 끝에 **읽을 파일 목록(manifest)** 을 출력 → 그 파일들을 읽어 지식화한다.

## 4. 주의

- `raw/slack/` 원문은 **immutable**(수집기만 다시 쓴다)이며 md 로 git 에 커밋된다(CLAUDE.md §4.3). 민감 내용이 남지 않도록 채널 선정·마스킹에 주의하고, 위키/brain 으로는 합성·마스킹해서만 승격.
- ⚠️ 개인 위키 저장소가 **포크면 조직 구성원이 원문을 볼 수 있다.** 비공개 채널을 받기 전에 [SLACK-GUIDE.md](../../SLACK-GUIDE.md) §1-1 로 확인한다.
- `sensitive` 채널·민감 정보(개인정보·급여·계약액·고객 식별)는 지식화 시 마스킹.
- Slack 링크는 **공개 채널 메시지 링크만** 출처로 남긴다. 비공개 채널 링크·첨부 파일 링크는 걷어낸다.
- Bot 미초대 채널은 `not_in_channel` 로 건너뛴다(경고만). User 토큰이면 대부분 회피됨.
- rate limit(429)·`ratelimited` 는 자동 대기·재시도.

## 5. 계정·비밀번호는 원문에도 남기지 않는다

Slack 에 누군가 계정 정보를 올리면 그대로 `raw/slack/` 에 쌓이고 커밋까지 된다. 그래서 **두 겹으로 막는다**.

1. **수집 단계에서 값을 지운다.** `fetch_slack.py` 가 파일을 쓰기 직전에 `tools/secret_mask.py` 로
   계정·비밀번호·키를 `[자격증명 가림]` 으로 바꾼다. 이름표(`PW:`)는 남아 무엇이 가려졌는지는 보인다.
2. **커밋 전에 한 번 더 막는다.** `tools/hooks/pre-commit` 이 커밋하려는 내용에 같은 규칙이 걸리면
   커밋을 거부한다. 등록은 `powershell -File tools/install-secret-hook.ps1`(상태 `-Status`·해제 `-Remove`).

```bash
python tools/slack-ingest/fetch_slack.py --mask-existing --dry-run   # 이미 쌓인 원문에서 대상만 본다
python tools/slack-ingest/fetch_slack.py --mask-existing             # 실제로 가린다
```

- 규칙은 코드가 아니라 **`tools/sensitive-check.txt` 의 `[credentials]` 절** 한 곳에 있다. 줄만 더하면 된다.
- 같은 규칙을 `tools/company-wiki.py` 의 전사 업로드 직전 검사도 함께 쓴다.
- **git 이력에 이미 들어간 값은 지워지지 않는다.** 노출된 비밀번호는 반드시 바꾼다.
