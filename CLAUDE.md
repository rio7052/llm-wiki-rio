# CLAUDE.md — 개인 LLM wiki schema

@me.md

> 위 `@me.md` 는 운영자(나)의 정체성·맥락(PCM 단일 진실)을 자동 로드한다.
> 이 CLAUDE.md 는 wiki 의 schema(구조·포맷·워크플로우)를, me.md 는 '나'(Meaning·Assets)를 담는다 — 역할이 다르다.

> 개인 LLM wiki schema 템플릿. Karpathy 의 LLM Wiki 패턴 + 일일/월간 업무 리포트 통합.
> 1인 운영. 본인이 자유롭게 진화시킨다. 변경 시 commit message 에 이유 명시.
>
> 이 파일은 **스타터 키트 템플릿**이다. `<...>` 표시는 본인 환경에 맞게 채운다. 처음엔 그대로 써도 되고, 안 쓰는 규칙은 지워도 된다.

## 1. What this repo is

이 repo 는 **나의 개인 LLM wiki** 다. 다음을 누적한다.

- Entity·concept·domain knowledge (학습한 사실·도구·개념)
- 본인 차원의 기술·업무 결정 ADR
- 자주 하는 작업의 playbook
- **일일/월간 업무 리포트** (업무 누적)
- Synthesis (재사용 가치 있는 Q&A 답변)

**레이어 (3-brain)**:
- `raw/` — 원본 소스(캡처한 재료). **불변(immutable)**. 일일 raw 리포트도 여기. **md 로 변환해 git 추적**(§4.3). (2nd brain 의 입력)
- `brain/` — **2nd brain**. 내가 쓴 생각·가설·반론. editable. `brain/README.md` 참조.
- `wiki/` — **3rd brain**. AI 가 컴파일한 합성 페이지. 직접 편집·유지.
- `CLAUDE.md` (이 파일) — schema. 본인이 진화시킴.

> 1st brain(직관·감성)은 나 자신 — 파일이 아니다. brain note 가 그 1st brain 을 글로 끄집어내 2nd brain(`brain/`)에 적재하고, AI 가 컴파일해 3rd brain(`wiki/`)을 만든다.

**핵심 인덱스**:
- `index.md` — 전체 페이지 카탈로그
- `log.md` — 시간순 활동 로그 (append-only)

> 이 위키는 **개인 private repo**(전사 템플릿에서 **Use this template** 으로 만든 독립 저장소)다. **포크면 조직 권한을 물려받아 남이 볼 수 있으므로** [MIGRATE-FROM-FORK.md](MIGRATE-FROM-FORK.md) 로 옮긴다. 회사 공용 지식은 **전사 LLM wiki** 에 있고, 이 위키에서 참조·승격한다 — 경계와 절차는 §17.

---

## 2. 경계 — 개인 wiki / 전사 wiki / 진행관리 도구

세 곳을 쓰므로 무엇을 어디에 둘지 먼저 정한다. **판정 한 줄: 다른 사람이 알아야 하나? → Yes 면 전사 wiki, No 면 여기.**

### 개인 wiki(여기)에만 둔다
- 내 회고·생각·가설·반론 (`brain/`) — **절대 전사로 흐르지 않는다**
- 내 일일 raw 리포트, 개인 태스크 보드
- 아직 안 굳은 초안·개인 학습 메모

### 전사 wiki 로 보낸다 (§17)
- 업무 진행 상황·산출물 (일일/월간 리포트의 **공유 가능분**)
- 배운점·교훈 중 다른 파트가 알면 좋은 것
- 회사 공용 결정·용어·entity·프로젝트 지식

### Wiki 에만 둔다 (진행관리 도구가 아니라)
- Entity (도구·라이브러리·하드웨어·플랫폼·고객사)
- Concept (개념·기법·이론)
- Decision (확정된 본인 ADR)
- Domain knowledge — 본인 도메인의 누적 지식 (`wiki/domains/<area>/`)
- Playbook
- **일일/월간 업무 리포트** (업무 누적)
- **개인 태스크 보드** — 확인 필요·할일·우선순위. `wiki/tasks/board.md` (§15)

### 진행관리 도구(Notion·Jira 등)에만 둔다
- 팀 sprint·OKR (회사 표준 도구). **단 개인 태스크 보드는 위키**(§15)
- 공유 할 일은 **GitHub issue** 로 둔다. 조직 보드 Bodit Tasks 가 모아 보여 준다(§17.3)
- 회의록 raw, 1:1 노트
- 진행 중 초안 (작성 중인 제안서)

### Slack
- **공개 채널은 전사 공용 보관함(NAS `wiki-share`)에서 읽는다**(2026-09-17). 분석파트 워크스테이션이 매시 받아 개인정보를 가린 사본이라 모두가 같은 것을 본다. **비공개 채널은 필요한 사람만** 개인 토큰으로 `raw/slack/` 에 받는다(§7.7). 처음 연결은 [SLACK-GUIDE.md](SLACK-GUIDE.md).
- 위키엔 합성·마스킹만 올린다. 원문 통째 복사 금지. NAS 사본은 회사 밖으로 내보내지 않는다.

### 이전 트리거
- 일일 리포트에서 굳어진 결정·교훈 → wiki `decisions/`, `playbooks/` 로 합성·추출
- 회의에서 entity·decision 굳음 → wiki 에 ingest
- 외부 페이지 통째 복사 금지. wiki 페이지는 항상 합성된 형태.
- 공유 가치가 생기면 → 전사 wiki 승격 제안(§17)

---

## 3. Language policy

> 아래는 한국어 본문 기준 예시다. 본인 주력 언어로 바꿔도 되지만, **구조(파일명·태그·slug)는 영어 kebab-case 로 통일**하길 권장한다 (grep·URL·git diff 안정).

**섞어쓰기**:
- **본문(prose)**: 본인 주력 언어, 평어체(~한다, ~이다). 존댓말·이모지 X.
- **frontmatter, 필드명, 태그, slug, 디렉토리명, 파일명**: 영어, kebab-case
- **wikilink target**: 영어 slug — 예: `[[entities/some-sensor]]`. 표시 텍스트는 본문 언어 가능 — `[[entities/some-sensor|어떤 센서]]`
- **코드·명령어·변수명**: 원어 그대로
- **인용·발췌**: 원문 언어 그대로
- **영어 용어가 본문에 등장 시**: 그대로 영어 (번역 강요 금지). 예: "Focal Loss 를 적용해서 class imbalance 를 처리했다."

**용어 통일이 위키의 핵심 가치다.** 같은 entity 는 같은 페이지에.

---

## 4. Directory rules

### 4.1 What goes where

```
raw/            ← 전부 .md (§4.3). 원본 바이너리는 커밋되지 않는다
├── articles/      ← 웹 아티클 (변환 .md)
├── papers/        ← 논문 요약·발췌 .md (/pdf-ingest, §7.8). 원본 PDF 는 로컬에만
├── notes/         ← 본인 메모 + 회의록·보고서 .md (/pdf-ingest, §7.8)
├── reports/
│   └── daily/     ← 본인 일일 raw 업무 리포트 (YYYY-MM-DD.md)
├── slack/         ← 비공개 채널 수집 원문 (<channel>/YYYY-MM-DD.md, 선택). 공개 채널은 NAS 에서 읽는다. §7.7
└── assets/        ← 외부 이미지 참조 stub(.md). 이미지 파일 자체는 wiki/assets 로

brain/             ← 2nd brain. 내 생각·가설. editable
├── README.md      ← 레이어 정의 (3-brain 위치)
├── TEMPLATE.md    ← brain note 템플릿
└── <slug>.md      ← 개별 brain note

wiki/
├── entities/      ← 도구·라이브러리·하드웨어·플랫폼·고객사
├── concepts/      ← 개념·기법·방법론·이론
├── domains/<area>/← 도메인별 누적 지식
├── projects/<proj>/← 프로젝트
├── tasks/         ← 태스크 보드 (board.md — 확인 필요·할일·우선순위). §15
├── decisions/     ← 본인 차원 의사결정 (ADR)
├── playbooks/     ← "어떻게 X 하는가"
├── reports/
│   └── monthly/   ← 월간 합성 리포트 (YYYY-MM.md)
├── syntheses/     ← Query 답변 중 재사용 가치 있는 것
└── assets/        ← 위키 내부에서 만든 산출물 (§11)
    ├── charts/    ← 차트·다이어그램 이미지
    └── reports/   ← 남에게 건네는 완성 산출물 (회의록 PDF·리포트 HTML 등). §11.1
```

