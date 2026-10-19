# SETUP — 환경 설정 가이드

> [README.md](README.md) 의 5분 시작으로 부족할 때, 도구별 상세 설정. 필요한 것만 골라 한다.
> **처음부터 혼자 설정한다면 [START-HERE.md](START-HERE.md) 가 먼저다.**
> **이미 쓰던 개인 위키를 회사 GitHub(전사 위키·할 일 보드)과 연결한다면 [GITHUB-CONNECT.md](GITHUB-CONNECT.md) 를 따른다.**

## 0. 개인 위키 만들기

1. 템플릿 repo 에서 **Use this template** → **본인 계정 · private** 으로 새 저장소 생성 → 로컬 clone.
   - ⚠️ **Fork 로 만들지 않는다.** 포크는 조직 권한을 물려받는다. 이미 포크했다면 [MIGRATE-FROM-FORK.md](MIGRATE-FROM-FORK.md).
2. `me.md` 의 `<...>` 를 본인 값으로. **L1·가치는 본인만 채울 수 있다.**
3. 첫 커밋.

> `.env`·토큰·`channels.json` 은 `.gitignore` 로 빠진다. **`raw/` 는 md 만 커밋된다** — PDF·이미지·jsonl 원본은 자동으로 제외된다(CLAUDE.md §4.3).

## 1. Claude Code (필수)

- Claude Code 를 위키 폴더에서 실행하면 같은 폴더의 `CLAUDE.md` 가 자동 로드되고, 첫 줄 `@me.md` 가 '나'를 로드한다.
- `.claude/commands/*.md` 가 slash command 로 인식된다. 대화창에서 `/brain`, `/eod` 처럼 호출.
- 가장 먼저 해볼 것: `/brain <요즘 생각 한 줄>` → 대화로 첫 2nd brain note 작성.

### 터미널이 어려우면 — 웹에서 쓰기

CLI 를 안 쓰는 사람도 **claude.ai 에 본인 계정으로 로그인해 Claude Code(웹)** 로 같은 위키를 쓸 수 있다. 본인 계정의 private repo 를 연결하면 브라우저 채팅창에서 `/eod` 같은 커맨드가 그대로 동작한다. 이때 위키가 **git 에 다 올라가 있어야** 웹에서 보이므로, raw 를 md 로 커밋하는 정책(§4.3)이 전제다.

> Claude Desktop 으로 **읽기**만 하려면 Filesystem MCP(또는 폴더 연결)로 이 폴더를 붙여 "위키에서 ~ 찾아줘" 로 질의할 수 있다.

## 2. 전사 LLM wiki 연동 — Jarvis MCP 커넥터

CLAUDE.md §17 참조. 사내 표준 커넥터는 **Jarvis**다. 연결하면 툴이 여러 개 생기지만 쓰는 것은 `jarvis_ask` 하나다.

> ⚠️ **일일 리포트 저장·팀 조회와 할 일은 자비스가 아니라 GitHub 으로 한다.** 아래 2-1 을 먼저 한다. 자비스는 사내 질의(`jarvis_ask`)와 축산 데이터 조회에 쓴다.
- `jarvis_ask` — 사내 위키·정책·개념·축산 운영 DB 를 자연어로 질의 (읽기, 내 권한으로 스코프·PII 자동 마스킹)
- `jarvis_eod_save` · `jarvis_team_eod` · `jarvis_task_create` — 쓰지 않는다. 일일 리포트와 할 일은 `tools/company-wiki.py` 로 한다(2-1)

**전제**: @bodit.co Google 계정 + 대시보드 `users` 에 등록된 활성 사용자.

### 2-1. 전사 위키 연결 — 일일 리포트 올리기·팀 리포트 읽기·할 일

