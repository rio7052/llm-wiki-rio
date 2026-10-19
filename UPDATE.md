# 템플릿 새 판 받기

> 템플릿(이 저장소)이 바뀌면 내 개인 위키에 **명령 하나로** 받아 온다. 내 기록은 건드리지 않는다.
> 무엇이 바뀌었는지는 [CHANGELOG.md](CHANGELOG.md) 에 판마다 적혀 있다.

## 평소

```
/template-update
```

`/morning` 이 새 판을 보면 한 줄로 알려 준다. 그때 이 한 줄만 치면 된다.

Claude 가 이렇게 진행한다.
1. 무엇이 바뀌었는지와 **사람이 할 일**을 보여 준다.
2. 승인하면 파일을 받아 온다.
3. 자동으로 합치지 못한 파일은 내 것을 살려 가며 함께 합친다.
4. 바뀐 파일을 커밋한다.

## 처음 한 번 (이 명령이 아직 없을 때)

개인 위키 폴더의 Claude Code 에 이렇게 말한다.

```
gh 로 bodit-inc/llm-wiki-template 의 UPDATE.md 를 읽고 "처음 한 번" 을 따라 해줘.
```

Claude 가 할 일은 셋이다.

1. 동기화 도구를 받는다.

   ```bash
   python -c "import pathlib,subprocess;p='tools/template-sync.py';pathlib.Path(p).parent.mkdir(parents=True,exist_ok=True);pathlib.Path(p).write_bytes(subprocess.run(['gh','api','-H','Accept: application/vnd.github.raw','repos/bodit-inc/llm-wiki-template/contents/tools/template-sync.py'],capture_output=True,check=True).stdout)"
   ```

2. 무엇이 바뀌는지 본다. **아직 아무것도 바꾸지 않는다.**

   ```bash
   python tools/template-sync.py
   ```

3. 사람이 확인한 뒤 적용하고, 그다음은 `/template-update` 2~4단계와 같다.

   ```bash
   python tools/template-sync.py --yes
   ```

> `gh` 로그인이 필요하다(`gh auth status`). 템플릿 저장소가 private 이라 로그인 없이는 받을 수 없다.
> 처음 실행은 **파일마다 템플릿 이력에서 내 파일과 똑같은 판을 찾아** 기준으로 삼는다. 그래서 그동안 부분적으로 받아 왔더라도 어긋나지 않는다.

## 무엇을 건드리고 무엇을 안 건드리나

| | 파일 | 어떻게 |
|---|---|---|
| **템플릿이 관리** | `.claude/commands/` · `tools/` · `CLAUDE.md` · 안내 문서(README·SETUP·START-HERE 등) · `.gitignore` | 내가 안 고쳤으면 새 판으로 바꾼다. 고쳤으면 **3방향으로 합친다**(내 수정 + 템플릿 수정) |
| **절대 안 건드림** | `me.md` · `brain/` · `raw/` · `wiki/` · `index.md` · `log.md` · `tools/slack-ingest/channels.json` · `.env` | 그대로 둔다 |

- 규칙은 `tools/template-sync-rules.txt` 에 있다. **내가 크게 고친 커맨드를 갱신에서 빼고 싶으면** 그 줄을 `keep` 으로 올린다. 예: `keep .claude/commands/eod.md`
- **내가 지운 파일은 다시 받지 않는다.** (안 쓰는 커맨드를 지웠어도 매번 되살아나지 않는다.)
- 이번에만 어떤 파일을 빼고 싶으면 `python tools/template-sync.py --yes --skip <경로>`.

## 합치지 못한 파일이 있을 때

내 수정과 템플릿 수정이 같은 줄에서 부딪히면 도구는 **내 파일을 그대로 두고** 재료만 `.template-sync/` 에 모은다.

```
.template-sync/conflicts/<경로>   충돌 표시가 들어간 합친 결과
.template-sync/base/<경로>        내가 마지막으로 받았던 템플릿 판
.template-sync/new/<경로>         새 템플릿 판
```

`/template-update` 가 이 셋을 보고 내 파일에 합쳐 준다. 다 합치면 표시를 지운다.

```bash
python tools/template-sync.py --resolved <경로>
```

## 막혔을 때

| 이런 말이 나오면 | 이렇게 한다 |
|---|---|
| `템플릿을 받지 못했다` | `gh auth status` 로 로그인 확인. `bodit-inc` 조직 접근 권한이 있어야 한다 |
| `gh 을 찾지 못했다` | GitHub CLI 를 설치한다([GITHUB-CONNECT.md](GITHUB-CONNECT.md) §1-2) |
| 받고 나서 커맨드가 안 보인다 | Claude Code 를 한 번 껐다 켠다 |
| 합친 결과가 이상하다 | 커밋 전이면 `git checkout -- <경로>` 로 되돌리고 `--skip <경로>` 로 그 파일만 빼고 다시 받는다 |

## 템플릿을 고치는 사람 (Kevin)

1. 템플릿에 변경을 올릴 때 **`CHANGELOG.md` 맨 위에 판을 하나 올린다**(`## vN · 날짜 · 제목` + `### 바뀐 것` + `### 사람이 할 일`).
2. 사람이 할 일이 있는 변경은 **슬랙에도 공지**한다. 공지 문안은 CHANGELOG 항목을 그대로 쓰면 된다.
3. 판을 올리지 않으면 `/morning` 알림에는 "작은 수정이 있다" 로만 뜨고, 사람이 할 일은 전달되지 않는다.
