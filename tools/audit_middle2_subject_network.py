from __future__ import annotations

import csv
import html
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit
from xml.etree import ElementTree


SITE = Path(__file__).resolve().parents[1]
CENTER_CSV = SITE.parent / "참고자료" / "공통자료" / "센터정보 정리.csv"
SUBJECT_ROOT = SITE / "과목별학원"
SITEMAP = SITE / "sitemap.xml"
DOMAIN = "https://xn--z92bu9jx8cwzc.com"
SUBJECT_SEGMENT = "과목별학원"
CATEGORIES = {
    "중2수학학원": "중2 수학학원",
    "중2영어학원": "중2 영어학원",
}
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def row_value(row: dict[str, str], needle: str) -> str:
    for key, value in row.items():
        if needle in key:
            return (value or "").strip()
    return ""


def normalize_url(value: str, base: str | None = None) -> str:
    absolute = urljoin(base, value) if base else value
    parts = urlsplit(absolute)
    host = (parts.hostname or "").encode("idna").decode("ascii").lower()
    if parts.port:
        host = f"{host}:{parts.port}"
    path = unquote(parts.path or "/")
    path = re.sub(r"/{2,}", "/", path)
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    tail = path.rsplit("/", 1)[-1]
    if not path.endswith("/") and "." not in tail:
        path += "/"
    return urlunsplit(((parts.scheme or "https").lower(), host, path, "", ""))


def canonical_url(category: str, local: str | None = None) -> str:
    segments = [SUBJECT_SEGMENT, category]
    if local:
        segments.append(local)
    path = "/" + "/".join(segments) + "/"
    return DOMAIN + quote(path, safe="/")


def page_url(page: Path) -> str:
    relative = page.parent.relative_to(SITE)
    if not relative.parts:
        return f"{DOMAIN}/"
    return DOMAIN + quote("/" + relative.as_posix() + "/", safe="/")


def subject_local_path(value: str) -> Path | None:
    normalized = normalize_url(value)
    parts = urlsplit(normalized)
    if parts.netloc != urlsplit(DOMAIN).netloc:
        return None
    decoded = unquote(parts.path)
    segments = [part for part in PurePosixPath(decoded).parts if part not in {"/", ""}]
    if not segments or segments[0] != SUBJECT_SEGMENT:
        return None
    if decoded.endswith("/"):
        segments.append("index.html")
    candidate = SITE.joinpath(*segments).resolve()
    try:
        candidate.relative_to(SITE.resolve())
    except ValueError:
        return None
    return candidate


@dataclass
class ParsedPage:
    h1: list[str] = field(default_factory=list)
    canonical: list[str] = field(default_factory=list)
    og_url: list[str] = field(default_factory=list)
    anchors: list[str] = field(default_factory=list)
    related_anchors: list[str] = field(default_factory=list)
    faq: list[tuple[str, str]] = field(default_factory=list)
    json_documents: list[object] = field(default_factory=list)
    json_errors: list[str] = field(default_factory=list)


class SubjectPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.result = ParsedPage()
        self.stack: list[str] = []
        self.h1_depth: int | None = None
        self.h1_buffer: list[str] = []
        self.related_marker: tuple[str, int] | None = None
        self.faq_marker: tuple[str, int] | None = None
        self.detail_depth: int | None = None
        self.summary_depth: int | None = None
        self.answer_depth: int | None = None
        self.question_buffer: list[str] = []
        self.answer_buffer: list[str] = []
        self.script_depth: int | None = None
        self.script_buffer: list[str] = []

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key.lower(): value or "" for key, value in attrs}

    def _inside(self, marker: tuple[str, int] | None) -> bool:
        return marker is not None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr = self._attrs(attrs)
        classes = set(attr.get("class", "").split())
        depth = len(self.stack)

        if "local-page-nav" in classes:
            self.related_marker = (tag, depth)
        if "local-faq-card" in classes:
            self.faq_marker = (tag, depth)

        if tag == "h1":
            self.h1_depth = depth
            self.h1_buffer = []
        elif tag == "link" and "canonical" in attr.get("rel", "").lower().split():
            self.result.canonical.append(attr.get("href", ""))
        elif tag == "meta" and attr.get("property", "").lower() == "og:url":
            self.result.og_url.append(attr.get("content", ""))
        elif tag == "a":
            href = attr.get("href", "")
            if href:
                self.result.anchors.append(href)
                if self._inside(self.related_marker):
                    self.result.related_anchors.append(href)
        elif tag == "details" and self._inside(self.faq_marker):
            self.detail_depth = depth
            self.question_buffer = []
            self.answer_buffer = []
        elif tag == "summary" and self.detail_depth is not None:
            self.summary_depth = depth
        elif tag == "p" and self.detail_depth is not None and self.answer_depth is None:
            self.answer_depth = depth
        elif tag == "script" and attr.get("type", "").lower() == "application/ld+json":
            self.script_depth = depth
            self.script_buffer = []

        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_data(self, data: str) -> None:
        if self.h1_depth is not None:
            self.h1_buffer.append(data)
        if self.summary_depth is not None:
            self.question_buffer.append(data)
        if self.answer_depth is not None:
            self.answer_buffer.append(data)
        if self.script_depth is not None:
            self.script_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        depth = len(self.stack) - 1

        if tag == "h1" and self.h1_depth is not None:
            self.result.h1.append(clean_text("".join(self.h1_buffer)))
            self.h1_depth = None
            self.h1_buffer = []
        elif tag == "summary" and self.summary_depth is not None:
            self.summary_depth = None
        elif tag == "p" and self.answer_depth is not None:
            self.answer_depth = None
        elif tag == "details" and self.detail_depth is not None:
            self.result.faq.append(
                (
                    clean_text("".join(self.question_buffer)),
                    clean_text("".join(self.answer_buffer)),
                )
            )
            self.detail_depth = None
            self.summary_depth = None
            self.answer_depth = None
            self.question_buffer = []
            self.answer_buffer = []
        elif tag == "script" and self.script_depth is not None:
            raw = "".join(self.script_buffer).strip()
            try:
                self.result.json_documents.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                self.result.json_errors.append(str(exc))
            self.script_depth = None
            self.script_buffer = []

        if self.related_marker == (tag, depth):
            self.related_marker = None
        if self.faq_marker == (tag, depth):
            self.faq_marker = None

        if self.stack:
            if self.stack[-1] == tag:
                self.stack.pop()
            elif tag in self.stack:
                position = len(self.stack) - 1 - self.stack[::-1].index(tag)
                del self.stack[position:]


def parse_page(path: Path) -> ParsedPage:
    parser = SubjectPageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser.result


def schema_nodes(documents: list[object]) -> list[dict[str, object]]:
    nodes: list[dict[str, object]] = []
    for document in documents:
        if isinstance(document, dict) and isinstance(document.get("@graph"), list):
            nodes.extend(node for node in document["@graph"] if isinstance(node, dict))
        elif isinstance(document, list):
            nodes.extend(node for node in document if isinstance(node, dict))
        elif isinstance(document, dict):
            nodes.append(document)
    return nodes


def has_type(node: dict[str, object], expected: str) -> bool:
    value = node.get("@type")
    if isinstance(value, str):
        return value == expected
    return isinstance(value, list) and expected in value