`/eod`·`/morning` 이 `tools/company-wiki.py` 로 전사 위키를 **내려받지 않고** 읽고 쓴다. 할 일도 같은 도구로 GitHub issue 와 조직 보드 **Bodit Tasks**(https://github.com/orgs/bodit-inc/projects/7)에서 다룬다. 준비는 세 가지다.

1. **GitHub CLI 로그인** — `gh auth login` (한 번). Claude 에게 "GitHub 로그인 도와줘" 라고 해도 된다.
2. **할 일 보드 권한** — `gh auth refresh -h github.com -s project` (한 번). 토큰에 `project` 권한이 있어야 할 일을 보드에 넣고 읽을 수 있다.
3. **전사 위키 내 프로필에 GitHub 계정** — `bodit-inc/bodit-llm-wiki` 의 `people/<내이름>.md` frontmatter 에 `github: <내 계정>` 한 줄. 없으면 Claude 에게 "전사 위키 내 프로필에 github 계정 추가해줘" 라고 한다.

**2번에서 막힐 때**: Claude Code 안에서 실행하면 브라우저 승인 결과를 받아 오다가 `context deadline exceeded` 로 끝나는 경우가 있다. 그때는 둘 중 하나로 한다.

- Claude Code 밖의 터미널(Windows Terminal, macOS 터미널)에서 같은 명령을 실행한다.
- Claude 에게 "백그라운드로 실행해서 일회용 코드를 알려줘" 라고 한다. 코드를 받으면 브라우저에서 넣고 승인한다. 코드는 약 15분 동안 유효하다.

확인: `python tools/company-wiki.py whoami` 가 내 이름·파트를 보여주고, `python tools/company-wiki.py task-list --mine` 이 오류 없이 목록(비어 있어도 된다)을 보여주면 끝이다. 올리는 규칙·리뷰어 지정은 전사 `docs/guide/contributing.md`.

**A. Claude Code (CLI)**
```bash
claude mcp add --transport http jarvis https://jarvis-mcp.bodit-lab.co/mcp -s user
```
그 다음 `/mcp` 입력 → 인증 트리거 → 브라우저에서 **Google 로그인(@bodit.co)**. (`-s user` 는 모든 프로젝트에서 쓰겠다는 뜻 — 개인 위키 하나만 쓸 거면 생략)

**B. Claude Desktop / Web (claude.ai)**
Settings → Connectors → **Add custom connector** → URL `https://jarvis-mcp.bodit-lab.co/mcp` → 연결 → Google 로그인 → Authorize. 채팅에서 커넥터를 켜면 툴이 보인다.

**연결 안 해도 된다**: 커맨드가 전사 단계를 건너뛰고 한 줄 고지한다. 개인 위키 기능은 전부 정상 동작한다.

> **지식 페이지(decision·concept·entity)는 전사 위키에 PR 로 올리고 리뷰어를 지정한다**(전사 `docs/guide/contributing.md`). `/promote` 가 `tools/company-wiki.py wiki-pr` 로 올린다. 내 회의록·논문 원문은 `mine-put` 으로 main 에 바로 올린다. 둘 다 `--yes` 없이는 미리보기만 나온다.
> 어느 경로든 **개인 회고·`brain/` 은 절대 넘어가지 않는다**(§17.1). 일일 리포트도 원본은 개인 위키에 남고, **민감분을 걷어낸 공유본**만 전사로 간다.

### 문제 해결 (Jarvis)

| 증상 | 조치 |
|---|---|
| "등록 실패 / OAuth 클라이언트 ID 추가" | 관리자에게 — Allowed redirect URIs 에 클라 콜백 추가 요청 |
| "Invalid nonce" | Access 로그아웃 후 커넥터 재추가 |
| Claude Web 에서 자꾸 실패 | **Claude Code** 로 시도(더 안정적) |
| 툴이 안 보임 | 커넥터 **재연결**(툴 목록 캐시 갱신) |
| "미등록 사용자" 취급 | 대시보드 `users` 등록 필요 → 관리자 |

## 2.5 템플릿 새 판 받기 (`/template-update`)

템플릿이 바뀌면 `/template-update` 로 받는다. 처음 한 번은 [UPDATE.md](UPDATE.md) 의 "처음 한 번"(동기화 도구 내려받기)을 따라 한다. 내 기록(`me.md`·`brain/`·`raw/`·`wiki/`·`index.md`·`log.md`)은 건드리지 않는다.

## 3. Slack 연동 (`/slack-ingest`)

> **처음 연결은 [SLACK-GUIDE.md](SLACK-GUIDE.md) 를 따라간다.** 비개발자용으로 쓴 단계별 안내다. Claude 에게 "SLACK-GUIDE.md 를 보고 슬랙 연결을 같이 해줘" 라고 하면 순서대로 안내한다.
> 2026-09-17 부터 **공개 채널은 전사 공용 보관함(NAS)** 에서 읽는다. 토큰은 비공개 채널이 필요한 사람만 연결한다.

동작 원리는 [tools/slack-ingest/README.md](tools/slack-ingest/README.md). 요약:

**공개 채널 (모두)**
1. 탐색기 `\\192.168.0.225\wiki-share` (macOS Finder `⌘K` → `smb://192.168.0.225/wiki-share`) 를 열어 NAS 계정으로 로그인한다. 사내망 전용이라 재택은 VPN 이 먼저다.
2. `python tools/slack-ingest/nas_slack.py --check` 로 연결 확인. 경로가 다르면 위키 루트 `.env` 에 `SLACK_NAS_ROOT=<경로>`.
3. 이후 `/slack-ingest` 가 커서 이후 대화를 읽고(`--pending`), 끝나면 커서를 옮긴다(`--mark`).

**비공개 채널 (선택)**
1. https://api.slack.com/apps 에서 앱 생성 → User Token Scopes(`groups:history` 등 private 범위 포함) → Install → 토큰(`xoxp-…`) 복사.
2. `cp tools/slack-ingest/.env.example .env` → 위키 루트 `.env` 에 `SLACK_TOKEN` 채우기.
3. `cp tools/slack-ingest/channels.json.example tools/slack-ingest/channels.json` → `include` 에 본인이 속한 비공개 채널을 적는다. NAS 에 있는 공개 채널은 적어도 건너뛴다. 인사·급여·면담 채널은 `exclude`.
4. `python tools/slack-ingest/fetch_slack.py --list-channels` 로 연결 확인.
5. 이후 `/slack-ingest` 가 채널을 고르게 한 뒤 수집·지식화를 대신 호출한다.

> Python 3.9+ 필요(표준 라이브러리만 씀, pip 설치 불필요).
> 비공개 채널 원문 `raw/slack/*.md` 는 **커밋된다**. 민감 내용이 섞이지 않도록 채널 선정과 마스킹에 주의한다. NAS 본문은 로컬에 복사하지 않는다.
> ⚠️ 개인 위키 저장소가 **포크(fork)면 조직 구성원이 원문을 볼 수 있다** — 연결 전에 [SLACK-GUIDE.md](SLACK-GUIDE.md) §1-1 로 확인한다.

## 4. 코드 레포 연동 (`/repo-ingest`) — 개발자용

- 위키와 코드 레포가 **워크스페이스 루트에 형제로** 있을 때 가장 자연스럽다.
- 레이아웃이 다르면 `.claude/commands/repo-ingest.md` 의 경로를 본인 구조에 맞게 조정.
- 대상 레포는 **read-only** — git log/diff 를 읽기만 하고 코드 레포를 수정하지 않는다.

## 5. 세션 회고 (`/session-retro`) — 개발자용

- `powershell -File tools/sync-sessions.ps1` 로 `~/.claude/projects/*.jsonl` 을 `raw/sessions/` 에 미러한다.
- `.jsonl` 은 md 가 아니라 **커밋되지 않는다** — 로컬 작업용이고, 회고 결과물(md)만 위키에 남는다.
- 주 1회 정도가 적당하다.

## 6. (선택) 회의록·산출물 PDF — `/meeting-ingest`

`/meeting-ingest` 는 **md 만으로도 완결된다.** 남에게 건넬 PDF 가 필요할 때만 아래를 갖춘다.

- **pandoc** 과 **Chrome**(또는 Chromium)이 있으면 `tools/md-to-pdf.sh` 가 동작한다. LaTeX 은 필요 없다.
- 스크립트가 흔한 설치 경로를 먼저 훑고, 못 찾으면 환경변수로 받는다:

```bash
PANDOC=/path/to/pandoc CHROME=/path/to/chrome bash tools/md-to-pdf.sh 입력.md wiki/assets/reports/출력.pdf "문서 제목"
```

- 출력은 `wiki/assets/reports/` 에 둔다(CLAUDE.md §11.1). 정리본은 `-minutes`, 원문은 `-transcript` 접미사로 짝을 맞춘다.
- 둘 중 하나가 없으면 스크립트가 한 줄로 알리고 멈춘다. **md 는 이미 저장돼 있으므로 회의록 자체는 유실되지 않는다.**

## 7. (선택) 워크스페이스 메모리로 코드 작업에 위키 붙이기

위키를 코드 레포들과 형제로 두고, 워크스페이스 루트에 `CLAUDE.local.md` 를 만들어 위키 경로·`@<wiki>/me.md` 를 안내하면, 어느 코드 repo 에서 작업해도 위키 컨텍스트가 자동으로 붙는다. (CLAUDE.md §13 참조)

---

## 트러블슈팅

- **slash command 가 안 보임**: Claude Code 를 위키 폴더(루트)에서 실행했는지 확인. `.claude/commands/` 가 그 폴더 안에 있어야 한다.
- **`NAS 에 닿지 않는다`**: 사내망(재택은 VPN)인지, 탐색기·Finder 로 `wiki-share` 에 한 번 로그인했는지 확인. 경로가 다르면 `.env` 의 `SLACK_NAS_ROOT`.
- **`SLACK_TOKEN 이 없다`**: `.env` 위치(위키 루트 우선) 와 토큰 값 확인. private 채널은 `groups:history` 스코프가 필요하다. 공개 채널만 쓴다면 무시해도 된다.
- **raw 의 PDF 가 커밋에 안 잡힘**: 정상이다(§4.3 md-only). 읽어서 md 로 발췌해 저장한다 — `/pdf-ingest` 가 대신 해준다.
- **전사 단계가 건너뛰어짐**: `claude mcp list` 로 jarvis 가 `Needs authentication` 인지 확인 → `/mcp` 로 로그인. 그래도 안 되면 위 문제 해결 표.
- **웹(claude.ai)에서 최근 내용이 안 보임**: 로컬에서 push 했는지 확인. 웹은 git 에 올라간 것만 본다.
- **`gh auth refresh` 가 `context deadline exceeded` 로 끝남**: Claude Code 안에서 실행해 브라우저 승인 결과를 받아 오지 못한 것이다. 2-1 의 "2번에서 막힐 때" 를 따른다.
- **`task-list`·`task-new` 가 권한 오류로 멈춤**: 토큰에 `project` 권한이 없다. `gh auth refresh -h github.com -s project` 를 실행한다.
- **PowerShell 스크립트에서 한글이 깨지거나 파서가 죽음**: Windows PowerShell 5.1 은 UTF-8 을 기본으로 안 쓴다. 세 지점을 확인한다 — ① `.ps1` 은 **UTF-8 with BOM** 으로 저장(BOM 없으면 ANSI 로 읽어 파서가 죽는다) ② 외부 exe 로 파이프하면 `$OutputEncoding`(기본 ASCII) 때문에 한글이 `?` 로 유실 → 스크립트 앞에서 UTF-8 로 고정 ③ `Set-Content -Encoding utf8` 은 **BOM 을 붙인다** — 기계가 파싱할 파일이면 `[System.IO.File]::WriteAllText` 로 BOM 없이 쓰고, 읽는 쪽은 `utf-8-sig` 로 읽는다. **`tools/*.ps1` 을 편집할 때 BOM 을 날리지 않도록 주의한다.**
