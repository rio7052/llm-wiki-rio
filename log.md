# Wiki Log

> 시간순 활동 로그 (append-only). **가장 최근이 위.** prefix `## [YYYY-MM-DD] <op>`.
> `grep "^## \[" log.md | head -20` 으로 최근 활동을 스캔한다.

<!-- 예시:
## [2026-05-18] daily | 2026-05-18
- raw: raw/reports/daily/2026-05-18.md

## [2026-05-18] ingest | "<title>" (paper)
- raw: raw/papers/<slug>.md
- 갱신: [[concepts/...]]
- 신규: [[entities/...]]
-->

## [2026-10-25] daily | 2026-10-25
- raw: raw/reports/daily/2026-10-25.md (10-21·10-22 리포트도 이번에 함께 커밋)
- 전사 공유본 업로드: bodit-inc/bodit-llm-wiki raw/reports/daily/rio/2026-10-25.md (금액·번호·개인명·배운점 제외)
- 규칙 변경: `/morning` 미완료 할 일 자동 이월 (별도 커밋 abe7de8)

## [2026-10-20] daily | 2026-10-20
- raw: raw/reports/daily/2026-10-20.md
- 전사 공유본 업로드: bodit-inc/bodit-llm-wiki raw/reports/daily/rio/2026-10-20.md (회고 생략)

## [2026-10-19] promote | 전사 프로필에 GitHub 계정 추가
- 전사: bodit-inc/bodit-llm-wiki people/rio.md (`github: rio7052`) — commit 4953f09
- 비고: `mine-put` 은 github 계정이 등록돼 있어야 동작해 첫 등록은 gh api 로 직접 올림

## [2026-10-19] setup | 개인 위키 초기 설정
- me.md: 이름·역할 유형(member)·본업(운영팀 매니저, ops)·L1 미션·AI 보완점
- 전사 위키 연결 확인: whoami(rio·ops), task-list --mine 정상
