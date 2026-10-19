# 개인 위키를 회사 GitHub 과 연결하기

> 이미 개인 위키를 쓰고 있는 사람이 **전사 위키와 할 일 보드(Bodit Tasks)** 를 쓰도록 연결하는 안내다. 15분 정도 걸린다.
> **템플릿을 다시 복사하지 않는다.** 다시 복사하면 그동안 쌓은 일일 리포트·메모·생각이 사라진다. 새 도구와 커맨드만 받아 온다.

연결하면 개인 위키에서 말로 이런 일을 할 수 있다.

| 할 수 있는 것 | 예 |
|---|---|
| 일일 리포트를 전사 위키에 올린다 | `/eod` |
| 어제 팀 리포트를 읽는다 | `/morning` |
| 공유 할 일을 GitHub 에 올린다 | "이거 공유 할 일로 올려줘. 담당 jeremy, 마감 9월 30일" |
| 내 할 일을 본다 | "내 공유 할 일 보여줘" |
| 굳은 결정을 전사 위키에 올린다 | "이 결정 전사 위키에 PR 로 올려줘. 리뷰어는 bley" |

---

## 0. 내 상황 고르기

| 지금 상태 | 할 일 |
|---|---|
| 개인 위키가 아직 없다 | 이 문서 대신 [START-HERE.md](START-HERE.md) 를 처음부터 따라 한다. 연결까지 그 안에 들어 있다 |
| 개인 위키를 **Fork** 로 만들었다 | [MIGRATE-FROM-FORK.md](MIGRATE-FROM-FORK.md) 로 먼저 옮기고, 이 문서 1절로 온다 |
| **Use this template** 으로 만들었다 | 이 문서 1절부터 |
| ZIP 으로 받아 내 컴퓨터에서만 쓴다 | 이 문서 1절부터. 2절은 2-B 를 따른다 |
| 잘 모르겠다 | 개인 위키 폴더에서 Claude 에게 "내 개인 위키가 포크인지, 템플릿으로 만든 건지 확인해줘" 라고 묻는다 |

---

## 1. 준비물 확인

### 1-1. 회사 GitHub 조직 멤버인가

브라우저에서 https://github.com/bodit-inc 를 열어 저장소 목록이 보이면 된다. 안 보이면 메일함에서 **bodit-inc 조직 초대 메일**을 찾아 수락한다. 초대 메일이 없으면 Kevin 에게 요청한다.

조직은 **2단계 인증**을 요구한다. 설정이 안 되어 있으면 GitHub 이 안내하는 대로 켠다.

### 1-2. GitHub CLI 로그인

개인 위키 폴더에서 Claude Code 를 열고 이렇게 말한다.

```
GitHub CLI 가 설치돼 있고 로그인돼 있는지 확인해줘. 안 돼 있으면 설치와 로그인을 도와줘.
```

직접 하려면 터미널에서 `gh auth status` 를 실행한다. `Logged in to github.com` 이 보이면 된다.

### 1-3. 할 일 보드 권한 추가

할 일 보드를 읽고 쓰려면 로그인 토큰에 `project` 권한이 하나 더 필요하다. **처음 한 번만** 한다.

```
gh auth refresh -h github.com -s project
```

1. 화면에 나온 **일회용 코드**를 복사한다.
2. 브라우저에서 https://github.com/login/device 를 열고 코드를 넣는다.
3. **Authorize** 를 누른다.

코드는 약 15분 동안 유효하다. **Claude Code 안에서 실행하면 승인 결과를 받아 오다가 `context deadline exceeded` 로 끝나는 경우가 있다.** 그때는 Claude Code 밖의 터미널(Windows Terminal, macOS 터미널)에서 같은 명령을 실행한다.

끝났는지는 `gh auth status` 의 `Token scopes` 에 `'project'` 가 있는지로 확인한다.

### 1-4. Python

`python --version` 이 3.9 이상이면 된다. 없으면 Claude 에게 "Python 설치 도와줘" 라고 한다.

---

## 2. 템플릿의 새 파일 받기 — 내 기록은 그대로

### 가장 쉬운 방법

1절이 끝났으면 개인 위키 폴더의 Claude Code 에 이렇게 말한다.

```
gh 로 bodit-inc/llm-wiki-template 의 UPDATE.md 를 읽고 "처음 한 번" 을 따라 해줘.
바꾸기 전에 무엇이 바뀌는지 먼저 보여줘.
```

동기화 도구 `tools/template-sync.py` 를 받아 한 번 돌리는 것이 전부다. 그다음부터는 `/template-update` 한 줄이면 된다.

### 2-A. 무엇이 일어나나

- 템플릿의 **모든 새 파일과 고쳐진 파일**을 받아 온다. 받을 목록을 사람이 관리하지 않으므로 새 도구가 빠지지 않는다.
- 내가 안 고친 파일은 새 판으로 바뀌고, **내가 고친 파일(`CLAUDE.md` 포함)은 3방향으로 합친다.** 합치지 못한 것만 Claude 와 함께 합친다.
- 내가 지운 파일은 다시 받지 않는다. 내가 따로 만든 커맨드는 그대로 남는다.
- 판마다 무엇이 바뀌고 **사람이 무엇을 해야 하는지**는 템플릿의 `CHANGELOG.md` 에 있다. 도구가 그것을 함께 보여 준다.

### 2-B. 절대 덮지 않는 것

