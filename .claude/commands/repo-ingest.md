---
description: 코드 레포의 새 작업을 위키에서 직접 pull 해 대화하며 개인지식화
argument-hint: (선택) topic 또는 repo명 [--branch origin/dev] [--since <hash|날짜>]. 비우면 topic 묻기.
---

`/repo-ingest` — 워크스페이스 형제 코드 레포에서 굳은 **결정·인터페이스 변경·모델 버전·교훈**을 위키로 합성한다. 코드 레포가 ingest 를 제안해주길 기다리지 않고(push), **위키에서 직접 `git log`·`diff`·파일을 읽어 끌어온다(pull)**. wiki schema §7.1(ingest)·§13(코드 repo 경계)·§3(언어)·§9(PII) 를 따른다.

> 핵심: 코드를 통째로 옮기지 않는다 — **결정·교훈·인터페이스만** 합성(§9·§11). 설계/계약 문서(INTERFACE.md 등)는 `raw/notes/` 캡처, 코드 자체는 복사 안 함.
> **경계(§13)**: 대상 레포는 **read-only**. `git log/diff/show`·파일 Read 만. 그 레포 파일을 **수정·커밋하지 않는다** — 산출은 위키/brain 에만.
> ⚙️ 전제: 위키와 코드 레포가 **워크스페이스 루트에 형제로** 있어야 한다(예: `Projects/my-wiki/`, `Projects/<category>/<repo>/`). 본인 레이아웃에 맞게 아래 경로를 조정한다.

## 1. 대상·범위 확정

`$ARGUMENTS` 해석:
- **topic 모드 (기본)** — 자유어거나 비움. 한 주제가 여러 레포에 걸치는 게 흔하므로 **관련 레포를 가로질러** 모은다. 어떤 레포가 관련인지 추론해 사용자에게 확인받는다.
- **single-repo 모드** — 인자가 레포명이면 그 레포만.
- `--branch <ref>` — 비교 기준 브랜치(기본 **`origin/main`**).
- `--since <hash|날짜>` — 시작점 수동 지정.

**범위 잡기**:
1. **항상 `git fetch` 먼저.** 로컬 HEAD·체크아웃 브랜치를 믿지 않는다(구 브랜치면 버전·내용 오인).
2. **커서**: `log.md` 에서 그 레포의 마지막 `repo-ingest` 항목이 남긴 **커밋 해시**를 읽어 `git log <cursor>..<branch>` 범위로 잡는다. 커서 없으면(첫 ingest) `--since` 를 묻거나 최근 N개 제시.
3. 대상 레포 경로는 `../<category>/<repo>` (워크스페이스 루트 직속). 못 찾으면 `find ../*/ -maxdepth 2 -name .git` 로 탐색.

확정 못 하면 묻고 멈춘다.

## 2. shortlist — 노이즈 필터 (이 커맨드의 핵심)

레포 커밋 대부분은 위키 감이 아니다. **지식 감만** 추린다.
- **1차 신호** = 커밋 메시지 + **설계/계약 문서**: `INTERFACE.md`, `*RULE*.md`, `PLAN.md`, `*spec*`, `README`, 버전 bump(setup.py/pyproject), `feat(model)`·`feat(package)` 류.
- **diff 는 shortlist 된 것만** 읽는다(전체 diff 통독 금지). `git show <hash> -- <문서>` 로 설계 문서 본문 우선.
- **합성 감** (올린다): 모델 버전·threshold 변경 · 인터페이스/계약 변경 · 아키텍처 결정 · 운영 룰 · 교훈·함정.
- **스킵**: 순수 리팩터·포맷·주석·dep bump·CI·오타.

## 3. 5버킷 분류 + 대화 (짧게)

shortlist 를 slack-ingest 와 같은 **5버킷**으로 압축 제시: 지식화 후보 / 확인 필요 / 빠뜨린 것 / 태스크 후보 / 방향 신호.
- **takeaway 3~5개** 1줄씩 → "위키 반영 핵심" 확정.
- **목적지** 합의: 결정 → `decisions/` · 도구/패키지/모델 → `entities/` · 개념 → `concepts/` · 프로젝트 진행 → `projects/` 갱신 · '내 생각/가설' → brain seed · 개인 할 일에 해당하는 확인할 것·후속 → [[tasks/board]].
- **다른 사람이 해야 할 일**(파트 간 인터페이스 변경의 후속 등)은 GitHub issue 초안을 만든다: `python tools/company-wiki.py task-new --title ... --body-file ... --assignee <위키 이름>` 으로 미리보기를 보여 주고, 승인을 받은 뒤에만 `--yes` 로 만든다. 코드 PR 로 끝나는 일은 `--repo bodit-inc/<그 저장소>`, 아니면 기본값. 본문 출처에 `<repo>@<hash>` 를 적는다.
- **버전·번호 divergence 같은 혼동 위험**은 "확인 필요"로 명시.
- **PII·경계**(§9): 소 귀표·개체번호 마스킹, NAS 경로·토큰 제거. 농가·업체명은 실명으로 둔다.

## 4. 합성 (확정분만)
- **코드·소스 페이지 안 만듦**. 위키엔 합성 결과만(§7.1).
- 설계/계약 문서는 **복사하지 않는다.** 원본이 코드 저장소에 이력과 함께 있으므로 사본을 두면 원본과 어긋나기만 한다. 판단에 쓴 핵심은 위키 페이지 본문에 합성하고, 출처로 저장소·경로·커밋 해시를 남긴다. 코드도 복사하지 않는다.
- 영향받는 기존 페이지 **갱신**, `last_updated`·`sources` 갱신.
- 새 페이지는 §5 page format(평어체 §3). **고립 금지**(§6).
- Sources 에 **`<repo>@<hash>:<경로>`** 를 명시한다(추적용, 필요하면 GitHub 주소).

## 5. 마무리
- `index.md` 신규 페이지 반영.
- `log.md` append: `## [YYYY-MM-DD] repo-ingest | <repo/topic> <hash범위>` + 신규/갱신 wikilink 줄. **새 커서 해시를 이 항목에 기록**(다음 실행이 읽음).
- 태스크 보드 유입(확인 필요·후속).
- **위키 변경분만 commit 제안**(요청 시) — 대상 코드 레포는 절대 건드리지 않음.
- 채팅 한 줄 보고: 본 범위(hash) · 신규 K개 · 갱신 N개 · 확인 필요로 남긴 것 · 새 커서.

## 톤·안전
- 사용자와의 대화는 **존댓말**, 위키 본문은 **평어체**.
- 대상 레포 read-only(§13). 산출은 위키/brain 에만.
- 한 번에 한 topic/repo. 배치는 명시 요청 시만.