### 4.2 Naming
- 모든 파일·디렉토리: **kebab-case 영어**. 예: `rotation-invariant-features.md`
- `decisions/`: `YYYY-MM-<short-title>.md`. 예: `2026-03-downsampling-25hz.md`
- `brain/`: `<slug>.md`, kebab-case 영어. 예: `honest-eval-beyond-leak.md`
- `raw/reports/daily/`: `YYYY-MM-DD.md`. 예: `2026-05-18.md`
- `wiki/reports/monthly/`: `YYYY-MM.md`. 예: `2026-05.md`
- 비-영어 파일명·디렉토리명 금지

### 4.3 raw 정책 — immutable · md-only · git 추적

**① immutable**: `raw/` 아래 파일은 **수정·삭제·이름변경 금지**. 새 파일 추가만 가능.
- **예외**: 일일 리포트는 그날 본인이 채워가는 것이므로 **작성 당일 자정까지 수정 OK**. 다음 날부터 immutable. (`raw/slack/` 은 수집기가 관리하는 캐시 — 같은 날짜를 다시 받으면 그날 파일을 통째로 다시 쓴다. 사람이 수동 편집하지 않는다.)

**② md-only**: raw 에 들어가는 것은 **전부 markdown** 이다. PDF·이미지·jsonl 등 원본 바이너리는 `.gitignore` 가 막는다(커밋 안 됨).
- 외부 자료를 넣을 땐 **읽고 md 로 변환·요약해서** 저장한다. 원본 파일은 본인 로컬 어디든 두되 위키에 커밋하지 않는다.
- 이유: ① 어디서든(웹 Claude Code 포함) clone 해서 바로 읽힌다 ② LLM 이 바로 읽는다 ③ repo 가 안 무거워진다 ④ git diff 로 이력이 남는다.

**③ git 추적**: raw 도 커밋한다(개인 private repo 전제). 백업·이력·기기 이동이 git 하나로 해결된다.
- 그래도 **마스킹(§9)은 raw 에도 적용**한다 — 계정·토큰·급여·계약액·개인 식별 정보는 raw 단계에서 이미 지운다. "private repo 니까 괜찮다" 로 넘기지 않는다.
- 공유하면 안 되는 회고·민감 메모는 애초에 raw 가 아니라 `brain/` 에 두고, 전사로 승격하지 않는다(§17).

---

## 5. Page format

모든 wiki 페이지는 frontmatter + 본문:

```markdown
---
type: entity | concept | domain | decision | synthesis | playbook | report | brain-note | task-board
category: <free-text, e.g. hardware/imu, ml/loss-function>
aliases: [<alt names>]
tags: [<lowercase-kebab>, ...]
status: active | draft | superseded | archived
sources: <count of raw/ files referenced>
last_updated: YYYY-MM-DD
---

# <Title>

<1–2줄 요약>

## <Section headers>
...

## 관련 페이지
- [[entities/...]]
- [[concepts/...]]

## Sources
- [[raw/papers/...]]
- [[raw/notes/...]]
```

### 5.1 Required fields
- `type` 필수
- `last_updated` 필수, 수정 시 매번 갱신
- `tags` 최소 1개, lowercase-kebab 만

### 5.2 Page-type specifics
- **entity**: 한 줄 정의 → 핵심 스펙/사실 → 운영 컨텍스트 → 관련 → Sources
- **concept**: 한 줄 정의 → 직관 → 수식·메커니즘 → 실무 적용 → trade-offs → 관련 → Sources
- **decision**: Context → Decision → Consequences → Alternatives Considered → 관련 → Sources
- **playbook**: 목적 → 사전조건 → 단계별 절차 → 자주 발생하는 문제 → 관련 → Sources
- **synthesis**: 답변한 질문 → 답변 본문 → 가정·한계 → 관련 → Sources
- **brain-note** (`brain/`): 2nd brain. 추가 frontmatter `seed`(핵심 생각 한 문장), `status`(seed | growing | evergreen), `created` 필수. 본문: 배경 → 공명 → 확장 → 통합(triple+wikilink) → 탐색. 중립 요약이 아니라 주관·가설·반론. 템플릿 `brain/TEMPLATE.md`
- **report**: 추가 frontmatter `report_kind`(daily | monthly), `period`(YYYY-MM-DD | YYYY-MM) 필수
  - **daily** (`raw/reports/daily/`): 한 일 / 발견 / 배운점·느낀점 / 결정 / 막힘 / 내일 할 일
  - **monthly** (`wiki/reports/`): 주요 산출물 / 주요 결정 / 신규 지식 / 반복된 issue / 다음 우선순위 — 일일 raw 링크 + 신규 wiki 페이지 wikilink 포함
- **task-board** (`wiki/tasks/board.md`): 살아있는 단일 보드. 섹션 = 📥 Inbox / 👀 확인 필요 / 🔥 우선 / 📋 진행 중 / ⏳ 대기 / ✅ 최근 완료. 라인 `- [ ] <할 일> · src:<출처> · @담당 · due:… · note:…`. GitHub issue 로 옮긴 줄은 끝에 `gh:<owner/repo#n>` 을 붙이고, 그 줄의 상태는 GitHub 이 원본이다. report 와 달리 immutable 아님. 상세 §15

---

## 6. Wikilinks

- 영어 slug 사용: `[[entities/some-chip]]`
- 표시 텍스트: `[[entities/some-chip|어떤 칩]]`
- **고립 금지**: 들어오는 링크가 하나도 없는 **고립 페이지**를 만들지 않는다. 페이지를 만들 때 들어오는 링크를 1개 이상 확보하고, 관련 페이지 2–3개에 새 페이지로 향하는 링크를 추가한다.

---

## 7. Operations

### 7.0 Slash commands — Actions 레지스트리

이 wiki 의 정형화된 작업은 `.claude/commands/*.md` 의 slash command 로 수행한다. 상세 절차는 각 커맨드 파일에.

