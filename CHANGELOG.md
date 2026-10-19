# 템플릿 변경 기록

> 판마다 **무엇이 바뀌었나**와 **사람이 할 일**을 적는다.
> `/template-update` 가 내 위키에 반영할 때 이 목록을 보여 주고, `/morning` 은 새 판이 나오면 한 줄로 알린다.
> 반영 방법은 [UPDATE.md](UPDATE.md).
>
> 형식은 `## vN · YYYY-MM-DD · 제목` 아래 `### 바뀐 것` 과 `### 사람이 할 일`(없으면 "없음") 이다.
> 템플릿을 고치는 사람은 **판을 하나 올리고 여기에 먼저 적는다**(UPDATE.md §템플릿을 고치는 사람).

## v6 · 2026-10-06 · 전사 위키에 올리는 파일은 늘 LF

### 바뀐 것
- `tools/company-wiki.py` — 전사 위키에 올리는 모든 파일(일일 리포트·활동 기록·회의록·PR)을 올리기 직전에 줄바꿈을 LF 로 맞춘다. 전사 위키 raw 는 한 번 올리면 덮어쓸 수 없어서, 내 위키 파일이 어떤 줄바꿈이든 업로드 지점 한 곳에서 정리한다.
- 배경: Windows 에서 Python 으로 파일을 고치면 기본 설정이 LF 를 CRLF 로 바꾼다. 몇 줄만 고쳤는데 git diff 가 파일 전체 변경으로 나오면 이 함정이다. 기존 파일을 스크립트로 고칠 때는 바이트로 읽고 쓰거나(`open(p, 'rb')`·`open(p, 'wb')`) 텍스트 모드라면 읽기·쓰기 모두 `newline=''` 을 준다.

### 사람이 할 일
- 없음. `/template-update` 로 받으면 된다.

## v5 · 2026-09-18 · 템플릿 새 판을 명령 하나로 받는다

### 바뀐 것
- `tools/template-sync.py` — 템플릿 새 판을 **파일마다 비교해** 반영한다. 내가 안 고친 파일은 새 판으로 바꾸고, 내가 고친 파일(`CLAUDE.md` 포함)은 3방향으로 합치며, 합치지 못한 것만 Claude 가 이어서 합친다. 내가 지운 파일은 다시 받지 않는다.
- `me.md`·`brain/`·`raw/`·`wiki/`·`index.md`·`log.md`·`channels.json`·`.env` 는 **건드리지 않는다**. 규칙은 `tools/template-sync-rules.txt` 에 있고, 내가 고친 커맨드를 갱신에서 빼고 싶으면 그 줄을 `keep` 으로 올리면 된다.
- `/template-update` 커맨드와 이 변경 기록, 받는 방법 안내 [UPDATE.md](UPDATE.md).
- `/morning` 이 하루에 한 번 새 판이 있는지 보고 한 줄로 알린다.
- `GITHUB-CONNECT.md` 2절이 "받을 파일을 손으로 고르는" 방식에서 `/template-update` 로 바뀌었다. 파일 목록이 낡아 새 도구가 빠지는 문제를 없앤다.

### 사람이 할 일
- 처음 한 번만: 개인 위키 폴더의 Claude Code 에 `gh 로 bodit-inc/llm-wiki-template 의 UPDATE.md 를 읽고 "처음 한 번" 을 따라 해줘` 라고 말한다.
- 그다음부터: `/morning` 이 알려 주면 `/template-update` 한 줄이면 된다.

## v4 · 2026-09-17 · 슬랙 공개 채널은 전사 공용 보관함(NAS)에서 읽는다

### 바뀐 것
- 공개 채널은 분석파트 워크스테이션이 **매시 정각에 받아 개인정보를 가린 사본**을 NAS `\\192.168.0.225\wiki-share` 에 쌓는다. 새 도구 `tools/slack-ingest/nas_slack.py` 가 그것을 읽는다. **슬랙 토큰이 필요 없다.**
- 개인 토큰 수집기(`fetch_slack.py`)는 **비공개 채널과 NAS 에 없는 공개 채널만** 받는다. NAS 에 있는 채널은 채널 ID 로 판정해 건너뛴다.
- 수집기 버그 수정: 같은 날 다시 받을 때 그날 앞부분이 지워지던 문제를 고쳤고, 최근 3일 원글을 다시 훑어 **늦게 달린 답글**도 잡는다.
- `/slack-ingest` 가 NAS 를 먼저 읽고, 정리한 항목마다 **슬랙 메시지 링크**를 붙인다. 공개 채널 메시지 링크는 전사 위키에도 출처로 올릴 수 있다.
- `SLACK-GUIDE.md` 를 공개 채널(NAS 로그인, 모두)과 비공개 채널(토큰, 필요한 사람만) 두 단계로 나눴다. 슬랙 앱 공개 배포(Distribution) 경고를 넣고 DM 권한 안내는 뺐다.

