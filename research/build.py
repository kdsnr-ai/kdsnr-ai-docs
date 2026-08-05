# -*- coding: utf-8 -*-
"""리서치 포스팅 .md → .html 변환.

글은 .md로 쓰고 이 스크립트로 .html을 만든다. 사이트가 쓰는 문법만 처리하므로
설치할 것이 없다(표준 라이브러리만 사용).

사용:
    python build.py                 # 이 폴더의 .md 전부 변환
    python build.py archive.md      # 하나만
    python build.py archive.md -o   # 변환 후 브라우저로 열기

쓸 수 있는 문법
    ---                     맨 위 머리말 시작·끝
    title: / sub: / meta:   제목 · 부제 · (분류 · 날짜 · 작성자)
    ## 제목                 큰 절
    ### 제목                작은 절
    - 항목                  목록
    **굵게**                강조
    [글자](주소)            링크
    > 문장                  안내 상자. 첫 줄이 **굵게**면 상자 제목이 된다
    ![설명](파일.png)       그림. 설명은 캡션으로 아래에 붙는다
    | a | b |               표. 다음 줄에 |---|---| 구분선이 있어야 한다
    <!-- 메모 -->           HTML 주석 — 그대로 남고 화면에는 안 보인다
    빈 줄                   문단 구분
"""
from __future__ import annotations

import html
import re
import sys
import webbrowser
from pathlib import Path

SHELL = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>kdsnr-ai · {title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="../assets/style.css?v=20260804-1">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github-dark.min.css">
</head>
<body>

<aside class="sidebar" id="sidebar"></aside>
<script src="../assets/nav.js?v=20260729-2"></script>

<main class="content">

<article class="post fn-below">

<h1>{title}</h1>
<p class="post-sub">{sub}</p>
<p class="post-meta">{meta}</p>

{body}

</article>

</main>
</body>
</html>
"""


def esc(s: str) -> str:
    """본문용 이스케이프 — 따옴표는 그대로 둔다(본문에서는 escape할 필요가 없고 소스만 지저분해진다)."""
    return html.escape(s, quote=False)


def inline(text: str) -> str:
    """굵게·링크만 처리하고 나머지는 이스케이프 (HTML 태그를 직접 쓰지 않아도 되게)."""
    out, pos = [], 0
    pattern = re.compile(r"\*\*(.+?)\*\*|!\[([^\]]*)\]\(([^)]+)\)|\[([^\]]+)\]\(([^)]+)\)")
    for m in pattern.finditer(text):
        out.append(esc(text[pos:m.start()]))
        if m.group(1) is not None:
            out.append(f"<strong>{esc(m.group(1))}</strong>")
        elif m.group(3) is not None:                   # 이미지
            out.append(f'<img src="{html.escape(m.group(3), quote=True)}" '
                       f'alt="{html.escape(m.group(2), quote=True)}">')
        else:
            out.append(f'<a href="{html.escape(m.group(5), quote=True)}">{esc(m.group(4))}</a>')
        pos = m.end()
    out.append(esc(text[pos:]))
    return "".join(out)


def convert(md: str) -> tuple[dict, str]:
    lines = md.splitlines()
    head: dict = {}
    if lines and lines[0].strip() == "---":            # 머리말
        end = lines.index("---", 1)
        for line in lines[1:end]:
            if ":" in line:
                k, v = line.split(":", 1)
                head[k.strip()] = v.strip()
        lines = lines[end + 1:]

    out: list[str] = []
    buf: list[str] = []      # 이어지는 문단
    items: list[str] = []    # 목록
    quote: list[str] = []    # 안내 상자

    def flush_para():
        if buf:
            out.append(f"<p>{inline(' '.join(buf))}</p>")
            buf.clear()

    def flush_list():
        if items:
            out.append("<ul>\n" + "\n".join(f"<li>{inline(i)}</li>" for i in items) + "\n</ul>")
            items.clear()

    def flush_quote():
        if not quote:
            return
        body = []
        first = quote[0]
        m = re.fullmatch(r"\*\*(.+?)\*\*", first.strip())
        if m:                                          # 첫 줄이 굵게면 상자 제목
            body.append(f'<p class="note-head">{inline(m.group(1))}</p>')
            rest = quote[1:]
        else:
            rest = quote
        if rest:
            body.append(f"<p>{inline(' '.join(rest))}</p>")
        out.append('<div class="note">\n' + "\n".join(body) + "\n</div>"
                   if len(body) > 1 else f'<div class="note">{inline(" ".join(quote))}</div>')
        quote.clear()

    rows: list[list[str]] = []   # 표

    def flush_table():
        if not rows:
            return
        head_cells, body_rows = rows[0], rows[1:]
        cells = "".join(f"<th>{inline(c)}</th>" for c in head_cells)
        trs = ["<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body_rows]
        out.append("<table>"
                   f"<thead><tr>{cells}</tr></thead>"
                   "<tbody>" + "".join(trs) + "</tbody></table>")
        rows.clear()

    def flush_all():
        flush_para(); flush_list(); flush_quote(); flush_table()

    def split_row(s: str) -> list[str]:
        return [c.strip() for c in s.strip().strip("|").split("|")]

    for line in lines:
        s = line.rstrip()
        if not s.strip():
            flush_all()
        elif s.startswith("<!--"):
            flush_all()
            out.append(s)
        elif s.startswith("### "):
            flush_all()
            out.append(f"<h3>{inline(s[4:])}</h3>")
        elif s.startswith("## "):
            flush_all()
            out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("|") and set(s.replace("|", "").replace(" ", "")) <= set("-:"):
            pass                                       # 표 구분선 |---|---| 은 버린다
        elif s.startswith("|"):
            flush_para(); flush_list(); flush_quote()
            rows.append(split_row(s))
        elif re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", s.strip()):
            flush_all()                                # 줄 전체가 그림이면 캡션을 붙여 크게 싣는다
            m = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", s.strip())
            # 사이트에 이미 있는 .shots 규칙을 쓴다 (새 클래스를 만들면 스타일이 따로 논다)
            cap = f"<figcaption>{esc(m.group(1))}</figcaption>" if m.group(1) else ""
            out.append('<figure class="shots single">'
                       f'<img src="{html.escape(m.group(2), quote=True)}" '
                       f'alt="{html.escape(m.group(1), quote=True)}">{cap}</figure>')
        elif s.startswith("- "):
            flush_para(); flush_quote()
            items.append(s[2:])
        elif s.startswith(">"):
            flush_para(); flush_list()
            quote.append(s.lstrip("> ").rstrip())
        else:
            flush_list(); flush_quote()
            buf.append(s.strip())
    flush_all()
    return head, "\n\n".join(out)


def build(path: Path) -> Path:
    head, body = convert(path.read_text(encoding="utf-8"))
    missing = [k for k in ("title", "sub", "meta") if k not in head]
    if missing:
        raise SystemExit(f"{path.name}: 머리말에 {', '.join(missing)} 가 없습니다")
    target = path.with_suffix(".html")
    target.write_text(SHELL.format(title=head["title"], sub=head["sub"],
                                   meta=head["meta"], body=body), encoding="utf-8")
    return target


if __name__ == "__main__":
    here = Path(__file__).parent
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    targets = [here / a for a in args] or sorted(here.glob("*.md"))
    if not targets:
        raise SystemExit("변환할 .md 파일이 없습니다")
    for src in targets:
        out = build(src)
        print(f"  {src.name} → {out.name}  ({out.stat().st_size:,} bytes)")
        if "-o" in sys.argv:
            webbrowser.open(out.resolve().as_uri())