| command | 하는 일 | 상세 |
|---------|---------|------|
| `/morning` | 아침 시작 — 오늘 자리 + 어제 + 전사 확인 + **오늘 일정·메일**(Calendar·Gmail) → 할 일 확정 | `morning.md` |
| `/log` | **세션 자동 캡처** — 모든 레포 세션에서 한 일을 뽑아 오늘 리포트에 적재 (§7.11). 인자 주면 수동 한 줄 | `log.md` |
| `/eod` | 퇴근 마감 — 일일 리포트(회고) + 지식화 + **전사 필수 업데이트**(§17.3) | `eod.md` |
| `/brain` | brain note(2nd brain) 작성 | `brain.md` |
| `/brain-check` | brain 거리 감지·제안 (상시) | `brain-check.md` |
| `/promote` | 개인 위키 산출물을 전사 wiki 로 승격 (§17) | `promote.md` |
| `/template-update` | 템플릿 새 판 받기 — 내 기록은 그대로, 내가 고친 파일은 합친다 (§14.5) | `template-update.md` |
| `/pdf-ingest` | 외부 PDF → md 변환 → raw → 개인지식화 (§7.8) | `pdf-ingest.md` |
| `/meeting-ingest` | 회의 스크립트·메모 → **원문 + 정리본**(액션 표 포함) (§7.12) | `meeting-ingest.md` |
| `/monthly` | 월간 합성 — 한 달 일일을 월간 리포트로 (§7.4) | `monthly.md` |
| `/slack-ingest` | 슬랙 대화(공개 채널은 **NAS 공용 보관함**, 비공개 채널은 선택 수집) → 지식화 + 태스크 추출 (§7.7) | `slack-ingest.md` |
| `/repo-ingest` | *(개발자용)* 코드 레포의 새 작업을 위키로 pull (§7.9) | `repo-ingest.md` |
| `/session-retro` | *(개발자용)* Claude Code 세션 회고 → 룰·skill 승격 (§7.10) | `session-retro.md` |

새 커맨드를 추가하면 이 표와 해당 §7.x 절차를 함께 갱신한다.

> **하루 루프는 `/morning` → `/log` → `/eod` 3개면 충분하다.** 나머지는 필요해질 때 하나씩 켠다.
> *(개발자용)* 표시 커맨드는 코드 레포를 다루는 사람만 쓴다 — 안 쓰면 파일을 지워도 된다.
> 외부 종속성: `/slack-ingest` 는 사내망의 NAS 로그인(비공개 채널까지 보려면 Slack 토큰), `/promote` 와 전사 참조는 전사 wiki 접근(§17)이 필요하다. 나머지는 설정 없이 바로 동작한다.

### 7.1 Ingest — 새 외부 소스 처리

1. **읽기**: 소스 전체. URL 이면 변환 후 `raw/articles/` 에 저장. PDF 는 `/pdf-ingest`(§7.8) — Read 툴이 페이지 단위로 바로 읽으니 변환 불필요.
2. **토론**: 핵심 takeaway 3–5개 짧게 → "이 중 위키에 반영할 핵심" 확인. 장황한 요약 금지.
3. **확정 후 작성**:
   - 소스 자체 페이지 안 만듦 (raw/ 에 있음)
   - 영향 받는 기존 entity/concept 페이지 **갱신** (새 사실, 모순 플래그, 출처 추가)
   - 새 entity/concept 필요시 신규 작성
   - 각 페이지의 `last_updated` 갱신, `sources` 카운트 +1
4. **index.md** 신규 페이지 추가
5. **log.md** append (§8.2 형식)
6. commit

**한 번에 한 source 씩.** 배치 ingest 는 명시적 요청 시에만.

### 7.2 Query

1. `index.md` 에서 관련 페이지 식별 → 해당 페이지 읽기 → 필요시 링크 따라가기
2. 위키 정보 충분성 판단: 충분 → 답변 + 인용 wikilink / 부족 → "위키에 이 정보 없음. raw/<file> 추가로 읽을까요?"
3. 답변 형식 자유: prose / 표 / 코드 / 다이어그램
4. **가치 있는 답변은 묻기**: "이 답변을 `wiki/syntheses/<slug>.md` 로 저장할까요?" (분석·합성성 → 저장 / 단순 fact → 저장 안 함)

### 7.3 Daily report — 일일 업무 리포트

1. 그날 일과 종료 시 `raw/reports/daily/YYYY-MM-DD.md` 작성 (보통 `/eod` 가 수행)
2. frontmatter: `type: report`, `report_kind: daily`, `period: YYYY-MM-DD`, `tags`
3. 본문 섹션: **한 일 / 발견 / 배운점·느낀점 / 결정 / 막힘 / 내일**
4. 굳어진 entity·concept·decision 은 **별도로** wiki 에 ingest (일일 리포트는 raw 유지)
5. **공유본 산출 → 전사 업로드**(§17.3, 연결 시): 위 리포트에서 민감분(면담·1:1·타인 판단·개인 사정·급여·처우·계약액·아직 공유 못 할 판단)을 걷어낸 판을 `python tools/company-wiki.py daily-put` 으로 전사 위키 `raw/reports/daily/<나>/` 에 올린다.
   - **원본은 여기, 공유본은 전사.** 두 번 쓰는 게 아니라 같은 리포트의 공유 버전이다.
   - 무엇을 걷어냈는지 보여주고 올린다. 공유할 게 없으면 올리지 않는다.
6. log.md append

### 7.4 Monthly report — 월간 합성

1. 매월 1일(전월 결산) 작성
2. `wiki/reports/monthly/YYYY-MM.md`
3. 한 달치 일일 raw 리포트를 훑고 합성: 주요 산출물 / 주요 결정 / 신규 지식 / 반복된 issue / 다음 우선순위
4. index.md, log.md 갱신

### 7.5 Lint — 월 1회 (요청 시)
모순 / 고립 페이지 / 언급되지만 페이지 없는 개념 / stale(6개월+) / 누락 cross-reference / 데이터 갭 을 보고만 한다. 수정은 별도 commit.

### 7.6 New decision — 결정 기록
대화 중 결정이 굳어지면 LLM 이 **적극 제안**: "이거 `decisions/` 에 기록할까요?" → 승인 시 ADR 형식으로 `wiki/decisions/YYYY-MM-<slug>.md` 작성, 영향 받는 페이지에서 wikilink.

### 7.7 Slack ingest — 슬랙 대화 지식화

**공개 채널은 전사 공용 보관함에서 읽는다**(2026-09-17). 분석파트 워크스테이션이 공개 채널을 매시 정각에 받아 개인정보를 가린 사본을 사내 NAS `\\192.168.0.225\wiki-share` 에 쌓는다(전사 `wiki/playbooks/slack-archive.md`). 모두가 같은 사본을 보므로, 사람마다 공용 채널을 제각각 모아 서로 다른 사실을 보게 되는 문제가 없다. **비공개 채널은 필요한 사람만** 개인 토큰으로 받는다. 이때도 NAS 에 있는 채널은 받지 않는다 — 같은 공개 채널을 가리기 전 원문으로 따로 읽으면 NAS 마스킹이라는 관문이 무의미해지기 때문이다. 처음 연결은 [SLACK-GUIDE.md](SLACK-GUIDE.md).

`/slack-ingest` 가 수행. 상세는 `.claude/commands/slack-ingest.md`. 도구는 `tools/slack-ingest/README.md`.
1. **읽을 대상**:
   - **NAS**: `tools/slack-ingest/nas_slack.py --pending` 이 커서 이후 메시지를 메시지 링크와 함께 낸다. 분량이 2만 토큰을 넘으면 `--stats` 로 먼저 재고 채널을 좁힌다. 사내망 전용이라 재택이면 VPN 이 필요하다.
   - **비공개 채널(선택)**: 인자로 채널을 지정하거나, 비우면 `channels.json` 의 후보를 **보여주고 고르게 한다**(전체 자동 수집 금지). `tools/slack-ingest/fetch_slack.py` 가 `raw/slack/<channel>/YYYY-MM-DD.md` 로 받는다.
