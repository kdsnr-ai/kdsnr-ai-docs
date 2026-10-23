import re
import subprocess
import sys
from pathlib import Path

INDEX = Path("research/index.html")
CARD = re.compile(r'<a class="card"([^>]*?)href="([^"]+)"([^>]*)>')
ASSET_VERSION = re.compile(r'^<(script|link)\b[^>]*\?v=[^>]*>(</script>)?$')


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def only_asset_versions(sha, path):
    lines = [
        line
        for line in git("show", "--format=", "-U0", sha, "--", str(path)).splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]
    changed = [line[1:].strip() for line in lines]
    if not changed:
        return False
    if all(ASSET_VERSION.match(line) for line in changed):
        return True
    removed = {re.sub(r"\.(png|jpg)\b", ".webp", line[1:]) for line in lines if line[0] == "-"}
    added = {line[1:] for line in lines if line[0] == "+"}
    return removed == added


def commit_dates(path):
    commits = [line.split() for line in git("log", "--format=%H %cs", "--", str(path)).splitlines() if line.strip()]
    if not commits:
        return "", ""
    created = commits[-1][1]
    updated = next((date for sha, date in commits if not only_asset_versions(sha, path)), created)
    return created, updated


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