### 사람이 할 일
- **NAS 폴더에 한 번 로그인한다.** Windows 는 탐색기 주소창에 `\\192.168.0.225\wiki-share`, macOS 는 Finder `⌘K` → `smb://192.168.0.225/wiki-share`. 재택이면 VPN 을 먼저 연결한다(SLACK-GUIDE §2).
- 확인: `python tools/slack-ingest/nas_slack.py --check` — 채널 목록과 마지막 갱신 시각이 나오면 된다.
- 슬랙 토큰을 쓰던 사람: 슬랙 앱에 DM 권한(`im:history`·`mpim:history`)을 넣었다면 빼고 다시 설치한다(선택). `channels.json` 의 공개 채널은 그대로 둬도 되고, NAS 에 있는 것은 자동으로 건너뛴다.

## v3 · 2026-09-16 · 계정·비밀번호·키는 원문에도 남기지 않는다

### 바뀐 것
- `tools/secret_mask.py` — 슬랙 수집기가 파일을 쓰기 직전에 계정·비밀번호·키를 `[자격증명 가림]` 으로 바꾼다.
- `tools/hooks/pre-commit` — 그래도 새어 들어온 것을 **커밋 단계에서 막는다.** 규칙은 `tools/sensitive-check.txt` 의 `[credentials]` 한 곳이다.

### 사람이 할 일
- 커밋 차단 훅 등록: Windows `powershell -File tools/install-secret-hook.ps1`, macOS·Linux `git config core.hooksPath tools/hooks && chmod +x tools/hooks/pre-commit`.
- 슬랙 토큰을 쓰던 사람: `python tools/slack-ingest/fetch_slack.py --mask-existing` 으로 이미 받아 둔 원문의 값을 지운다. **git 이력에 이미 올라간 값은 지워지지 않으므로, 노출된 비밀번호는 바꾼다.**

## v2 · 2026-09-15 · 공유 할 일은 GitHub, 지식은 전사 위키 PR

### 바뀐 것
- 할 일 도구 `task-new`·`task-list`·`task-update`·`task-close`(`tools/company-wiki.py`). **늦어지면 남이 불편해지는 일(공유 할 일)은 GitHub issue**, 나만 불편한 일(개인 할 일)은 개인 보드에 둔다. 만들기·배정·닫기는 미리보기 뒤 승인받아야 실행된다.
- 지식 올리기 `wiki-pr`(전사 위키 PR + 리뷰어 지정), 내 회의록·논문 원문은 `mine-put`.
- `/eod` 가 마무리에서 개인 위키를 커밋·push 하고, `/morning` 이 나에게 배정된 issue 를 읽어 온다.
- 기능 채널 이름 규칙 `<제품>-feat-<기능>`(예 `fh-feat-분만-알림`), 기존 채널에서는 머리말 태그 `[fh-분만-알림]`.
- 이미 쓰던 위키를 회사 GitHub 과 잇는 안내 `GITHUB-CONNECT.md`.

### 사람이 할 일
- 할 일 보드 권한 한 번: `gh auth refresh -h github.com -s project`
- 확인: `python tools/company-wiki.py whoami` · `python tools/company-wiki.py task-list --mine`

## v1 · 2026-09-13 · 일일 리포트를 전사 위키로

### 바뀐 것
- `tools/company-wiki.py` — 일일 리포트 공유본을 전사 위키 `raw/reports/daily/<나>/` 에 올리고(`daily-put`), 팀 리포트를 읽는다(`daily-get`). 자비스 EOD 저장을 대신한다.
- 올리기 직전 민감 정보 기계 검사(`tools/sensitive-check.txt`), 혼자 설정하는 매뉴얼 `START-HERE.md`.
- 포크로 만든 위키는 조직 사람이 볼 수 있으므로 독립 저장소로 옮긴다(`MIGRATE-FROM-FORK.md`).

### 사람이 할 일
- `gh auth login` 뒤 `python tools/company-wiki.py whoami` 로 내 이름·파트가 나오는지 확인한다.
- 포크로 만들었다면 `MIGRATE-FROM-FORK.md` 를 따라 옮긴다.