2. **NAS 원칙**: 사람이 검토하지 않은 기계 가공본이다. 정리한 항목마다 **메시지 링크**를 달고, 숫자·결론은 원문을 확인하기 전까지 "누가 이렇게 말했다" 로 적으며, `{SECRET}`·`{TEL_…}` 같은 토큰은 복원하지 않는다.
3. **5가지로 추림**: 지식화 후보 / 확인 필요 / 빠뜨린 것 / 태스크 후보 / 팀 방향 신호.
4. **반영**: 확인 필요·태스크 → 보드(공유 할 일은 `task-new` 초안을 보여 주고 승인받는다, §17.3) / 생각·교훈 → brain note / 확정 결정·개념 → wiki. 어느 채널發이든 **회사 공용 결정이면 마스킹·합성해 전사 승격 제안**(§17).
   - **Slack 링크**: 공개 채널 메시지 링크(`…/archives/<채널ID>/p<16자리>`)는 출처로 남긴다. 비공개 채널 링크와 첨부 파일 링크는 걷어낸다. 전사 업로드 기계 검사(`tools/sensitive-check.txt`)도 메시지 링크만 통과시킨다.
5. index.md·log.md 갱신. 다 반영했으면 `nas_slack.py --mark` 로 NAS 커서를 옮긴다(중간에 끊었으면 옮기지 않는다).

> 비공개 채널 원문은 가리기 전 원문이라 민감도가 높다. raw 도 git 에 올라가므로(§4.3) **수집 단계에서 마스킹**하고, 인사·급여·면담 채널은 애초에 `channels.json` 의 `exclude` 에 넣는다.

> **계정·비밀번호·키는 원문에도 안 남긴다**(2026-09-16 신설). 수집기가 파일을 쓰기 직전에 값을 `[자격증명 가림]` 으로 바꾸고, `tools/hooks/pre-commit` 이 그래도 새어 들어온 것을 커밋 단계에서 막는다(등록: `powershell -File tools/install-secret-hook.ps1`). 규칙은 `tools/sensitive-check.txt` 의 `[credentials]` 한 곳이고 전사 업로드 검사도 같은 목록을 쓴다. 이미 쌓인 원문은 `python tools/slack-ingest/fetch_slack.py --mask-existing` 으로 덮어쓴다. **git 이력에 이미 들어간 값은 지워지지 않으므로, 노출된 비밀번호는 바꾼다.** NAS 사본은 워크스테이션이 따로 `{SECRET}` 으로 지운다.
> 개인 위키 저장소가 **포크(fork)면 조직 구성원이 원문을 볼 수 있다** — 비공개 채널을 연결하기 전에 [SLACK-GUIDE.md](SLACK-GUIDE.md) §1-1 로 확인한다.

### 7.8 PDF ingest
`/pdf-ingest` 가 수행. 상세는 `.claude/commands/pdf-ingest.md`. Read 툴로 PDF 직접 읽기(변환 불필요). 논문→`raw/papers/`, 회의록·보고서→`raw/notes/`. takeaway 대화 → 확정분만 §7.1·§5 형식으로 합성. 고립 금지(§6), 마스킹(§9).

### 7.9 Repo ingest *(개발자용)*
`/repo-ingest` 가 수행. 상세는 `.claude/commands/repo-ingest.md`. 코드 레포가 제안해주길 기다리지 않고 **위키에서 직접 `git log/diff` 를 읽어 끌어온다(pull)**. 결정·인터페이스·교훈만 합성하고, **코드와 설계 문서는 복사하지 않는다**(출처로 `<repo>@<hash>:<경로>` 만 남긴다). 다른 사람이 해야 할 후속은 `task-new` 초안 → 승인(§17.2). 대상 레포는 read-only(§13).

### 7.10 Session retro *(개발자용)*
`/session-retro` 가 수행. 상세는 `.claude/commands/session-retro.md`. Claude Code 세션 기록에서 ① 반복된 교정 → 룰 승격 ② 반복 워크플로우 → 새 커맨드 ③ 대화에만 남고 흘러간 결정·생각 회수. **전자동 룰화 금지 — 후보 제시 후 본인이 큐레이션**. 주 1회 권장.

### 7.11 Session capture — 세션에서 자동으로 로그 쓰기 (시간 단위)

`/log` 가 수행. 상세는 `.claude/commands/log.md`. §7.10 이 **주 단위 깊은 회고**라면 이건 **시간 단위 얕은 기록**이다 — 목적은 "무슨 일 했더라"를 저녁에 떠올리지 않게 하는 것. *(Claude Code 를 쓰는 사람만 해당.)*

1. **재료**: `tools/session-digest.py` 가 `~/.claude/projects/**/*.jsonl` 을 훑어 **사용자 발화 + 편집 파일 + 실행 명령 + 커밋**만 남긴 압축 digest 를 만든다. 24시간분 ≈ 10KB. 원본 transcript 는 통째로 읽지 않는다.
2. **커서 기준, 시간 창 아님**: `.log-cursor`(로컬·비추적) 이후 전체를 훑는다. 몇 시간 걸러 돌려도 **누락 없이 따라잡는다**.
3. **전 레포 가로지름**: 어느 워크스페이스·worktree 에서 일했든 한 번에 잡힌다. "다른 레포에서 한 일이 안 남는" 문제를 여기서 막는다.
4. **합성해서 적는다**: 명령 나열이 아니라 작업 단위 한 줄로 묶어 오늘 `raw/reports/daily/` 의 한 일/발견/결정/막힘에 배치. **마스킹(§9)은 여기서 적용** — 세션 원문에는 마스킹이 안 돼 있다.
5. **무인 실행(선택)**: `tools/install-hourly-log.ps1` 로 작업 스케줄러에 걸면 매 시간 자동으로 돈다. 활동이 없으면 LLM 을 호출하지 않아 비용이 안 든다.
6. `/eod` 가 저녁에 이걸 재료로 합성·지식화한다. `/log` 는 캡처만, 판단은 `/eod` 몫.

> **세션 원문 보존**은 별개다: `tools/sync-sessions.ps1` 이 `raw/sessions/` 로 미러하지만 `.jsonl` 은 md-only 규칙(§4.3)상 **git 비추적**이라 로컬에만 남는다. **git 에 남는 영구 기록은 digest 를 합성한 일일 리포트**다.

**밀린 날의 사후 복원**: 리포트를 못 쓴 날이 쌓였으면 `tools/backfill-daily.ps1` 로 세션 기록에서 복원한다. 단 **사실(한 일·발견·결정·막힘)만** 복원하고 **배운점·회고는 복원하지 않는다** — 그건 세션 로그에 없고 사람 머릿속에만 있었다. 추측으로 채우면 거짓 기록이 되므로 백필분에는 그 사실을 본문에 명시한다.

### 7.12 Meeting ingest — 회의 스크립트 → 원문 + 정리본

`/meeting-ingest` 가 수행. 상세는 `.claude/commands/meeting-ingest.md`. 회의 전사 스크립트나 손메모를 던지면 **원문과 정리본을 각각** 남긴다.

1. **원문과 정리본은 다른 파일이다.** 원문은 나중에 "그때 정확히 뭐라고 했더라"를 확인하는 근거이고, 정리본은 읽고 실행하는 물건이다. 섞으면 둘 다 못 쓴다.
2. **구조부터 본다**: 전사 스크립트는 통째로 읽지 않는다. 타임스탬프·발화자 분포·실제 줄 수를 먼저 세고, 빈 줄을 걷어내 청크로 읽는다.
3. **메타는 묻는다**: 전사본에는 표시명만 있고 실제 참석자가 없다. 일시·참석자(소속별)·공유 자료를 확인한다. ⚠️ **화자 분리는 대개 부정확하다** — 한 마이크를 여럿이 쓰면 여러 사람 말이 한 표시명으로 묶이므로, 표시명 하나를 사람 하나로 단정하지 않는다.
4. **원문**: `raw/notes/YYYY-MM-DD-<slug>-transcript.md`. frontmatter·머리말을 붙이고 **마스킹(§9)** 과 발화자 표시명 정리만 한다. 전사 품질·화자 분리의 한계는 **이 파일 머리말에** 적는다.
5. **정리본**: `raw/notes/YYYY-MM-DD-<slug>-minutes.md`. 머리에는 **일시·참석·자료만** 둔다 — 전사 품질이나 복원 방식 같은 작업 메타를 정리본에 섞지 않는다. 본문은 큰 줄기(선택) → 주제별 절 → **우리가 할 일(담당 표)** → 다음 일정 순. **확신이 서지 않는 대목은 옮기지 않는다.**
6. **(선택) PDF**: 남에게 건넬 판이 필요하면 `bash tools/md-to-pdf.sh <입력.md> <출력.pdf> "<제목>"` → `wiki/assets/reports/`(§11.1). md 와 pdf 는 같은 접미사(`-minutes`·`-transcript`)로 짝을 맞춘다.
7. index·log 갱신(`## [YYYY-MM-DD] meeting | <회의명>`), 오늘 일일 리포트에 한 줄. **액션은 태스크 보드 반영을 제안한다**(§15) — 임의로 다 올리지 않는다. 공유 할 일에 해당하는 액션은 `task-new` 초안을 만들어 승인받는다(§17.3).

