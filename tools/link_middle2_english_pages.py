from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote

import generate_middle2_math_pages as base


SITE = base.SITE
TARGET_ROOT = SITE / "과목별학원" / "중2영어학원"


def relative_href(source: Path, target: Path) -> str:
    relative = Path(os.path.relpath(target, source.parent))
    return "/".join(quote(part, safe="") for part in relative.parts)


def add_visible_link(page: Path, target: Path, label: str) -> bool:
    text = page.read_text(encoding="utf-8")
    href = relative_href(page, target)
    if href in text or "/중2영어학원/" in text:
        return False
    marker = re.search(r'<div class="child-button-grid"[^>]*>', text)
    if not marker:
        raise ValueError(f"내부링크 그리드 없음: {page}")
    anchor = f'<a class="child-page-button" href="{href}">{base.esc(label)}</a>'
    text = text[: marker.end()] + anchor + text[marker.end() :]
    page.write_text(text, encoding="utf-8", newline="\n")
    return True


def main() -> None:
    rows = base.read_csv(base.CENTER_CSV)
    counts = {"parent": 0, "middle1_english": 0, "middle2_math": 0}
    for row in rows:
        local = base.row_value(row, "근처 수업가능 동네")
        parent = base.find_parent_page(row)
        if parent is None:
            raise FileNotFoundError(f"전국학원 부모페이지 없음: {local}")
        target = TARGET_ROOT / local / "index.html"
        if not target.exists():
            raise FileNotFoundError(f"중2 영어 페이지 없음: {local}")
        if add_visible_link(parent, target, f"{local} 중2 영어학원"):
            counts["parent"] += 1
        middle1 = parent.parent / "중1영어학원" / "index.html"
        if add_visible_link(middle1, target, f"{local} 중2 영어학원"):
            counts["middle1_english"] += 1
        math_page = SITE / "과목별학원" / "중2수학학원" / local / "index.html"
        if add_visible_link(math_page, target, f"{local} 중2 영어학원"):
            counts["middle2_math"] += 1
    print(" ".join(f"{key}={value}" for key, value in counts.items()))


if __name__ == "__main__":
    main()
