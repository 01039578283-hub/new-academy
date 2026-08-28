#!/usr/bin/env python3
"""Add page-specific anchor navigation to subject academy detail pages.

Only regional detail pages directly below the eight ``과목별학원`` category
folders are targeted. Category hubs and the top-level subject hub remain
untouched. Existing H2 IDs and visible H2 text are reused, with one stable ID
added to the lead manuscript heading. Visible copy, metadata, images, and
JSON-LD are not rewritten.

Run this idempotent postprocessor again after regenerating subject pages.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBJECT_ROOT = ROOT / "과목별학원"
SUBJECT_CATEGORIES = (
    "고1수학학원",
    "고1영어학원",
    "고2수학학원",
    "고2영어학원",
    "중2수학학원",
    "중2영어학원",
    "중3수학학원",
    "중3영어학원",
)
EXPECTED_PER_CATEGORY = 371
TARGET_IDS = (
    "answer-title",
    "learning-guide-title",
    "local-facts-title",
    "checklist-title",
    "faq-title",
    "related-title",
)

STYLE_MARKER = "<!-- subject-page-anchor-toc:style -->"
STYLE_HREF = "../../../assets/subject-anchor-toc.css"
STYLE_LINK = f'<link rel="stylesheet" href="{STYLE_HREF}">'
TOC_START = "<!-- subject-page-anchor-toc:start -->"
TOC_END = "<!-- subject-page-anchor-toc:end -->"

TOC_BLOCK_RE = re.compile(
    rf"^[ \t]*{re.escape(TOC_START)}\r?\n.*?"
    rf"^[ \t]*{re.escape(TOC_END)}\r?\n",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
TOC_CAPTURE_RE = re.compile(
    rf"{re.escape(TOC_START)}.*?{re.escape(TOC_END)}",
    re.IGNORECASE | re.DOTALL,
)
SITE_CSS_RE = re.compile(
    r'(?P<indent>^[ \t]*)<link\s+rel=["\']stylesheet["\']\s+'
    r'href=["\']\.\./\.\./\.\./assets/site\.css["\']\s*>',
    re.IGNORECASE | re.MULTILINE,
)
STYLE_BLOCK_RE = re.compile(
    rf"^[ \t]*{re.escape(STYLE_MARKER)}\r?\n"
    rf'[ \t]*<link\s+rel=["\']stylesheet["\']\s+'
    rf'href=["\']{re.escape(STYLE_HREF)}["\']\s*>\r?\n?',
    re.IGNORECASE | re.MULTILINE,
)
H2_RE = re.compile(
    r"<h2\b(?P<attrs>[^>]*)>(?P<body>.*?)</h2>",
    re.IGNORECASE | re.DOTALL,
)
ID_RE = re.compile(r'\bid\s*=\s*(["\'])(?P<id>[^"\']+)\1', re.IGNORECASE)
ANY_ID_RE = re.compile(
    r'\bid\s*=\s*(["\'])(?P<id>[^"\']+)\1', re.IGNORECASE
)
ANSWER_SECTION_RE = re.compile(
    r'<section\b[^>]*\baria-labelledby=["\']answer-title["\'][^>]*>',
    re.IGNORECASE,
)
MANUSCRIPT_SECTION_RE = re.compile(
    r'<section\b(?=[^>]*\bclass=["\'][^"\']*\bmanuscript-panel\b[^"\']*["\'])[^>]*>',
    re.IGNORECASE,
)
TOC_LINK_RE = re.compile(
    r'<a href="#(?P<id>[^"]+)">.*?'
    r'<span class="subject-page-toc-text">(?P<label>.*?)</span>\s*</a>',
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class TocTarget:
    target_id: str
    text: str
    position: int


def visible_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return " ".join(html.unescape(text).split())


def detect_newline(source: str) -> str:
    if "\r\n" in source:
        if "\n" in source.replace("\r\n", ""):
            raise ValueError("Mixed newline styles")
        return "\r\n"
    return "\n"


def detail_pages() -> list[Path]:
    result: list[Path] = []
    actual_categories = tuple(
        sorted(path.name for path in SUBJECT_ROOT.iterdir() if path.is_dir())
    )
    if actual_categories != tuple(sorted(SUBJECT_CATEGORIES)):
        raise ValueError(
            "Subject category folders differ from the expected eight: "
            f"{actual_categories}"
        )
    for category in SUBJECT_CATEGORIES:
        pages = sorted(
            (path / "index.html")
            for path in (SUBJECT_ROOT / category).iterdir()
            if path.is_dir() and (path / "index.html").is_file()
        )
        if len(pages) != EXPECTED_PER_CATEGORY:
            raise ValueError(
                f"{category}: expected {EXPECTED_PER_CATEGORY} detail pages, "
                f"found {len(pages)}"
            )
        result.extend(pages)
    return sorted(result, key=lambda path: path.as_posix())


def select_targets(source: str) -> list[TocTarget]:
    found: dict[str, TocTarget] = {}
    for heading in H2_RE.finditer(source):
        id_match = ID_RE.search(heading.group("attrs"))
        if not id_match:
            continue
        target_id = id_match.group("id")
        if target_id not in TARGET_IDS:
            continue
        if target_id in found:
            raise ValueError(f"Duplicate target {target_id}")
        label = visible_text(heading.group("body"))
        if not label:
            raise ValueError(f"Empty H2 target {target_id}")
        found[target_id] = TocTarget(target_id, label, heading.start())

    missing = [target_id for target_id in TARGET_IDS if target_id not in found]
    if missing:
        raise ValueError(f"Missing H2 targets: {missing}")
    targets = [found[target_id] for target_id in TARGET_IDS]
    if [target.position for target in targets] != sorted(
        target.position for target in targets
    ):
        raise ValueError("Target order differs from the expected reading order")
    return targets


def ensure_learning_guide_target(source: str) -> str:
    existing = [
        heading
        for heading in H2_RE.finditer(source)
        if (id_match := ID_RE.search(heading.group("attrs")))
        and id_match.group("id") == "learning-guide-title"
    ]
    manuscripts = list(MANUSCRIPT_SECTION_RE.finditer(source))
    if not manuscripts:
        raise ValueError("Lead manuscript section not found")
    lead_heading = H2_RE.search(source, manuscripts[0].end())
    if not lead_heading:
        raise ValueError("Lead manuscript H2 not found")
    if existing:
        if len(existing) != 1 or existing[0].start() != lead_heading.start():
            raise ValueError("Learning guide target is not on the lead manuscript H2")
        return source
    if ID_RE.search(lead_heading.group("attrs")):
        raise ValueError("Lead manuscript H2 already has another ID")
    replacement = (
        '<h2 id="learning-guide-title"'
        + lead_heading.group("attrs")
        + ">"
        + lead_heading.group("body")
        + "</h2>"
    )
    return source[: lead_heading.start()] + replacement + source[lead_heading.end() :]


def ensure_style_link(source: str, newline: str) -> str:
    if STYLE_MARKER in source:
        if len(STYLE_BLOCK_RE.findall(source)) != 1:
            raise ValueError("Existing TOC stylesheet marker is malformed")
        return source
    matches = list(SITE_CSS_RE.finditer(source))
    if len(matches) != 1:
        raise ValueError(f"Main stylesheet link count is {len(matches)}")
    match = matches[0]
    addition = (
        newline
        + match.group("indent")
        + STYLE_MARKER
        + newline
        + match.group("indent")
        + STYLE_LINK
    )
    return source[: match.end()] + addition + source[match.end() :]


def toc_markup(targets: list[TocTarget], indent: str, newline: str) -> str:
    child = indent + "  "
    grandchild = child + "  "
    item_indent = grandchild + "  "
    lines = [
        indent + TOC_START,
        indent
        + '<nav class="shell subject-page-toc" '
        + 'aria-labelledby="subject-page-toc-title">',
        child + '<div class="subject-page-toc-panel">',
        grandchild + '<div class="subject-page-toc-heading">',
        item_indent + '<p class="eyebrow">PAGE CONTENTS</p>',
        item_indent + '<strong id="subject-page-toc-title">학습 안내 목차</strong>',
        grandchild + "</div>",
        grandchild + '<ol class="subject-page-toc-list">',
    ]
    for index, target in enumerate(targets, start=1):
        lines.append(
            item_indent
            + "<li>"
            + f'<a href="#{html.escape(target.target_id, quote=True)}">'
            + f'<span class="subject-page-toc-number" aria-hidden="true">{index:02d}</span>'
            + f'<span class="subject-page-toc-text">{html.escape(target.text)}</span>'
            + "</a></li>"
        )
    lines.extend(
        [
            grandchild + "</ol>",
            child + "</div>",
            indent + "</nav>",
            indent + TOC_END,
        ]
    )
    return newline.join(lines) + newline


def render_page(original: str) -> tuple[str, int]:
    if original.count(TOC_START) != original.count(TOC_END):
        raise ValueError("Unbalanced TOC markers")
    if original.count(TOC_START) > 1:
        raise ValueError("Multiple TOC blocks found")
    source = TOC_BLOCK_RE.sub("", original, count=1)
    newline = detect_newline(source)
    source = ensure_style_link(source, newline)
    source = ensure_learning_guide_target(source)
    targets = select_targets(source)
    answer_sections = list(ANSWER_SECTION_RE.finditer(source))
    if len(answer_sections) != 1:
        raise ValueError(f"Answer section count is {len(answer_sections)}")
    insertion_point = answer_sections[0].start()
    line_start = source.rfind(newline, 0, insertion_point) + len(newline)
    indent = source[line_start:insertion_point]
    if indent.strip():
        raise ValueError("Answer section does not start on its own line")
    rendered = (
        source[:line_start]
        + toc_markup(targets, indent, newline)
        + source[line_start:]
    )
    return rendered, len(targets)


def validate_page(source: str) -> list[str]:
    errors: list[str] = []
    if source.count(STYLE_MARKER) != 1 or source.count(STYLE_HREF) != 1:
        errors.append("TOC stylesheet marker or link count is not exactly one")
    if source.count(TOC_START) != 1 or source.count(TOC_END) != 1:
        errors.append("TOC marker count is not exactly one")
    toc = TOC_CAPTURE_RE.search(source)
    if not toc:
        errors.append("TOC block missing")
        return errors

    try:
        targets = select_targets(source)
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))
        return errors
    expected = [(target.target_id, target.text) for target in targets]
    links = [
        (match.group("id"), visible_text(match.group("label")))
        for match in TOC_LINK_RE.finditer(toc.group(0))
    ]
    if links != expected:
        errors.append("TOC links or labels do not match visible H2 headings")

    all_ids = [match.group("id") for match in ANY_ID_RE.finditer(source)]
    duplicate_ids = sorted(
        target_id
        for target_id, count in Counter(all_ids).items()
        if count > 1
    )
    if duplicate_ids:
        errors.append(f"Duplicate IDs found: {duplicate_ids}")
    if all_ids.count("subject-page-toc-title") != 1:
        errors.append("TOC title ID count is not exactly one")
    for target_id, _ in links:
        if all_ids.count(target_id) != 1:
            errors.append(
                f"Anchor target count for {target_id!r} is "
                f"{all_ids.count(target_id)}"
            )

    answer_section = ANSWER_SECTION_RE.search(source)
    if not answer_section or toc.end() > answer_section.start():
        errors.append("TOC is not immediately before the answer section")
    elif source[toc.end() : answer_section.start()].strip():
        errors.append("Unexpected content appears between TOC and answer section")
    return errors


def validate_hubs() -> list[str]:
    hubs = [SUBJECT_ROOT / "index.html"] + [
        SUBJECT_ROOT / category / "index.html" for category in SUBJECT_CATEGORIES
    ]
    errors: list[str] = []
    for hub in hubs:
        source = hub.read_text(encoding="utf-8")
        if STYLE_MARKER in source or TOC_START in source or TOC_END in source:
            errors.append(
                f"Hub unexpectedly contains a subject detail TOC: "
                f"{hub.relative_to(ROOT).as_posix()}"
            )
    return errors


def process(write: bool) -> int:
    try:
        pages = detail_pages()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR {exc}")
        return 1

    changed = 0
    validated = 0
    distribution: Counter[int] = Counter()
    categories: Counter[str] = Counter()
    failures: list[str] = []

    for path in pages:
        try:
            raw = path.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf"):
                raise ValueError("UTF-8 BOM is not supported")
            original = raw.decode("utf-8")
            rendered, target_count = render_page(original)
            page_errors = validate_page(rendered)
            if page_errors:
                raise ValueError("; ".join(page_errors))
            if rendered != original:
                changed += 1
                if write:
                    path.write_bytes(rendered.encode("utf-8"))
            distribution[target_count] += 1
            categories[path.relative_to(SUBJECT_ROOT).parts[0]] += 1
            validated += 1
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{path.relative_to(ROOT).as_posix()}: {exc}")

    failures.extend(validate_hubs())
    print(f"pages={len(pages)} validated={validated}")
    print(
        "toc_link_distribution="
        + ",".join(
            f"{count}:{page_count}"
            for count, page_count in sorted(distribution.items())
        )
    )
    print(
        "toc_links_total="
        + str(sum(count * page_count for count, page_count in distribution.items()))
    )
    print(
        "categories="
        + ",".join(f"{name}:{count}" for name, count in sorted(categories.items()))
    )
    print(f"changed={changed} mode={'write' if write else 'check'}")
    for failure in failures[:50]:
        print("ERROR", failure)
    if len(failures) > 50:
        print(f"ERROR ... and {len(failures) - 50} more")
    if not write and changed:
        print("ERROR check mode found pages that need updating")
        return 1
    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Apply or refresh TOCs")
    mode.add_argument("--check", action="store_true", help="Validate idempotence")
    args = parser.parse_args()
    raise SystemExit(process(write=args.write))


if __name__ == "__main__":
    main()