---

## 8. Index & Log conventions

### 8.1 index.md
카테고리별 + 한 줄 설명 + wikilink. 예시는 `index.md` 참조.

### 8.2 log.md
Append-only. **가장 최근이 위**. prefix `## [YYYY-MM-DD] <op>`:

```markdown
## [2026-05-18] daily | 2026-05-18
- raw: raw/reports/daily/2026-05-18.md

## [2026-05-18] ingest | "<title>" (paper)
- raw: raw/papers/<slug>.md
- 갱신: [[concepts/...]]
- 신규: [[entities/...]]
```

`grep "^## \[" log.md | head -20` 작동해야 함.

---

## 9. What NOT to do

- ❌ `raw/` 파일 수정·삭제·이름변경 (일일 리포트는 작성 당일까지만 예외)
- ❌ 고립 페이지 생성 (들어오는 링크가 0인 페이지)
- ❌ raw 센서/원본 데이터·고객 PII 위키 저장 (**raw/ 도 포함** — §4.3)
- ❌ raw 에 md 가 아닌 원본 파일(PDF·이미지·jsonl) 커밋 (§4.3)
- ❌ 외부 도구(Notion 등) 페이지 통째 복사 (합성·추출만 허용)
- ❌ `brain/`·개인 회고를 전사 wiki 로 올리기 (§17)
- ❌ 코드를 위키에 통째로 저장 (결정·교훈만)
- ❌ 비-영어 파일명/디렉토리명/slug
- ❌ frontmatter 임의 키 추가 (schema 갱신 후 사용)
- ❌ 같은 질문에 매번 새 답변 생성 (먼저 `syntheses/` 검색)
- ❌ 장황한 preamble — 짧고 직접적으로
- ❌ Mermaid 로 그릴 수 있는 다이어그램을 PNG·draw.io 로 박기
- ❌ 개인·고객 식별 정보 노출 (마스킹·크롭)
- ❌ 이미지만 박고 핵심 결론 텍스트 안 적기 (LLM 이 이미지 안 텍스트 못 읽음)

---

## 10. Style
- **간결함 우선**: 본문 짧게, 정보 밀도 높게. 길면 sub-page 로 분할.
- **인용 명시**: "논문에 따르면…" 대신 "[[raw/papers/xxx]] 에 따르면…"
- **불확실성 표시**: "추정:", "검증 필요:", "아직 결정 안 됨"
- **평어체**: ~한다, ~이다. 존댓말·이모지 X.

---

## 11. Images & Assets

### 11.1 공유용 산출물 — `wiki/assets/reports/`

남에게 건네는 **완성 산출물**(회의록 PDF·리포트 HTML·시안·제안서)을 둔다. 이미지 자산 자리(`charts/`)와 구분한다.

- **위키 페이지와 구분한다.** `wiki/` 의 md 페이지는 *지식*이고, 여기 있는 것은 그 지식으로 만든 *전달물*이다. 산출물을 만들었다고 지식이 남는 게 아니므로, 거기서 굳어진 결정·원칙은 **별도로** wiki 페이지에 합성한다(§7.1·§7.6).
- **파일명**: `YYYY-MM-<slug>.<ext>`, kebab-case 영어. 짝이 있는 문서는 접미사로 구분한다(`-minutes`·`-transcript`).
- **자기완결**: HTML 이면 외부 스크립트·CDN 의존 없이 단일 파일로 열려야 한다.
- **마스킹은 더 엄격하게**(§9). 위키 밖으로 나가는 물건이므로 가격·계약액·급여·인사 사정·고객 식별 정보는 뺀다. 확정되지 않은 값은 **자리 표시임을 문서 안에 명시**한다 — 예시 숫자가 실적으로 읽히면 안 된다.
- **log.md 에 `asset` 항목으로 남긴다**(§8.2). 게시본 URL 이 있으면 함께 적는다.
- 오래된 시안은 지워도 된다. raw 가 아니므로 immutable 이 아니다.

### 11.2 기본 룰

- **파일명**: kebab-case 영어, 날짜·버전 포함. 비-영어·공백·특수문자 금지.
- **포맷**: 다이어그램 SVG 우선(git diff 가능), 사진·스크린샷 PNG(1MB 초과 시 압축). 100MB 초과 금지.
- **Mermaid 우선**: 아키텍처·데이터플로우·state machine·sequence·의사결정 흐름은 Mermaid. 예외(PNG/SVG): 회로도·heatmap·scatter·정밀 도면·사진.
- **개인정보**: 식별 정보 마스킹·크롭.
- **Alt text + 핵심 결론 텍스트 필수**: LLM 은 이미지 안 텍스트 못 읽음.
- **상대 경로 사용**: 절대 경로 금지.
- **실험 결과 vs 마일스톤**: 모든 run·metric 은 실험 추적 도구(MLflow 등)에. 위키엔 운영 모델 교체·방법론 변경 근거·6개월 후 참조 가치 있는 마일스톤만.

---

## 12. Commands

```bash
# 최근 활동 스캔 (최근이 위)
grep "^## \[" log.md | head -20
# 위키 전체 키워드 검색
grep -ri <keyword> wiki/
# 일일 리포트만 검색
grep -ri <keyword> raw/reports/daily/
# 커밋되면 안 되는 게 raw 에 들어왔는지 확인 (md 만 잡혀야 정상)
git status --short raw/

# 슬랙 공용 보관함(NAS) — 공개 채널 읽기 (§7.7)
python tools/slack-ingest/nas_slack.py --check              # 연결·채널·마지막 갱신
python tools/slack-ingest/nas_slack.py --pending --stats    # 지식화 대기 분량
python tools/slack-ingest/nas_slack.py --mark               # 지식화 끝 — 본 데까지 커서 전진

# 자격 증명 커밋 차단 훅 (계정·비밀번호·키, §7.7)
powershell -File tools/install-secret-hook.ps1            # 등록
powershell -File tools/install-secret-hook.ps1 -Status    # 상태
python tools/slack-ingest/fetch_slack.py --mask-existing  # 이미 쌓인 Slack 원문에서 값 지우기

# 세션 digest — 마지막 /log 이후 전 레포에서 한 일 (§7.11)
python tools/session-digest.py --since-file .log-cursor
python tools/session-digest.py --since-hours 24
python tools/session-digest.py --day 2026-08-14          # 특정 하루만

# 세션 transcript 미러
powershell -File tools/sync-sessions.ps1

# 매시간 무인 로그 적재 (작업 스케줄러)
powershell -File tools/install-hourly-log.ps1            # 등록 (매 정각)
powershell -File tools/install-hourly-log.ps1 -Status    # 상태·최근 실행 로그
powershell -File tools/install-hourly-log.ps1 -Remove    # 해제

# 과거 일일 리포트 사후 복원 (세션 기록에서 — 사실만, 회고는 복원 안 함)
powershell -File tools/backfill-daily.ps1 -From 2026-07-07 -To 2026-08-17 -DryRun
```

