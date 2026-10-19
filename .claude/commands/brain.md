---
description: brain note(2nd brain) 작성 — 내 생각을 배경·공명·확장·통합·탐색으로 끄집어낸다
argument-hint: <주제 또는 씨앗 문장>
---

`/brain` — 나의 **2nd brain** 에 생각 한 편을 적는다. wiki(3rd brain, 중립 지식)가 아니라 **내 생각·가설·반론**을 담는 레이어다. 규칙은 `brain/README.md`, 포맷은 `brain/TEMPLATE.md`, schema 는 `CLAUDE.md §5.2 brain-note` 참조.

주제/씨앗: **$ARGUMENTS**

## 진행 순서

1. **씨앗 확정.** `$ARGUMENTS` 를 한 문장 핵심 생각(`seed`, triple 지향: `주어 —(관계)→ 목적어`)으로 압축해 사용자에게 확인받는다. 비어 있으면 "무슨 생각을 적을까요?" 한 줄로 묻는다.

2. **연결 후보 수집 (고립 방지).** 작성 전에 위키에서 관련 페이지를 찾는다:
   - `index.md` 와 `wiki/`(특히 `concepts/`·`projects/`·`decisions/`) 를 주제어로 검색.
   - 최근 맥락이 필요하면 `raw/reports/daily/` 최근 며칠, `log.md` 상단도 훑는다.
   - 통합(Integrate)에서 걸 `[[wikilink]]` 후보 2–3개를 미리 확보한다. (최소 1개 — 고립 금지, §6)

3. **5단계로 끄집어낸다.** 한 번에 다 묻지 말고, 사용자의 답이 얇은 칸만 짧게 되묻는다. 내가 채울 수 있는 칸(배경 링크·통합 후보)은 먼저 채워 초안을 보여주고, **공명·확장은 본인 생각**이라 비우거나 잠정 추론에 "검증 필요" 표시.
   - **배경 (Background)** — 무엇이 이 생각을 촉발했나. 출처·계기 링크.
   - **공명 (Resonate)** — 무엇이 *나에게* 꽂혔나, 왜. (남의 요약 금지)
   - **확장 (Amplify)** — 그래서 내 결론·가설 / 반론·의심 / "만약 ___ 라면?"
   - **통합 (Integrate)** — `A —(관계)→ B` triple + `[[wiki/...]]` 링크.
   - **탐색 (Navigate)** — 다음 질문 / 실험 / ingest·decision 후보.

4. **파일 작성.** `brain/<slug>.md` (kebab-case 영어 slug). `brain/TEMPLATE.md` 구조를 따르고 frontmatter 채운다: `type: brain-note`, `seed`, `status`(처음은 보통 `seed` 또는 `growing`), `tags`(lowercase-kebab 최소 1개), `created`·`last_updated`(오늘 날짜).

5. **마무리.**
   - `index.md` 에 brain note 섹션이 있으면 추가.
   - `log.md` 상단에 `## [YYYY-MM-DD] brain | <제목>` 한 줄 append.
   - 탐색(Navigate)에 decision·ingest 후보가 있으면, "이건 `wiki/` 로 ingest/decision 으로 승격할까요?" 제안.

## 톤·언어
- 사용자와의 대화는 **존댓말**. brain note **본문은 평어체**(~한다, ~이다). 파일명·frontmatter·slug 는 영어 kebab-case. (CLAUDE.md §3)
- 장황한 preamble 금지. 짧게, 본인의 생각이 주인공이 되도록 — 내가 대신 생각해 채우지 말고 *끄집어내는* 역할.