def faq_from_schema(node: dict[str, object]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    entities = node.get("mainEntity")
    if not isinstance(entities, list):
        return result
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        answer = entity.get("acceptedAnswer")
        if isinstance(answer, list):
            answer = answer[0] if answer else {}
        answer_text = answer.get("text", "") if isinstance(answer, dict) else ""
        result.append((clean_text(str(entity.get("name", ""))), clean_text(str(answer_text))))
    return result


def related_urls_from_schema(node: dict[str, object]) -> list[str]:
    result: list[str] = []
    items = node.get("itemListElement")
    if not isinstance(items, list):
        return result
    for item in items:
        if not isinstance(item, dict):
            continue
        target = item.get("url") or item.get("item")
        if isinstance(target, dict):
            target = target.get("@id") or target.get("url")
        if isinstance(target, str) and target:
            result.append(target)
    return result


def load_locals(errors: list[str]) -> list[str]:
    if not CENTER_CSV.exists():
        errors.append(f"센터 CSV 없음: {CENTER_CSV}")
        return []
    with CENTER_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    locals_ = [row_value(row, "근처 수업가능 동네") for row in rows]
    if len(locals_) != 371:
        errors.append(f"센터 CSV 행 수: 기대 371, 실제 {len(locals_)}")
    if any(not local for local in locals_):
        errors.append("센터 CSV에 빈 동네명이 있습니다.")
    if len(set(locals_)) != len(locals_):
        duplicates = [name for name, count in Counter(locals_).items() if count > 1]
        errors.append(f"센터 CSV 동네명 중복: {duplicates}")
    return locals_


def read_sitemap(errors: list[str]) -> list[str]:
    if not SITEMAP.exists():
        errors.append(f"사이트맵 없음: {SITEMAP}")
        return []
    try:
        root = ElementTree.parse(SITEMAP).getroot()
    except ElementTree.ParseError as exc:
        errors.append(f"사이트맵 XML 오류: {exc}")
        return []
    return [clean_text(node.text or "") for node in root.findall(".//{*}loc")]


def main() -> int:
    errors: list[str] = []
    locals_ = load_locals(errors)
    expected: dict[str, tuple[str, str, Path]] = {}
    category_urls: dict[str, set[str]] = {}

    for category, label in CATEGORIES.items():
        category_root = SUBJECT_ROOT / category
        actual_dirs = {
            path.name
            for path in category_root.iterdir()
            if path.is_dir() and (path / "index.html").exists()
        } if category_root.exists() else set()
        if actual_dirs != set(locals_):
            missing = sorted(set(locals_) - actual_dirs)
            extra = sorted(actual_dirs - set(locals_))
            errors.append(
                f"{category} 지역 폴더 불일치: 누락 {len(missing)} {missing[:5]}, "
                f"추가 {len(extra)} {extra[:5]}"
            )
        urls: set[str] = set()
        for local in locals_:
            url = normalize_url(canonical_url(category, local))
            path = category_root / local / "index.html"
            expected[url] = (category, local, path)
            urls.add(url)
        category_urls[category] = urls

    if len(expected) != 742:
        errors.append(f"기대 상세 URL 수: 742, 실제 {len(expected)}")

    parsed: dict[str, ParsedPage] = {}
    peer_links: dict[str, set[str]] = defaultdict(set)
    related_links: dict[str, list[str]] = {}
    faq_counts: list[int] = []

    for url, (category, local, path) in expected.items():
        if not path.exists():
            errors.append(f"페이지 없음: {path}")
            continue
        page = parse_page(path)
        parsed[url] = page
        expected_title = f"{local} {CATEGORIES[category]}"

        if page.h1 != [expected_title]:
            errors.append(f"H1 오류 {url}: {page.h1!r}, 기대 {[expected_title]!r}")

        canonical_values = [normalize_url(value, url) for value in page.canonical if value]
        if canonical_values != [url]:
            errors.append(f"canonical 오류 {url}: {canonical_values!r}")
        og_values = [normalize_url(value, url) for value in page.og_url if value]
        if og_values != [url]:
            errors.append(f"og:url 오류 {url}: {og_values!r}")

        if page.json_errors:
            errors.append(f"JSON-LD 파싱 오류 {url}: {page.json_errors}")
        nodes = schema_nodes(page.json_documents)
        faq_nodes = [node for node in nodes if has_type(node, "FAQPage")]
        if len(faq_nodes) != 1:
            errors.append(f"FAQPage 개수 오류 {url}: {len(faq_nodes)}")
            schema_faq: list[tuple[str, str]] = []
        else:
            schema_faq = faq_from_schema(faq_nodes[0])
        faq_counts.append(len(page.faq))
        if not 6 <= len(page.faq) <= 8:
            errors.append(f"화면 FAQ 개수 오류 {url}: {len(page.faq)} (기대 6~8)")
        if page.faq != schema_faq:
            errors.append(f"화면/FAQPage 불일치 {url}: 화면 {len(page.faq)}, JSON-LD {len(schema_faq)}")

        related_nodes = [
            node
            for node in nodes
            if has_type(node, "ItemList")
            and str(node.get("@id", "")).endswith("#related-pages")
        ]
        if len(related_nodes) != 1:
            errors.append(f"관련 ItemList 개수 오류 {url}: {len(related_nodes)}")
            schema_related: list[str] = []
        else:
            schema_related = [normalize_url(value, url) for value in related_urls_from_schema(related_nodes[0])]
        visible_related = [normalize_url(value, url) for value in page.related_anchors]
        related_links[url] = visible_related
        if visible_related != schema_related:
            errors.append(
                f"화면/관련 ItemList URL 불일치 {url}: 화면 {len(visible_related)}, "
                f"JSON-LD {len(schema_related)}"
            )
        if len(visible_related) != len(set(visible_related)):
            errors.append(f"화면 관련 링크 중복 {url}")

        for href in page.anchors:
            target = normalize_url(href, url)
            target_path = subject_local_path(target)
            if target_path is not None and not target_path.exists():
                errors.append(f"과목별 정적 내부링크 대상 없음 {url} -> {target}")

        for target in set(visible_related):
            if target != url and target in category_urls[category]:
                peer_links[url].add(target)
        if len(peer_links[url]) < 6:
            errors.append(f"같은 카테고리 peer 부족 {url}: {len(peer_links[url])}개")

    for source, targets in peer_links.items():
        for target in targets:
            if source not in peer_links.get(target, set()):
                errors.append(f"peer 비대칭: {source} -> {target}")

    inbound: dict[str, set[str]] = defaultdict(set)
    if SUBJECT_ROOT.exists():
        for source_path in SUBJECT_ROOT.rglob("index.html"):
            source = normalize_url(page_url(source_path))
            source_page = parsed.get(source) or parse_page(source_path)
            for href in source_page.anchors:
                target = normalize_url(href, source)
                if target in expected and target != source:
                    inbound[target].add(source)

    inbound_counts: list[int] = []
    for url in expected:
        count = len(inbound.get(url, set()))
        inbound_counts.append(count)
        if count < 8:
            errors.append(f"과목별학원 내부 유입 부족 {url}: {count}개")

    sitemap_values = read_sitemap(errors)
    normalized_sitemap = [normalize_url(value) for value in sitemap_values if value]
    sitemap_counts = Counter(normalized_sitemap)
    duplicate_sitemap = sorted(url for url, count in sitemap_counts.items() if count > 1)
    if duplicate_sitemap:
        errors.append(f"사이트맵 중복 URL: {len(duplicate_sitemap)}개, 예시 {duplicate_sitemap[:5]}")
    sitemap_set = set(normalized_sitemap)
    missing_sitemap = sorted(set(expected) - sitemap_set)
    if missing_sitemap:
        errors.append(f"사이트맵 상세 URL 누락: {len(missing_sitemap)}개, 예시 {missing_sitemap[:5]}")

    print(f"DETAIL_EXPECTED={len(expected)}")
    print(f"DETAIL_PARSED={len(parsed)}")
    print(f"SUBJECT_HTML_SCANNED={len(list(SUBJECT_ROOT.rglob('index.html'))) if SUBJECT_ROOT.exists() else 0}")
    if faq_counts:
        print(f"FAQ_MIN={min(faq_counts)} FAQ_MAX={max(faq_counts)}")
    peer_counts = [len(peer_links.get(url, set())) for url in expected]
    if peer_counts:
        print(
            f"PEER_MIN={min(peer_counts)} PEER_AVG={statistics.mean(peer_counts):.3f} "
            f"PEER_MAX={max(peer_counts)}"
        )
    if inbound_counts:
        print(
            f"SUBJECT_INBOUND_MIN={min(inbound_counts)} "
            f"SUBJECT_INBOUND_AVG={statistics.mean(inbound_counts):.3f} "
            f"SUBJECT_INBOUND_MAX={max(inbound_counts)}"
        )
    print(f"SITEMAP_URLS={len(normalized_sitemap)}")
    print(f"SITEMAP_DUPLICATES={len(duplicate_sitemap)}")
    print(f"ERRORS={len(errors)}")

    if errors:
        limit = 100
        for message in errors[:limit]:
            print(f"ERROR: {message}")
        if len(errors) > limit:
            print(f"ERROR: ... 나머지 {len(errors) - limit}개 오류 생략")
        return 1
    print("AUDIT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