PowerShell 에서는 `grep` 대신 `Select-String` 사용 가능.

---

## 13. Using this wiki from code repos

위키가 워크스페이스 루트에 있고 코드 레포들과 형제로 두면, 워크스페이스 메모리(`CLAUDE.local.md`)에 위키 경로를 안내해 어느 repo 에서 작업해도 컨텍스트가 붙게 할 수 있다. 개별 repo 의 `CLAUDE.md` 에 위키 참조를 추가하는 방법도 있다.

**경계**: 코드 repo 에서는 **wiki 파일을 직접 수정하지 않는다**. wiki 변경은 wiki repo 에서 별도 작업. 코드 repo 쪽으로 link 추가는 OK. `/repo-ingest` 대상 레포는 read-only.

---

## 14. Evolution — 자율적 업그레이드 (상시)

이 위키는 **스스로 나아지는 것을 지향한다.** 사용자가 불편을 알아채고 지적할 때까지 기다리지 않는다 — AI 가 마찰을 먼저 감지해 고치거나 제안한다. 위키가 정체되는 가장 흔한 이유는 규칙이 틀려서가 아니라 **틀린 걸 아무도 안 고쳐서**다.

### 14.1 마찰 신호 (감지하면 놓치지 않는다)

| 신호 | 뜻 |
|---|---|
| 같은 교정을 **2회 이상** 받음 | 룰이 없거나 틀렸다 |
| 같은 절차를 손으로 **3회 이상** 반복 | 커맨드가 될 때가 됐다 |
| 문서가 실제와 다름 (없는 경로·죽은 툴·바뀐 정책) | 즉시 고칠 것 |
| 커맨드의 특정 단계를 매번 건너뜀 | 그 단계가 현실과 안 맞는다 |
| 위키에 넣기 애매한 게 반복 등장 | page-type·디렉토리가 부족하다 |

### 14.2 자율 등급 — 무엇을 스스로 해도 되나

| 등급 | 범위 | 행동 |
|---|---|---|
| **자율 수정 OK** | 오타, 깨진 wikilink, 죽은 경로·파일명, 문서 ↔ 실제 불일치, index·log 누락 보정 | 고치고 **한 줄 보고**. 허락을 묻느라 멈추지 않는다 |
| **제안 후 승인** | 룰 신설·삭제, 커맨드 절차 변경, 새 커맨드·page-type, 디렉토리 구조 변경 | 근거(어떤 마찰이 몇 번)와 함께 제안. 승인 후 반영 |
| **자율 금지** | 경계 정책(§2·§17), PII·마스킹 규칙(§9), 승인 게이트 자체 | 절대 임의 완화 금지. 느슨하게 만드는 방향은 항상 승인 필요 |

### 14.3 과적합 금지

**1회성 교정을 일반 룰로 만들지 않는다.** 그 세션에서만 맞았던 지시를 schema 에 박으면 CLAUDE.md 가 잡음이 되고, 잡음이 쌓이면 아무도 안 읽는다. 애매하면 룰로 승격하지 말고 관찰만 누적해 뒀다가 **2회째에 승격**한다.

규칙을 **더하는 것만큼 빼는 것도** 진화다. 안 지켜지는 룰, 죽은 절차는 지운다.

### 14.4 반영·환류

- 변경 시 commit message 에 **왜 바꾸는지** 명시 — 나중의 내가 되돌릴지 판단할 근거다.
- 이 repo 는 템플릿에서 만든 것이다. 개선이 **나만의 사정이 아니라 일반적**이면 템플릿에도 제안한다 — 다음 사람이 같은 마찰을 안 겪는다.
- 반대로 템플릿이 좋아지면 `/template-update` 로 받아 온다(§14.5).
- `/session-retro` 가 이 절의 정기 실행판이다(§7.10). 상시 감지 + 주기 회고 두 축으로 돈다.

### 14.5 템플릿 새 판 받기

이 위키는 템플릿(`bodit-inc/llm-wiki-template`)에서 만들었다. 템플릿이 좋아지면 **명령 하나로** 받아 온다.

- `/template-update` — 바뀐 것과 **사람이 할 일**(CHANGELOG)을 보여 주고, 승인받아 파일을 받는다. 상세는 `UPDATE.md`.
- 내가 안 고친 파일은 새 판으로 바뀌고, 내가 고친 파일(`CLAUDE.md` 포함)은 **3방향으로 합친다**. 합치지 못한 것만 대화로 함께 합친다.
- **내 기록은 건드리지 않는다**: `me.md`·`brain/`·`raw/`·`wiki/`·`index.md`·`log.md`·`channels.json`·`.env`. 규칙은 `tools/template-sync-rules.txt`.
- `/morning` 이 하루 한 번 새 판이 있는지 보고 한 줄로 알린다.
- **템플릿을 다시 복사하지 않는다** — 그동안 쌓은 기록이 사라진다.

---

## 15. Task board — 개인 태스크 관리

일정 관리·우선순위는 사람이 약한 부분을 AI 가 보완하는 핵심 장치다. **개인 태스크를 위키에서** 관리한다.

- **단일 보드**: `wiki/tasks/board.md` (`type: task-board`). 여러 파일로 쪼개지 않는다.
- **섹션**: 📥 Inbox / 👀 확인 필요 / 🔥 우선(이번 주) / 📋 진행 중 / ⏳ 대기(blocked) / ✅ 최근 완료.
- **라인 포맷**: `- [ ] <할 일> · src:<출처> · @담당 · due:YYYY-MM-DD · note:한줄`. GitHub 으로 옮긴 줄은 끝에 `· gh:<owner/repo#n>` 을 붙인다.
- **이 보드에 두는 일**: "이 일이 늦어지면 나 말고 누가 불편해지는가?" 에 **나만 불편하다**고 답하는 일이다. 공유 할 일은 GitHub issue 가 원본이다(§17.3).
- **GitHub 과의 관계**: `gh:` 가 붙은 줄은 상태의 원본이 GitHub 이므로 체크박스를 따로 관리하지 않는다. 나에게 배정된 GitHub 이슈는 보드에 옮겨 적지 않는다. `/morning` 이 `tools/company-wiki.py task-list --mine` 으로 읽어 하루 계획에 넣는다.
- **유입**: `/slack-ingest`·`/eod`·회의·대화. LLM 은 액션 아이템이 굳으면 **보드 반영을 제안**(남발 금지).
- **완료**: `- [x]` + 완료일 → ✅ 로 이동. 오래된 완료는 주기적으로 정리.
- **마스킹**: 보드도 위키이므로 개인정보·급여·계약액·고객 식별 정보는 마스킹(§9).
- report 와 달리 **immutable 아님** — 계속 편집하는 살아있는 보드.

### 15.1 역할별 운용 — `me.md` 의 `역할 유형` 을 따른다

**태스크를 어디까지 책임지느냐가 역할에 따라 다르다.** `me.md` L2 의 `역할 유형`(`lead` / `member`)을 읽어 `/morning`·`/eod` 가 아래로 갈린다. 값이 없으면 `member` 로 본다.

> ⚠️ **어제 팀 흐름은 역할과 무관하게 모두 본다.** 동료가 어제 무엇을 했는지는 직급이 아니라 협업의 문제다. `/morning` 이 읽는 것은 전사 위키 `raw/reports/daily/` 의 **공유본**, 즉 각자 민감분을 걷어내고 올린 기록이다. 역할이 가르는 것은 *보느냐 마느냐* 가 아니라 거기서 **무엇을 더 챙기느냐** 다.

