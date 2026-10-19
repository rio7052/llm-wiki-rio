# brain/ — 2nd brain

> 내가 모으고 **쓴** 생각의 레이어.

## 3-brain 위치

| | 정의 | 레이어 |
|---|---|---|
| 1st brain | 직관·감성 (나 자신) | — (파일 아님) |
| **2nd brain** | 내가 모으고 쓴 지식 | **`brain/`** (내 생각) + `raw/` (캡처한 재료) |
| 3rd brain | AI 가 컴파일한 지식 | `wiki/` |

핵심: **2nd = 사람 측(내가 쓴 것) / 3rd = AI 측(AI 가 컴파일)**.
1st brain(내 직관)을 brain note 로 끄집어내 2nd brain 에 쌓으면, AI 가 그걸 컴파일해 3rd brain(`wiki/`)을 만든다.

## wiki/ 와의 차이

- `wiki/` (3rd) = AI 합성, **중립적**, "X 는 무엇인가".
- `brain/` (2nd) = 내 생각, **주관·가설·반론**, "그래서 내 생각은 무엇인가".

## 규칙

- 위치: `brain/<slug>.md`. 파일명 kebab-case 영어.
- 포맷: [TEMPLATE.md](TEMPLATE.md) (배경·공명·확장·통합·탐색).
- raw 와 달리 **editable** — 생각이 자라면 갱신한다. `status`: seed → growing → evergreen.
- 고립 금지 (§6): 통합 섹션에서 wiki/project 페이지로 최소 1개 link.
- 굳은 통찰·결정은 `wiki/`(decisions·concepts)로 **ingest** 해 3rd brain 으로 승격.

## 도메인 축 — 자라면 그때 폴더로

brain note 는 **개수가 적을 땐 flat 유지**하고 **도메인 태그**로만 축을 잡는다. 폴더는 한 축이 비대해져 *아플 때* 판다(CLAUDE.md §14). status 로는 폴더를 나누지 않는다 — frontmatter 필드로 충분하고 이동하면 wikilink 가 깨진다.

도메인 태그(`tags` 첫 항목으로 1개) 예시 — 본인 분야에 맞게:

| 태그 | 의미 |
|---|---|
| `<domain-a>` | 본인 전문 도메인 생각 |
| `ops` | 운영·팀리딩·일하는 방식 생각 |
| `meta` | AI 협업·위키·시스템 자체에 대한 생각 |

**폴더 분리 트리거**: 한 도메인이 ~10개를 넘고 한눈에 안 들어올 때. 그 시점에 해당 태그 노트만 하위 폴더로 옮기고 wikilink 를 갱신한다.

schema: CLAUDE.md §4.1(디렉토리)·§5(brain-note type) 참조.
