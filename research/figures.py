# -*- coding: utf-8 -*-
"""Archive 포스팅의 검색 예시 도식을 만든다.

문항 이미지와 학년도·번호·정답률·단원은 아카이브에서 받아 오므로,
자료가 바뀌면 다시 돌리기만 하면 된다. 도식은 SVG로 나오고 문항 이미지는
그 안에 실려 있어 파일 하나로 완결된다.

사용:
    ARCHIVE_KEY=... python figures.py            # 전부
    ARCHIVE_KEY=... python figures.py filter     # 하나만
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ARCHIVE = "https://kdsnr-archive-2mkpi2xkyq-du.a.run.app"
HERE = Path(__file__).parent
CACHE = HERE / "_figure_cache"

FONT = "Pretendard, Apple SD Gothic Neo, sans-serif"
INK = "#30343b"
HEAD_IN = "#f6f7f9"
HEAD_OUT = "#eaf1fb"
TEXT = "#191f28"
SUB = "#4e5968"
FAINT = "#8b95a1"

WIDTH = 960
MARGIN = 30
BODY = WIDTH - MARGIN * 2
HEAD = 42
LABEL = 74
PAD = 12
ARROW = 56


def api(path: str, params: dict) -> dict:
    key = os.environ.get("ARCHIVE_KEY")
    if not key:
        raise SystemExit("ARCHIVE_KEY 환경변수가 필요합니다")
    url = f"{ARCHIVE}{path}?{urllib.parse.urlencode(params, doseq=True)}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())


def question_image(item_id: str) -> Path:
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / f"{item_id}.webp"
    if not cached.exists():
        out = api(f"/v1/questions/{item_id}", {"include_img": 1})
        blob = out.get("q_img") or ""
        raw = base64.b64decode(blob.split(",")[-1] if blob.startswith("data:") else blob)
        cached.write_bytes(raw)
    return cached


def lookup(year: int, q_num: int, course: str = "생명과학1", org: str = "수능") -> dict:
    out = api("/v1/questions", {"course": course, "org": org,
                                "year": year, "q_num": q_num, "limit": 1})
    items = out.get("items") or []
    if not items:
        raise SystemExit(f"{year}학년도 {q_num}번을 아카이브에서 찾지 못했습니다")
    return items[0]


def rate(item: dict) -> str:
    value = item.get("correct_rate")
    return f"정답률 {round(value * 100)}%" if value is not None else "정답률 미입력"


def text(x, y, s, size=17.5, weight=None, fill=TEXT, anchor=None) -> str:
    bits = [f'x="{x}" y="{y}" font-size="{size}" fill="{fill}"']
    if weight:
        bits.append(f'font-weight="{weight}"')
    if anchor:
        bits.append(f'text-anchor="{anchor}"')
    return f'<text {" ".join(bits)}>{s}</text>'


def frame(x, y, w, h, head_fill) -> str:
    return (f'<g transform="translate({x} {y})">'
            f'<rect width="{w}" height="{h}" rx="10" fill="#ffffff" '
            f'stroke="{INK}" stroke-width="2"/>'
            f'<rect x="1" y="1" width="{w - 2}" height="{HEAD - 1}" rx="9" '
            f'fill="{head_fill}"/>'
            f'<rect x="1" y="{HEAD - 11}" width="{w - 2}" height="10" '
            f'fill="{head_fill}"/>'
            f'<path d="M0 {HEAD}h{w}" stroke="{INK}" stroke-width="2"/>')


def shot(path: Path, x, y, w) -> tuple[str, float]:
    picture = Image.open(path)
    height = w * picture.height / picture.width
    buffer = io.BytesIO()
    picture.convert("RGB").save(buffer, "WEBP", quality=88, method=6)
    blob = base64.b64encode(buffer.getvalue()).decode()
    return (f'<image href="data:image/webp;base64,{blob}" x="{x}" y="{y}" '
            f'width="{w}" height="{height:.1f}" preserveAspectRatio="none"/>'), height


def rule(d) -> str:
    return f'<path d="{d}" stroke="{INK}" stroke-width="2"/>'


def results(y, head, note, cards) -> tuple[str, float]:
    column = BODY / 3
    parts = []
    shots = []
    for index, card in enumerate(cards):
        x = MARGIN + index * column + 16
        block, height = shot(card["shot"], x, y + HEAD + LABEL + PAD,
                             column - 32)
        shots.append(height)
        parts.append(block)
    height = HEAD + LABEL + PAD + max(shots) + 16

    out = [frame(MARGIN, y, BODY, height, HEAD_OUT),
           text(18, 28, head, 19, 700, TEXT),
           rule(f"M0 {HEAD + LABEL}h{BODY}")]
    if note:
        out.append(text(BODY - 18, 28, note, 17, None, FAINT, "end"))
    for index, card in enumerate(cards):
        x = index * column
        if index:
            out.append(rule(f"M{x} {HEAD}v{height - HEAD}"))
        out.append(text(x + 16, HEAD + 32, card["title"], 17.5, 650, TEXT))
        out.append(text(x + 16, HEAD + 58, card["sub"], 15.5, None, FAINT))
    out.append("</g>")
    return "".join(out) + "".join(parts), height


def conditions(y, head, rows) -> tuple[str, float]:
    height = HEAD + 66
    column = BODY / len(rows)
    out = [frame(MARGIN, y, BODY, height, HEAD_IN),
           text(18, 28, head, 19, 700, SUB)]
    for index, (name, value) in enumerate(rows):
        x = index * column
        if index:
            out.append(rule(f"M{x} {HEAD}v{height - HEAD}"))
        out.append(text(x + 18, HEAD + 26, name, 15.5, None, FAINT))
        out.append(text(x + 18, HEAD + 52, value, 18, 650, TEXT))
    out.append("</g>")
    return "".join(out), height


def sentence(y, head, line) -> tuple[str, float]:
    height = HEAD + 66
    out = [frame(MARGIN, y, BODY, height, HEAD_IN),
           text(18, 28, head, 19, 700, SUB),
           text(BODY / 2, HEAD + 43, f"“{line}”", 19, 650, TEXT, "middle"),
           "</g>"]
    return "".join(out), height


def query_shot(y, head, note, label, path, line=None) -> tuple[str, float]:
    band = 46
    width = 340 if line else 380
    split = BODY * 0.52 if line else None
    left = MARGIN + (split - width) / 2 if line else MARGIN + (BODY - width) / 2
    block, picture = shot(path, left, y + HEAD + band + PAD, width)
    height = HEAD + band + PAD + picture + 16

    out = [frame(MARGIN, y, BODY, height, HEAD_IN),
           text(18, 28, head, 19, 700, SUB),
           rule(f"M0 {HEAD + band}h{BODY}")]
    if note:
        out.append(text(BODY - 18, 28, note, 17, None, FAINT, "end"))
    out.append(text(left - MARGIN, HEAD + 30, label, 17.5, 650, TEXT))
    if line:
        out.append(rule(f"M{split} {HEAD}v{height - HEAD}"))
        out.append(text(split + 26, HEAD + 30, "문장", 17.5, 650, TEXT))
        out.append(text((split + BODY) / 2, HEAD + band + (height - HEAD - band) / 2,
                        f"“{line}”", 18, 650, TEXT, "middle"))
    out.append("</g>")
    return "".join(out) + block, height


def arrow(y) -> str:
    return (f'<g transform="translate(480 {y + 12})">'
            f'<path d="M0 0v20" stroke="{FAINT}" stroke-width="2.5"/>'
            f'<path d="M-7 20l7 14 7-14z" fill="{FAINT}"/></g>')


def compose(name, title, desc, uid, blocks) -> Path:
    y = 66
    body = []
    for index, make in enumerate(blocks):
        if index:
            body.append(arrow(y))
            y += ARROW
        chunk, height = make(y)
        body.append(chunk)
        y += height
    total = round(y + MARGIN)

    target = HERE / f"{name}.svg"
    target.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {total}" '
        f'role="img" aria-labelledby="{uid}t {uid}d">'
        f'<title id="{uid}t">{title}</title><desc id="{uid}d">{desc}</desc>'
        f'<rect width="{WIDTH}" height="{total}" fill="#ffffff"/>'
        f'<g font-family="{FONT}">'
        + text(WIDTH / 2, 38, title, 27, 750, TEXT, "middle")
        + "".join(body) + "</g></svg>\n", encoding="utf-8")
    return target


def card(item: dict, sub: str | None = None) -> dict:
    return {"title": f'{item["year"]}학년도 수능 {item["q_nums_all"][0]}번',
            "sub": sub or f'{rate(item)} · {item.get("unit") or ""}'.strip(" ·"),
            "shot": question_image(item["item_id"])}


def build_filter() -> Path:
    found = api("/v1/questions", {"course": "생명과학1", "org": "수능",
                                  "keyword": "가계도", "limit": 20})
    items = sorted(found["items"], key=lambda i: -i["year"])[:3]
    cards = [card(i) for i in items]
    years = " · ".join(f'{i["year"]}' for i in items)
    return compose(
        "archive-filter", "조건으로 찾기",
        f'과목 생명과학Ⅰ, 시험 수능, 키워드 가계도를 조건으로 넣으면 '
        f'{found["total"]}건이 나오고, 그중 앞 셋은 {years}학년도 수능 19번입니다',
        "af",
        [lambda y: conditions(y, "넣은 것 — 조건",
                              [("과목", "생명과학Ⅰ"), ("시험", "수능"),
                               ("키워드", "가계도")]),
         lambda y: results(y, f'나온 것 — {found["total"]}건 · 소요시간 0.2초',
                           None, cards)])


def build_content() -> Path:
    line = "근육 원섬유 마디의 길이 변화를 계산하는 문항"
    items = [lookup(2020, 14), lookup(2021, 16), lookup(2022, 13)]
    cards = [card(i) for i in items]
    return compose(
        "archive-content", "문장으로 찾기",
        "근육 원섬유 마디의 길이 변화를 계산하는 문항이라고 문장으로 물으면 "
        "6건이 나오고, 그중 앞 셋은 2020학년도 14번, 2021학년도 16번, "
        "2022학년도 13번으로 모두 골격근의 수축 과정을 다룹니다",
        "ac",
        [lambda y: sentence(y, "넣은 것 — 문장", line),
         lambda y: results(y, "나온 것 — 6건 · 소요시간 2.1초", None, cards)])


def build_similar() -> Path:
    query = HERE / "gangdae-mock-2025-1-19.webp"
    if not query.exists():
        raise SystemExit(f"{query} 가 필요합니다 (아카이브에 없는 문항)")
    found = [(2022, 19, "0.985"), (2024, 19, "0.984"), (2025, 19, "0.983")]
    cards = [card(lookup(y, n), f"유사도 {s} · 유전") for y, n, s in found]
    return compose(
        "archive-similar", "문항으로 찾기",
        "아카이브에 없는 2025학년도 강대모의고사 1회 19번을 그대로 넣으면 "
        "2022 · 2024 · 2025학년도 수능 19번이 유사도 0.98대로 올라옵니다",
        "as",
        [lambda y: query_shot(y, "넣은 것 — 문항", "아카이브에 없는 문항",
                              "2025학년도 강대모의고사 1회 19번", query),
         lambda y: results(y, "나온 것 — 비슷한 문항", "수능 기출 10개년 중",
                           cards)])


def build_combo() -> Path:
    line = "DNA 상대량 표를 함께 제시하는 문항"
    seed = lookup(2026, 19)
    found = [(2023, 19, "0.984"), (2020, 19, "0.984"), (2024, 19, "0.981")]
    cards = [card(lookup(y, n), f"유사도 {s} · 유전") for y, n, s in found]
    return compose(
        "archive-combo", "문항과 문장을 함께 넣기",
        "2026학년도 수능 19번과 DNA 상대량 표를 함께 제시하는 문항이라는 문장을 "
        "같이 넣으면 유사도 차례를 그대로 둔 채 조건에 맞는 것만 남습니다",
        "ax",
        [lambda y: query_shot(y, "넣은 것 — 문항과 문장", None,
                              "2026학년도 수능 19번",
                              question_image(seed["item_id"]), line),
         lambda y: results(y, "나온 것 — 비슷하면서 조건에 맞는 문항 · 소요시간 7.7초",
                           None, cards)])


BUILDERS = {"filter": build_filter, "content": build_content,
            "similar": build_similar, "combo": build_combo}


if __name__ == "__main__":
    for name in sys.argv[1:] or list(BUILDERS):
        path = BUILDERS[name]()
        print(f"  {path.name}  {path.stat().st_size // 1024}KB")