| | **member** (팀원) | **lead** (파트장·팀장·리드) |
|---|---|---|
| 책임 범위 | **내 태스크**: 개인 보드 + 나에게 배정된 GitHub 이슈 | 위 전부 + **내 파트 이슈의 진행 상황**(Bodit Tasks 보드) |
| 어제 팀 흐름 | **본다.** 사람별 한 일 · 내 일과 닿는 지점 · 내가 답해야 상대가 움직이는 것 | 위에 더해 **막힌 사람 · 기록이 며칠째 빈 사람 · 팀 방향과 어긋나는 것** |
| `/morning` 에서 | 내 보드 🔥·📋·`due:` 임박 + 나에게 배정된 이슈(`task-list --mine`) | 추가로 팀의 막힘을 **내 보드 🔥 로** 끌어온다 |
| `/eod` 에서 | 오늘 완료·신규를 보드에 반영 → **공유 할 일만** GitHub issue 초안으로 만들어 승인받는다 | 추가로 내 파트 이슈의 진행·정체를 정리하고(`task-list --part`), 내가 막고 있는 건을 먼저 처리 |
| 판단의 중심 | *오늘 내가 무엇을 끝냈고, 팀의 어떤 움직임이 내 일에 닿나* | *팀이 무엇에 막혀 있고 내가 무엇을 풀어줘야 하나* |

**두 방향이 유기적으로 붙는 지점**은 다음 셋이다. 커맨드는 이 셋을 매번 확인한다.

1. **개인 보드 → GitHub** (`/eod`): 개인 보드에서 굳은 것 중 **공유 할 일만** GitHub issue 로 올린다(`task-new`, §17.3). 미리보기를 보여 주고 승인받은 뒤에만 만든다. 올린 줄에는 `gh:<owner/repo#n>` 을 붙인다. 개인 습관·개인 프로젝트는 보드에만 남긴다.
2. **GitHub → 하루 계획** (`/morning`): 나에게 배정된 이슈를 `task-list --mine` 으로 읽어 오늘 할 일에 넣는다. 보드에 옮겨 적지 않고 상태는 GitHub 에서 바꾼다. GitHub 에만 있는 일은 이렇게 읽어 오지 않으면 **오늘 안 보게 되므로 반드시 읽는다.**
3. **팀 흐름 → 내 할 일** (`/morning`, 모두): 어제 팀 기록에서 **내가 답해야 상대가 움직이는 것**이 나오면 오늘 할 일의 🔴 로 올린다. 남이 나를 기다리며 멈춰 있는 일은 내 일보다 먼저다. 이걸 놓치면 팀 전체가 하루씩 밀린다.
   - **`lead` 는 여기서 한 겹 더 본다**: 팀원이 스스로 못 푸는 **막힘** 중 내 결정·방향이 필요한 건을 **내 보드의 🔥 로** 옮긴다.

- **중복 관리 금지**: 같은 일을 개인 보드와 GitHub 에 각각 다른 상태로 두지 않는다. `gh:` 가 붙은 줄은 GitHub 이 상태의 원본이고, 붙지 않은 줄은 개인 보드가 원본이다. 보드에는 `src:` 로 어디서 흘러온 일인지 남긴다.
- **전사 미연결이어도 전부 동작한다.** 전사 단계만 건너뛰고 개인 보드는 그대로 쓴다(§17.2).

---

## 16. Brain 감지 — 생각 흘려보내기 방지 (상시)

"놓치는 일이 없도록" 을 2nd brain 에 적용한 장치. ingest·작업은 자꾸 3rd brain(사실 합성)으로만 끝나 **본인 생각이 안 남는 누락**이 반복된다 — 이를 막는다.

- **상시 발동**: 위키 관련 작업 중 **본인의 생각**(판단·가설·반론·교훈·주저·열린 질문·방향 의지)이 드러나면, 그 단계 끝에 짧게 "이거 brain note 로 남길까요?" 한 줄 제안한다.
- 판단 기준·제안 형식은 `.claude/commands/brain-check.md`(=`/brain-check`)에. 작성은 `/brain` 소관.
- **경계**: 외부 사실·스펙·남의 결정 → wiki. 확정 ADR → decisions. 액션 아이템 → 보드. 일회성 잡담 → 안 남김.
- **남발 금지**: 작업당 1~2개 상한, 같은 생각 반복 제안 금지.
- **대신 쓰지 않는다**: 공명·확장(본인 생각 칸)을 AI 가 채워 완성하지 않는다. 제안만 하고 작성은 `/brain` 대화로.

---

## 17. 전사 LLM wiki 연계

