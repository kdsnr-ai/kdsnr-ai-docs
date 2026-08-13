import re
import subprocess
import sys
from pathlib import Path

INDEX = Path("research/index.html")
CARD = re.compile(r'<a class="card"([^>]*?)href="([^"]+)"([^>]*)>')


def commit_dates(path):
    result = subprocess.run(
        ["git", "log", "--format=%cs", "--", str(path)],
        capture_output=True,
        text=True,
    )
    dates = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not dates:
        return "", ""
    return dates[-1], dates[0]


def stamp(match):
    before, href, after = match.group(1), match.group(2), match.group(3)
    target = INDEX.parent / href
    if not target.exists():
        return match.group(0)
    created, updated = commit_dates(target)
    if not created:
        return match.group(0)
    strip = lambda text: re.sub(r'\s*data-(created|updated)="[^"]*"', "", text)
    print(f"{href} 처음 {created} 마지막 {updated}")
    return f'<a class="card"{strip(before)}href="{href}"{strip(after)} data-created="{created}" data-updated="{updated}">'


def main():
    html = INDEX.read_text()
    stamped = CARD.sub(stamp, html)
    if stamped == html:
        print("바뀐 카드가 없습니다")
        return 0
    INDEX.write_text(stamped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