| 파일·폴더 | 이유 |
|---|---|
| `me.md` | 내가 누구인지 적은 파일 |
| `brain/` · `raw/` · `wiki/` | 내 생각·리포트·지식 |
| `index.md` · `log.md` | 내 위키 목록과 기록 |
| `tools/slack-ingest/channels.json` · `.env` | 내 비공개 채널 설정과 토큰, NAS 경로 |

규칙은 `tools/template-sync-rules.txt` 에 있다. 크게 고친 커맨드가 있으면 그 줄을 `keep` 으로 올려 갱신에서 뺄 수 있다.

### 2-C. 저장

바뀐 파일과 `.template-version` 을 커밋한다. `/template-update` 가 여기까지 해 준다.

---

## 3. 전사 위키에 내 GitHub 계정이 있는지 확인

```
python tools/company-wiki.py whoami
```

내 이름과 파트가 나오면 된다. 전사 위키 `people/<내이름>.md` 의 `github:` 한 줄로 나를 찾는다.

`github: <계정> 을 찾지 못했다` 가 나오면 내 프로필에 계정이 없는 것이다. 개발팀은 대부분 이미 들어 있다. 없으면 Kevin 에게 요청하거나, https://github.com/bodit-inc/bodit-llm-wiki 에서 `people/<내이름>.md` 를 열어 연필 아이콘으로 `github: <내 계정>` 한 줄을 넣는다.

---

## 4. 연결 확인 — 명령 세 개

| 명령 | 정상이면 |
|---|---|
| `python tools/company-wiki.py whoami` | 내 이름·파트가 나온다 |
| `python tools/company-wiki.py daily-get --date <어제 날짜>` | 어제 올라온 팀 리포트와 "쓴 사람·안 쓴 사람"이 나온다 |
| `python tools/company-wiki.py task-list --mine` | 내 할 일 목록이 나온다. 비어 있어도 오류만 없으면 된다 |

셋 다 되면 끝이다. Claude 에게 "회사 GitHub 연결됐는지 확인해줘" 라고 해도 된다.

---

## 5. 이제 이렇게 쓴다

**할 일을 어디에 둘지는 질문 하나로 가른다: "이 일이 늦어지면 나 말고 누가 불편해지는가?"**

| 답 | 이름 | 두는 곳 |
|---|---|---|
| 나만 불편하다 | **개인 할 일** | 개인 위키 보드 (`wiki/tasks/board.md`) |
| 남이 불편하다 | **공유 할 일** | GitHub 할 일 (코드 PR 로 끝나면 그 코드 저장소, 아니면 `bodit-ops-tasks`) |

**올리기 전에는 항상 확인 화면이 나온다.** 이슈는 만드는 순간 담당자에게 알림 메일이 가서 되돌릴 수 없기 때문이다. 확인 화면을 보고 "올려" 라고 해야 올라간다.

| 하고 싶은 것 | 이렇게 말한다 |
|---|---|
| 하루 마감 | `/eod` — 리포트를 전사 위키에 올리고, 공유 할 일은 이슈 초안으로 보여 준다 |
| 하루 시작 | `/morning` — 어제 팀 리포트와 내 GitHub 할 일을 모아 오늘 할 일 초안을 만든다 |
| 할 일 올리기 | "회의에서 나온 이거 공유 할 일로 올려줘. 담당 lia, 마감 10월 2일" |
| 할 일 상태 바꾸기 | "bodit-ops-tasks 12번 진행 중으로 바꿔줘" |
| 할 일 닫기 | "12번 끝났어. 닫아줘" |
| 지식 올리기 | "이 결정 전사 위키에 PR 로 올려줘. 리뷰어는 john" (`/promote`) |
| 회의록 올리기 | `/meeting-ingest` 끝에서 "전사에 올릴까요?" 를 묻는다 |

보드 화면은 https://github.com/orgs/bodit-inc/projects/7 에서 본다. 규칙 원문은 전사 위키 `docs/guide/task-policy.md` 에 있다.

---

## 6. 막혔을 때

| 화면에 나온 것 | 뜻 | 이렇게 한다 |
|---|---|---|
| `gh: command not found` | GitHub CLI 가 없다 | Claude 에게 "GitHub CLI 설치 도와줘" |
| `HTTP 401` · `gh auth login` 안내 | 로그인이 풀렸다 | `gh auth login` 을 다시 한다 |
| `missing required scopes [project]` · 보드 조회 실패 | 1-3 을 안 했다 | `gh auth refresh -h github.com -s project` |
| `context deadline exceeded` | Claude Code 안에서 인증 결과를 못 받았다 | Claude Code 밖의 터미널에서 같은 명령을 실행한다 |
| `refusing to merge unrelated histories` | merge 로 받으려 했다 | merge 를 취소(`git merge --abort`)하고 2-A 의 파일 단위 방법을 쓴다 |
| `github: ... 을 찾지 못했다` | 전사 위키 내 프로필에 계정이 없다 | 3절 |
| `HTTP 404` · 저장소를 찾을 수 없다 | 조직 멤버가 아니거나 초대를 수락하지 않았다 | 1-1 |
| `민감 정보 검사에 N건이 걸렸다` | 전화번호·금액 같은 것이 들어 있다 | 가리고 다시 올린다. 확인해 보니 괜찮은 것이면 그 항목을 승인한 뒤에 올린다 |
| 무엇이 잘못됐는지 모르겠다 | | 화면에 나온 문장을 그대로 Claude 에게 보여 준다. 올리기 전에는 확인 화면이 있어서 잘못 올라간 것은 없다 |