회사에는 **전사 LLM wiki** 가 따로 있다(공용 지식·일일 리포트 공유본). 슬랙 공개 채널은 사내 NAS 의 공용 보관함에 따로 모인다(§7.7). 개인은 **여기서만 작업**하고, 전사 wiki 는 ① 참조하고 ② 공유 가치가 생기면 승격한다. **자동 동기화는 없다.**
전사 할 일은 위키가 아니라 **GitHub issue** 가 원본이다. 조직 보드 **Bodit Tasks**(https://github.com/orgs/bodit-inc/projects/7)가 여러 저장소의 issue 를 모아 보여 준다.

### 17.1 경계 판정
> **다른 파트 사람이 알아야 하나?** — Yes → 전사 wiki / No → 여기.

| 전사로 간다 | 여기 남는다 |
|---|---|
| 업무 진행·산출물(공유 가능분) | 개인 회고·`brain/` 전부 |
| 배운점·교훈 중 남에게 쓸모 있는 것 | 아직 안 굳은 생각·가설 |
| 회사 공용 결정·용어·프로젝트 지식 | 개인 태스크 보드·개인 학습 메모 |
| 공유 할 일(GitHub issue) | 면담·1:1·타인 개인사·민감한 판단 |

할 일은 판정 질문이 따로 있다. "이 일이 늦어지면 나 말고 누가 불편해지는가?" 로 가른다(§17.3).

**절대 안 넘긴다**: `brain/` 노트, 개인 회고, 인사·급여·계약액, 고객 식별 정보, raw 원문 통째.

### 17.2 접근 방법 — MCP 커넥터와 GitHub

사내 질의는 **MCP 커넥터**로 한다. 사내 표준은 **Jarvis**(`https://jarvis-mcp.bodit-lab.co/mcp`, Google @bodit.co 로그인)이다. 일일 리포트와 할 일은 `tools/company-wiki.py` 가 GitHub 으로 다룬다. 세팅은 `SETUP.md` §2.

| 툴 | 하는 일 | 성격 |
|---|---|---|
| `jarvis_ask` | 사내 위키·정책·개념·축산 운영 DB 를 **자연어로 질의** | 읽기. 파일 탐색이 아니라 **질문**이다 |
| `tools/company-wiki.py daily-put` · `daily-get` | 내 일일 리포트 공유본 올리기 · 그날 팀 리포트 읽기 | 쓰기·읽기 |
| `tools/company-wiki.py task-new` · `task-list` · `task-update` · `task-close` | 할 일을 GitHub issue 로 만들고, Bodit Tasks 보드에서 읽고 바꾸고 닫는다 | 생성·배정·종료는 **사람 승인 뒤 `--yes`** |

- `jarvis_eod_save`·`jarvis_team_eod`·`jarvis_task_create` 는 쓰지 않는다.
- 응답의 농장·개체·PII 는 자동 마스킹되고 **내 권한으로 스코프**된다. 반대로 **내가 보내는 건 내가 마스킹한다.**
- **일일 리포트는 전사 위키(GitHub 저장소)에 올린다.** `tools/company-wiki.py` 가 **저장소를 내려받지 않고** GitHub API 로 읽고 쓴다. 전제는 `gh auth login` 과 전사 위키 `people/<내이름>.md` 의 `github:` 한 줄이다.
  - 올리기 `daily-put` → `raw/reports/daily/<나>/YYYY-MM-DD.md` 에 main 으로 바로(내 폴더라 PR 불필요) · 읽기 `daily-get --date` → 그날 팀 전체 + 안 쓴 사람
- **지식 승격**(decision·concept·entity)은 전사 위키에 **PR + 리뷰어 지정**으로 올린다(전사 `docs/guide/contributing.md`). 도구는 `tools/company-wiki.py wiki-pr`(브랜치·파일·활동 기록·PR·리뷰어를 한 번에, `--yes` 없으면 미리보기)이고, 내 회의록·논문 원문은 `mine-put` 으로 main 에 바로 올린다. 실행은 `/promote`. 오늘 못 올린 것은 `wiki/tasks/board.md` 에 `- [ ] 전사 승격 대기: <항목> · src:<개인 위키 경로>` 로 남긴다.
- 팀원 EOD 를 인용할 때는 **작성자와 날짜를 반드시 밝힌다**.
- **할 일**: 공유 할 일은 GitHub issue 로 만든다. 어느 저장소에 둘지는 §17.3 에서 가른다.
  - 만들기: `task-new --title --body-file --due --priority --assignee <위키이름 또는 @계정> [--repo] [--part] [--status] [--parent]`. **`--yes` 가 없으면 미리보기만 보여 주고 멈춘다.** 미리보기를 사람에게 보여 주고 승인받은 뒤에만 `--yes` 를 붙인다. 민감 정보 기계 검사와 같은 제목 중복 차단을 거친다.
  - 본문은 세 절로 쓴다: 무엇을, 왜 / 끝났다고 보는 기준 / 출처.
  - **남에게 배정할 수 있다.** `--assignee` 에 위키 이름이나 `@계정` 을 넣는다. issue 는 만드는 순간 담당자에게 알림 메일이 가서 되돌릴 수 없으므로 승인 없이 만들지 않는다.
  - 조회 `task-list [--mine] [--part] [--status] [--due-within N] [--assignee]` · 변경 `task-update <번호|owner/repo#n|주소> [--status --part --due --priority]` · 종료 `task-close <ref> [--not-planned] [--comment]`.
  - **승인 없이 하는 것**: 조회, 내가 담당인 이슈의 상태·마감 변경. **승인 뒤에만 하는 것**: 생성·배정·종료, 남이 담당인 이슈의 변경(`--yes`).
  - 보드 필드: Status(Idea·Inbox·Backlog·This week·In progress·Blocked·Done), Part(ops·analysis·embedded·frontend·backend·org), Target date(마감), Priority(Urgent·High·Medium·Low). 큰 일은 하위 이슈(sub-issue)로 나눈다(`--parent`).
  - 전제: GitHub 토큰에 `project` 권한이 있어야 한다. `gh auth refresh -h github.com -s project` 를 한 번 실행한다(`SETUP.md` §2-1).
- `jarvis_ask` 는 검색이 아니라 질의다 — "X 파일 보여줘" 가 아니라 "X 에 대해 우리가 뭘 정했나" 로 묻는다.
- **미연결이면**(인증 안 됨·툴 안 보임·`gh` 권한 없음) 해당 단계를 **건너뛰고 한 줄 고지**한다. 개인 위키 기능은 전부 정상 동작한다. 없는 걸 지어내거나 다른 경로로 우회 기록하지 않는다.

### 17.3 승격 절차

> **필수 업데이트 원칙**: **일일 리포트(`/eod`)와 공유 할 일은 전사 반영이 기본값이다** — 선택 사항이 아니다. 안 올리는 쪽이 예외이고, 그때는 **이유를 한 줄로 남긴다**. 조용히 건너뛰면 전사에 내 일이 안 보인다.
> 단, **필수인 것은 "올리는 행위"이지 "전부 올리는 것"이 아니다.** 무엇을 걷어냈는지 밝히는 한 마스킹·선별은 그대로 유효하다(§17.2 절대 안 넘기는 것 우선).

**경로별로 다르다:**

| 종류 | 경로 |
|---|---|
| 일일 업무·배운점(EOD) | `tools/company-wiki.py daily-put` → 전사 위키 `raw/reports/daily/<나>/` — 원본은 개인 위키에 남고, **민감 제외 공유본**만 올라간다 |
| 공유 할 일(늦어지면 남이 불편해지는 일) | `tools/company-wiki.py task-new` 로 GitHub issue 를 만든다. 미리보기 → 사람 승인 → `--yes`. 남에게 배정할 수 있다. 조회는 `task-list` |
| 지식(decision·concept·entity) | 전사 위키에 **PR + 리뷰어 지정**(전사 `docs/guide/contributing.md`). `wiki-pr` 로 올린다(미리보기 → 승인 → `--yes`). 내 회의록·논문 원문은 `mine-put` 으로 main 에 바로 |

- **원본은 여기, 공유본은 전사.** 일일 리포트를 두 번 쓰는 게 아니라, 개인 위키 원본에서 민감분을 걷어낸 것이 전사로 간다. **무엇을 걷어냈는지 사용자에게 보여주고** 올린다.
- **상시 제안**: 작업(`/eod`·ingest·대화) 중 회사 공용 가치가 익으면 "이거 전사 wiki 로 올릴까요?" 한 줄 제안. §16 brain 감지와 동형 — **남발 금지**(작업당 1~2개).
- **합성 재작성**: 개인 위키 문장을 복사하지 않는다. 읽는 사람이 다르므로 **다시 쓴다** — 내 맥락·주관·회고를 걷어내고 사실·결정·교훈만.
- **마스킹은 더 엄격하게**: 전사 규칙이 개인 규칙보다 강하다. 개인 위키에서 통과한 것도 전사에서 다시 검열한다.
- **md 로**: 전사 wiki 는 md 만 받는다. 첨부·바이너리는 링크나 stub 으로.
- 실행은 `/promote`(상세 `.claude/commands/promote.md`). `/eod` 는 하루 단위로 이 제안을 포함한다.
- 승격한 것은 `log.md` 에 `promote` 항목으로 남겨 **뭘 이미 올렸는지** 추적한다(중복 방지).

**할 일을 어디에 두나.** "이 일이 늦어지면 나 말고 누가 불편해지는가?" 로 가른다.

| 답 | 이름 | 두는 곳 |
|---|---|---|
| 나만 불편하다 | **개인 할 일** | 개인 보드 `wiki/tasks/board.md`. 전사에 올리지 않는다 |
| 남이 불편하고, 코드 PR 로 끝난다 | **공유 할 일** | 그 코드 저장소의 issue(`task-new --repo <owner/repo>`) |
| 남이 불편하고, 코드와 상관없다 | **공유 할 일** | `bodit-inc/bodit-ops-tasks` 의 issue(`task-new` 기본값) |

- 다음 중 하나라도 해당하면 "남이 불편하다" 로 본다: 담당이 다른 사람이다 · 남과 약속한 마감이 있다 · 결과를 다른 파트나 외부가 받는다 · 누군가 이 일을 기다린다 · 코드 PR 로 끝난다.
- 생성·배정·종료는 **사람 승인 뒤에만** 한다. issue 는 만드는 순간 담당자에게 알림 메일이 가서 되돌릴 수 없다. 조회와 내 이슈의 상태·마감 변경은 승인 없이 한다.
- 개인 보드의 줄을 GitHub 으로 옮기면 그 줄에 `gh:<owner/repo#n>` 을 붙인다(§15).
