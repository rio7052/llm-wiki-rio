---
description: Claude Code 세션 회고 — 전 레포 대화 기록에서 교정 패턴·반복 워크플로우·흘러간 지식을 추출해 룰·skill·위키로 승격
argument-hint: (선택) --since <날짜> 또는 repo명. 비우면 log.md 커서 이후 전체 세션
---

`/session-retro` — 모든 레포에서 Claude Code 와 나눈 세션 transcript(`~/.claude/projects/<slug>/*.jsonl`)를 위키에서 직접 읽어(pull) 회고·지식화한다. `/repo-ingest` 와 같은 패턴: read-only 소스 + `log.md` 커서 + 대화형 큐레이션. wiki schema §7.10·§9(PII)·§16(brain 감지)를 따른다. *(개발자용 — 코드 레포에서 Claude Code 를 쓰는 사람만 필요하다.)*

> 핵심 목적: ① 같은 실수 반복 방지 — 교정을 룰로 승격 ② 반복 업무의 skill/agent 화 ③ 대화에만 남고 흘러간 결정·지식·생각 회수.
> **전자동 룰화 금지**: 한 세션에서만 유효한 교정을 일반 룰로 과적합하면 CLAUDE.md 가 잡음이 된다. 후보를 제시하고 **사용자가 큐레이션**한다.

## 1. 동기화 + 범위 확정

1. **transcript 미러 먼저**: `powershell -File tools/sync-sessions.ps1` 실행 → `raw/sessions/<project-slug>/<session-id>.jsonl` 갱신. 이후 모든 읽기는 `raw/sessions/` 기준 (원본 `~/.claude/projects/` 는 건드리지 않음).
2. **커서**: `log.md` 의 마지막 `session-retro` 항목에 기록된 **처리 시각(ISO)** 이후에 수정된 세션만 대상. 커서 없으면(첫 실행) `--since` 를 묻거나 최근 1주 제안.
3. `$ARGUMENTS`: `--since <날짜>` 수동 지정 / repo명(slug 부분 매칭)으로 한 레포만.
4. **현재 진행 중인 세션(이 회고 세션 자신)은 제외.** 파일 크기 50KB 미만의 잡담·단발 세션은 목록만 보여주고 스킵 여부 확인.
5. 대상 목록(레포별 세션 수·크기) 1줄 요약 → 사용자 확인 후 진행.

## 2. 세션별 digest — 서브에이전트 fan-out

transcript 는 세션당 수백 KB~수십 MB 라 메인 컨텍스트에 다 못 싣는다. **세션당 Explore/general-purpose 서브에이전트 1개**로 digest 를 뽑는다 (독립적이므로 병렬 실행).

각 digest 에이전트에게 시킬 것 — assistant 메시지·툴 결과는 훑고 **user 메시지(사용자 발화)를 정독**:
- **교정 순간**: 사용자가 Claude 를 고친 지점 ("아니", "그게 아니라", 재작업·되돌리기 지시, 같은 지시 반복). 무엇을 어떻게 고쳤는지 + **세션 한정인지 일반화 가능한지** 판정.
- **반복 워크플로우**: 수동으로 여러 번 밟은 절차 (같은 명령 시퀀스, 같은 유형의 요청).
- **굳은 결정·지식**: 대화에서 확정됐는데 위키/코드 문서에 남지 않은 결정·사실.
- **사용자의 생각**: 가설·판단·반론·열린 질문 (brain 후보, §16 기준).
- **놓친 액션**: "나중에", "해야겠다" 하고 보드에 안 올라간 것.
- 세션 메타: 레포·날짜·주제 1줄.

거대 세션(10MB+)은 에이전트에게 파일을 구간(offset) 나눠 읽게 지시.

## 3. 종합 — 5버킷 + 사용자 큐레이션 (이 커맨드의 핵심)

digest 들을 모아 **세션 경계를 가로질러** 집계한다. 같은 교정·같은 워크플로우가 여러 세션에서 반복되면 그게 가장 강한 신호다.

| 버킷 | 승격 기준 | 목적지 |
|------|----------|--------|
| ① 교정 패턴 | **2회 이상 반복**되거나 명백히 일반적 | 해당 repo CLAUDE.md 룰 · wiki schema(이 repo CLAUDE.md) · 해당 skill 수정 · auto-memory(feedback) |
| ② 반복 워크플로우 | **3회 이상** 또는 사용자가 원함 | 새 slash command/skill 제안 (해당 repo `.claude/commands/`) · agent 정의 |
| ③ 흘러간 결정·지식 | 굳어졌고 재참조 가치 | `wiki/decisions/` · entities/concepts · projects 갱신 (§7.1) |
| ④ brain 후보 | 사용자 머릿속에서 나온 것 (§16 기준) | `/brain` 제안 (작업당 1~2개 상한) |
| ⑤ 놓친 태스크 | 아직 유효한 액션 | [[tasks/board]] |

- 버킷별 후보를 근거(어느 세션·몇 회)와 함께 **짧게** 제시 → 사용자가 채택/기각.
- 1회성 교정은 기본 기각 (목록엔 보여주되 승격 안 함).
- 반복 확인됐지만 아직 룰로 굳히기 이른 것 → [[playbooks/claude-collaboration]] 에 관찰로 누적 (2단계 승격: 관찰 → 룰).

## 4. 반영 (확정분만)

- **transcript 원문은 위키에 복사하지 않는다** — raw/sessions/ 에 이미 있음. 위키엔 합성만, Sources 에 `[[raw/sessions/<slug>/<session-id>]]` + 날짜 명시.
- [[playbooks/claude-collaboration]] (living page, §5.2 playbook) 갱신 — 회고마다 흩뿌리지 말고 이 한 장에 누적.
- 다른 코드 repo 의 CLAUDE.md·commands 수정이 채택되면: **그 repo 파일 수정은 OK** (지식 파일이지 코드가 아님 — §13 코드 read-only 경계의 의도적 예외). 단 수정만 하고 **그 repo 에서 commit 은 사용자에게 맡기거나 확인 후**.
- **PII(§9)**: transcript 에는 Slack 원문·귀표번호·토큰이 섞여 있을 수 있다. 위키 승격 시 마스킹 필수. `raw/sessions/*.jsonl` 은 md 가 아니라 커밋되지 않는다(§4.3) — 그래도 승격물에는 마스킹 필수.

## 5. 마무리

- `index.md` 신규 페이지 반영, 태스크 보드 유입.
- `log.md` append: `## [YYYY-MM-DD] session-retro | <기간> <N>세션/<M>레포` + 채택 항목 wikilink + **새 커서 시각(ISO) 기록** (다음 실행이 읽음).
- 위키 변경분만 선별 stage·commit 제안.
- 채팅 한 줄 보고: 본 세션 수 · 룰 승격 K · skill 후보 N · 위키 신규/갱신 · 새 커서.

## 톤·안전

- 사용자와의 대화는 **존댓말**, 위키 본문은 **평어체**.
- `~/.claude/projects/` 원본은 read-only. 산출은 위키·`.claude/commands/`·memory 에만.
- 주 1회 권장 (매일은 /eod 와 겹치고, 월간은 세션이 너무 쌓임). `/monthly` 직전 실행하면 월간 재료로도 쓰임.
