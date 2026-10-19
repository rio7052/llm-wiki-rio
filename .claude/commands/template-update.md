---
description: 템플릿 새 판을 내 위키에 반영 — 바뀐 것 요약 → 파일 동기화 → 충돌 합치기 → 사람이 할 일 → 커밋
argument-hint: (선택) 없음. 특정 파일을 빼려면 "eod.md 빼고" 처럼 말한다
---

`/template-update` — 개인 위키 템플릿(`bodit-inc/llm-wiki-template`)의 새 판을 받아 온다. 도구는 `tools/template-sync.py`, 받는 방법과 규칙은 [UPDATE.md](../../UPDATE.md), 판별 변경 내용은 템플릿의 `CHANGELOG.md` 에 있다.

> **내 기록은 건드리지 않는다**: `me.md`·`brain/`·`raw/`·`wiki/`·`index.md`·`log.md`·`channels.json`·`.env`.
> 템플릿이 관리하는 것은 커맨드·도구·안내 문서·`CLAUDE.md`·`.gitignore` 다. 내가 고친 파일은 3방향으로 합친다.
> 도구가 없으면(처음) UPDATE.md 의 "처음 한 번" 을 먼저 따라 한다.

## 1. 미리보기

```
python tools/template-sync.py
```

- 바뀐 판(CHANGELOG)·**사람이 할 일**·파일 분류가 나온다. **"받을 파일 변경이 없다"** 면 그 사실만 한 줄로 보고하고 끝낸다.
- 사용자에게는 **짧게** 보여 준다: 새 판 제목들, 사람이 할 일, 파일 수(바꿈·추가·합침·충돌). 파일 목록은 10개가 넘으면 접어서 요약한다.
- `gh` 로그인·네트워크 문제로 못 받으면(종료 코드 3) 그 사실만 알리고 멈춘다. 다른 경로로 우회해 받지 않는다.

## 2. 승인 → 적용

사용자가 승인하면 실행한다. 빼달라는 파일이 있으면 `--skip <경로>` 를 붙인다.

```
python tools/template-sync.py --yes
```

## 3. 합치지 못한 파일 합치기

충돌이 있으면 `.template-sync/` 에 재료가 남는다. **한 파일씩** 처리한다.

1. 세 판을 읽는다: 내 파일(그대로 있다) · `.template-sync/base/<경로>`(내가 마지막에 받았던 템플릿 판) · `.template-sync/new/<경로>`(새 템플릿 판). `.template-sync/conflicts/<경로>` 는 충돌 표시가 들어간 합친 결과다.
2. **내가 고친 부분은 살리고 템플릿의 새 내용을 얹는다.** `CLAUDE.md` 면 내가 채운 `<...>` 자리와 내가 더한 규칙을 반드시 유지한다.
3. 판단이 필요한 대목(같은 줄을 서로 다르게 고친 경우)만 사용자에게 묻는다.
4. 결과를 보여 주고 승인받은 뒤 표시를 지운다.
   ```
   python tools/template-sync.py --resolved <경로>
   ```

## 4. 사람이 할 일 안내

CHANGELOG 의 `사람이 할 일` 을 하나씩 짚는다.
- **Claude 가 할 수 있는 것**(명령 실행·설정 확인)은 승인받고 실행한다. 예: `python tools/slack-ingest/nas_slack.py --check`, `powershell -File tools/install-secret-hook.ps1`, `gh auth refresh -h github.com -s project`.
- **사람이 해야 하는 것**(NAS 폴더 로그인, 슬랙 앱 설정)은 안내만 하고 완료 여부를 묻는다.
- 못 한 것은 남겨 두고 마지막 보고에 적는다.

## 5. 마무리

- 커밋: 바뀐 파일과 `.template-version` 을 함께 올린다. `.template-sync/` 는 `.gitignore` 라 안 올라간다.
  ```
  git add -A -- .template-version <바뀐 경로들>
  git commit -m "template: vN 반영"
  ```
  이어서 push 한다(`/eod` §7 과 같다). ZIP 으로 쓰는 사람은 건너뛴다.
- `log.md` 에 한 줄: `## [YYYY-MM-DD] template | vA → vB` + 사람이 할 일 처리 결과.
- **한 줄 보고**: 새 판 N개 · 바꾼 파일 M · 합친 파일 K · 남은 충돌 J · 사람이 할 일 P건(끝낸 것/남은 것).

## 톤·안전
- 사용자와의 대화는 **존댓말**, 위키 본문은 **평어체**.
- **미리보기 없이 적용하지 않는다.** `--yes` 는 승인 뒤에만 붙인다.
- 내 기록 폴더는 도구가 건드리지 않는다. 혹시 `wiki/`·`raw/`·`brain/` 이 바뀌었다면 멈추고 알린다.
- 충돌을 임의로 "템플릿 것으로" 덮지 않는다. 내가 고친 이유가 있을 수 있으니 애매하면 묻는다.
- 받은 뒤 커맨드 파일이 바뀌었으면, 새 커맨드는 Claude Code 를 다시 켜야 보인다고 알린다.
