#!/usr/bin/env bash
# md → pdf (pandoc 으로 html 을 만들고 Chrome headless 로 인쇄한다)
#
#   bash tools/md-to-pdf.sh <입력.md> <출력.pdf> ["문서 제목"]
#
# 한글은 맑은 고딕으로 임베딩된다. LaTeX 없이 동작한다.
set -euo pipefail

IN="${1:?사용법: bash tools/md-to-pdf.sh <입력.md> <출력.pdf> [제목]}"
OUT="${2:?출력 pdf 경로가 필요하다}"
TITLE="${3:-$(basename "$IN" .md)}"

# 경로는 환경변수로 덮어쓸 수 있다. 예:
#   PANDOC=/usr/bin/pandoc CHROME=/usr/bin/google-chrome bash tools/md-to-pdf.sh ...
PANDOC="${PANDOC:-$(command -v pandoc 2>/dev/null || true)}"
CHROME="${CHROME:-}"
if [ -z "$CHROME" ]; then
  for c in "/c/Program Files/Google/Chrome/Application/chrome.exe"            "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"            "$(command -v google-chrome 2>/dev/null || true)"            "$(command -v chromium 2>/dev/null || true)"; do
    [ -n "$c" ] && [ -f "$c" ] && CHROME="$c" && break
  done
fi

[ -n "$PANDOC" ] && [ -x "$PANDOC" ] || { echo "pandoc 을 찾지 못했다. 설치하거나 PANDOC 환경변수로 경로를 지정한다."; exit 1; }
[ -n "$CHROME" ] && [ -f "$CHROME" ] || { echo "Chrome 을 찾지 못했다. CHROME 환경변수로 경로를 지정한다."; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cat > "$WORK/style.css" <<'CSSEOF'
@page { size: A4; margin: 18mm 16mm 20mm; }
body { font-family: "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo", "Noto Sans KR", system-ui, sans-serif;
       font-size: 10.5pt; line-height: 1.65; color: #1a1f24; max-width: none; margin: 0; }
h1 { font-size: 19pt; border-bottom: 2.5px solid #1D4E63; padding-bottom: 8px; margin: 0 0 6px; color: #12333f; }
h2 { font-size: 13.5pt; margin: 22px 0 8px; padding: 6px 0 6px 10px; border-left: 4px solid #1D4E63;
     background: #f2f6f8; color: #12333f; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 14px 0 6px; color: #2b4a58; page-break-after: avoid; }
blockquote { margin: 10px 0; padding: 8px 14px; background: #f7f9fa; border-left: 3px solid #7fa8b8; color: #33424c; }
blockquote p { margin: 4px 0; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9.5pt; page-break-inside: avoid; }
th { background: #e8eef1; border: 1px solid #c3ced5; padding: 6px 8px; text-align: left; font-weight: 600; }
td { border: 1px solid #d6dee3; padding: 6px 8px; vertical-align: top; }
ul, ol { padding-left: 22px; margin: 8px 0; }
li { margin: 3px 0; }
hr { border: 0; border-top: 1px solid #d6dee3; margin: 20px 0; }
code { background: #eef2f4; padding: 1px 5px; border-radius: 3px; font-size: 9.5pt;
       font-family: "Consolas", "D2Coding", monospace; }
strong { color: #0f2830; }
p { margin: 7px 0; }
CSSEOF

# 문서 안에 이미 `# 제목` 이 있으면 제목을 한 번 더 찍지 않는다(탭 제목으로만 쓴다).
# frontmatter(---) 는 건너뛰고 본문의 첫 줄을 본다. 없을 때만 받은 제목을 맨 위에 넣는다.
FIRST="$(awk 'NR==1 && /^---[[:space:]]*$/ {fm=1; next} fm && /^---[[:space:]]*$/ {fm=0; next} fm {next} NF {print; exit}' "$IN" | tr -d '\r')"
case "$FIRST" in
  "# "*) TITLE_OPT=(--metadata pagetitle="$TITLE") ;;
  *)     TITLE_OPT=(--metadata title="$TITLE") ;;
esac

"$PANDOC" "$IN" -o "$WORK/doc.html" \
  --standalone --from markdown --to html5 \
  "${TITLE_OPT[@]}" --css style.css

mkdir -p "$(dirname "$OUT")"
# Chrome 은 상대 경로에 쓰지 못한다. 반드시 절대 경로로 넘긴다.
OUT_ABS="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
OUT_WIN="$(cygpath -m "$OUT_ABS" 2>/dev/null || echo "$OUT_ABS")"
# 실패해도 옛 파일이 남아 성공처럼 보이는 것을 막는다.
rm -f "$OUT_ABS"

"$CHROME" --headless --disable-gpu --no-sandbox \
  --run-all-compositor-stages-before-draw --virtual-time-budget=15000 \
  --print-to-pdf="$OUT_WIN" \
  --no-pdf-header-footer "file:///$(cygpath -m "$WORK" 2>/dev/null || echo "$WORK")/doc.html" 2>&1 \
  | grep -vE "DEPRECATED_ENDPOINT|registration_request|GCM|Registration response" || true

[ -s "$OUT_ABS" ] || { echo "PDF 생성 실패: $OUT_ABS"; exit 1; }
OUT="$OUT_ABS"
python - "$OUT" <<'PYEOF'
import re, sys
d = open(sys.argv[1], 'rb').read()
print(f"생성 완료: {sys.argv[1]}  {len(re.findall(rb'/Type./Page[^s]', d))}쪽  {len(d)//1024}KB  폰트임베딩={b'FontFile2' in d}")
PYEOF
