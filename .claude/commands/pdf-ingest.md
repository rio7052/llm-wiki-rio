---
description: 외부 PDF(다운로드 등)를 raw 로 가져와 대화하며 개인지식화(wiki 합성)
argument-hint: (선택) PDF 경로/파일명. 비우면 Downloads 최신 PDF 후보 제시. 예 "데이터 리뷰", "D:\\x\\report.pdf"
---

`/pdf-ingest` — 외부에서 받은 PDF 를 `raw/` 에 보관하고 사용자와 **대화하며** 위키로 합성한다. 원본 PDF 는 커밋되지 않고(§4.3 md-only), **읽어서 md 로 변환한 발췌**가 `raw/` 에 남으며, 위키엔 **마스킹·합성**된 지식만 올린다. wiki schema §7.1(ingest)·§4(디렉토리)·§3(언어)·§9(PII) 를 따른다.

> 핵심: 원문을 통째로 옮기지 않는다 — **신호 있는 핵심만** 합성(§7.1·§11). raw 는 immutable·**md only**(§4.3).
> PDF 는 Read 툴이 페이지 단위로 바로 읽는다 — 별도 변환 불필요. (웹 URL 은 defuddle→`raw/articles/` 경로, §7.1.)

## 1. 대상 PDF 확정

`$ARGUMENTS` 해석:
- **절대경로/파일명** → 그 파일. 파일명만 주면 Downloads·CWD 에서 매칭.
- **비움** → `Get-ChildItem "$env:USERPROFILE\Downloads\*.pdf" | Sort LastWriteTime -Desc` 로 최근 목록을 보이고, **도메인 관련(논문·리포트·가이드)** 후보를 위로 추려 1개 고르게 한다. 이력서·청약·영수증 등 사적 파일은 후보에서 내린다.

확정 못 하면 묻고 멈춘다.

## 2. 읽기 + 분류

- Read 툴로 PDF 전체를 읽는다. **장황한 페이지별 요약 금지.**
- **type·목적지** 판단(§4.1):
  - 학술 논문 → `raw/papers/`
  - 회의록·보고서·가이드·캡처 메모 → `raw/notes/`
  - (웹 아티클이면 이 커맨드 밖 — defuddle→`raw/articles/`)
- **raw 에 md 로 기록**: PDF 를 읽고 **핵심 발췌·구조를 md 로 정리해** `raw/<papers|notes>/YYYY-MM-DD-<slug>.md` 로 저장한다. kebab-case 영어 파일명, 비-영어 금지(§4.2).
  - **원본 PDF 는 커밋되지 않는다**(§4.3 md-only). 원본을 보관하려면 위키 밖 본인 폴더에 두고, md 상단에 `원본: <로컬 경로 또는 출처 URL>` 한 줄만 남긴다.
  - 발췌 단계에서 이미 **마스킹**(§9) 한다 — raw 도 git 에 올라간다.

## 3. 사용자와 대화 (짧게)

원문을 추려 **압축 제시**하고 분류를 받는다:
- **takeaway 3~5개** 1줄씩 → "위키에 반영할 핵심" 확정.
- **어디로 합성할지** 같이 정한다:
  - 사실/개념/결정 → `entities/` · `concepts/` · `decisions/`
  - 도메인 지식 다발이면 → `domains/<area>/` hub(overview) + 하위 페이지
  - 프로젝트 산출/결정 → 해당 `projects/` 갱신
  - 애매하거나 '내 생각'이면 → brain seed 로 가볍게(`/brain`)
- **PII 경계**(§9) 도 이때 합의: 개인 실명·건강·급여·계약액·투자 사적정보·고객 식별 → 제거/역할화.

## 4. 합성 (확정분만)

- **소스 자체 페이지 안 만듦** — raw 에 있음. 위키엔 합성 결과만.
- 영향받는 기존 페이지 **갱신**(새 사실·모순 플래그), `last_updated` 갱신 + `sources` +1.
- 새 페이지는 §5 page format(frontmatter+본문, 평어체 §3) 준수.
- **고립 금지**(§6): 새 페이지로 향하는 들어오는 링크를 관련 페이지 1~3개에 추가. hub 구조면 hub↔하위 상호링크.
- Sources 에 `[[raw/notes/...]]` / `[[raw/papers/...]]` 명시.

## 5. 마무리

- `index.md` 신규 페이지 반영.
- `log.md` append: `## [YYYY-MM-DD] ingest | "<title>" (pdf)` + 신규/갱신 wikilink 줄(§8.2).
- 변경 commit 제안(요청 시). `raw/**/*.md` 도 함께 커밋된다 — 마스킹 확인 후 stage.
- 채팅 한 줄 보고: raw 보관 위치 · 신규 K개 · 갱신 N개 · 미반영으로 남긴 것.

## 톤·안전
- 사용자와의 대화는 **존댓말**. 위키 본문은 **평어체**.
- `raw/` 는 immutable·md only. 위키 페이지엔 마스킹·합성만.
- 한 번에 한 PDF. 배치는 명시 요청 시만.
- 사적·민감 문서(이력서·계약·개인 재무 등)는 ingest 전 한 번 더 확인하고, 애매하면 멈춰 묻는다.
