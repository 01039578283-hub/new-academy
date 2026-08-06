from __future__ import annotations

import csv
import html as html_lib
import json
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "참고자료" / "공통자료" / "센터정보 정리.csv"
SUBJECT_ROOT = ROOT / "과목별학원"
HUB = SUBJECT_ROOT / "중3수학학원"
MIDDLE2_HUB = SUBJECT_ROOT / "중2수학학원"
SITEMAP = ROOT / "sitemap.xml"
DOMAIN = "https://xn--z92bu9jx8cwzc.com"
CATEGORY = "중3수학학원"
CATEGORY_LABEL = "중3 수학학원"
SITE_NAME = "와와센터"
REQUIRED_TYPES = {
    "EducationalOrganization",
    "LocalBusiness",
    "Article",
    "Service",
    "FAQPage",
    "BreadcrumbList",
    "ItemList",
}
FORBIDDEN_SCHEMA_TYPES = {"Review", "AggregateRating"}
FORBIDDEN_PATTERNS = {
    "교차과목": re.compile(r"영어|국어|영수|국영수"),
    "근거 없는 성과·점수 보장": re.compile(
        r"(?:"
        r"(?:성적|점수|등급|합격)[^.!?<>]{0,35}(?:보장|상승|향상|오르|올리|끌어올리|완성|달성|연결)|"
        r"(?:보장|상승|향상|오르|올리|끌어올리)[^.!?<>]{0,25}(?:성적|점수|등급|합격)|"
        r"100\s*%|전교\s*1등|단기간\s*(?:성적|점수)|바로\s*(?:성적|점수)|"
        r"무조건\s*(?:성적|점수|등급|합격)|최고의\s*(?:학원|수업|강사진)|유일한\s*(?:학원|수업)"
        r")",
    ),
    "근거 없는 출제 단정": re.compile(
        r"(?:학교별|지역\s*학생들의?)[^.!?<>]{0,35}(?:출제\s*(?:흐름|경향)|시험\s*범위)[^.!?<>]{0,35}(?:맞춰|반영|분석|대비)|"
        r"출제\s*(?:흐름|경향)[^.!?<>]{0,25}(?:정확|완벽|반드시)"
    ),
}


def row_value(row: dict[str, str], needle: str) -> str:
    for key, value in row.items():
        if needle in key:
            return (value or "").strip()
    return ""


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(value or "")).strip()


def strip_tags(value: str) -> str:
    value = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", value, flags=re.I | re.S)
    return clean_text(re.sub(r"<[^>]+>", " ", value))


def attrs(tag: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, _quote, value in re.findall(r"([:\w-]+)\s*=\s*([\"'])(.*?)\2", tag, flags=re.S):
        result[name.lower()] = html_lib.unescape(value)
    return result


def first_match(pattern: str, text: str, flags: int = 0) -> str:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else ""


def canonical(local: str | None = None) -> str:
    parts = ["과목별학원", CATEGORY]
    if local:
        parts.append(local)
    return DOMAIN + "/" + "/".join(quote(part, safe="") for part in parts) + "/"


def middle2_canonical(local: str) -> str:
    parts = ["과목별학원", "중2수학학원", local]
    return DOMAIN + "/" + "/".join(quote(part, safe="") for part in parts) + "/"


def normalize_url(value: str, base: str | None = None) -> str:
    absolute = urljoin(base, value) if base else value
    parts = urlsplit(html_lib.unescape(absolute))
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


def page_url(page: Path) -> str:
    relative = page.parent.relative_to(ROOT)
    return DOMAIN + quote("/" + relative.as_posix() + "/", safe="/")


def local_path_from_url(value: str) -> Path | None:
    normalized = normalize_url(value)
    split = urlsplit(normalized)
    if split.netloc != urlsplit(DOMAIN).netloc:
        return None
    decoded = unquote(split.path)
    segments = [part for part in PurePosixPath(decoded).parts if part not in {"", "/"}]
    if decoded.endswith("/"):
        segments.append("index.html")
    if not segments:
        segments = ["index.html"]
    candidate = ROOT.joinpath(*segments).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def meta_value(text: str, key: str, attribute: str = "name") -> list[str]:
    values: list[str] = []
    for tag in re.findall(r"<meta\b[^>]*>", text, flags=re.I):
        data = attrs(tag)
        if data.get(attribute, "").lower() == key.lower():
            values.append(data.get("content", ""))
    return values


def canonical_values(text: str) -> list[str]:
    values: list[str] = []
    for tag in re.findall(r"<link\b[^>]*>", text, flags=re.I):
        data = attrs(tag)
        if "canonical" in data.get("rel", "").lower().split():
            values.append(data.get("href", ""))
    return values


def json_ld_blocks(text: str) -> tuple[list[object], list[str]]:
    blocks: list[object] = []
    errors: list[str] = []
    for raw in re.findall(
        r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        text,
        flags=re.I | re.S,
    ):
        try:
            blocks.append(json.loads(html_lib.unescape(raw.strip())))
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
    return blocks, errors


def walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def has_type(node: dict, expected: str) -> bool:
    value = node.get("@type")
    return value == expected or isinstance(value, list) and expected in value


def typed_nodes(blocks: list[object], expected: str) -> list[dict]:
    return [node for block in blocks for node in walk_json(block) if has_type(node, expected)]


def json_types(blocks: list[object]) -> set[str]:
    found: set[str] = set()
    for block in blocks:
        for node in walk_json(block):
            value = node.get("@type")
            if isinstance(value, str):
                found.add(value)
            elif isinstance(value, list):
                found.update(item for item in value if isinstance(item, str))
    return found


def visible_faq(text: str) -> list[tuple[str, str]]:
    section = first_match(
        r"<section\b[^>]*class=[\"'][^\"']*local-faq-card[^\"']*[\"'][^>]*>(.*?)</section>",
        text,
        re.I | re.S,
    )
    result: list[tuple[str, str]] = []
    for detail in re.findall(r"<details\b[^>]*>(.*?)</details>", section, flags=re.I | re.S):
        question = strip_tags(first_match(r"<summary\b[^>]*>(.*?)</summary>", detail, re.I | re.S))
        answer = strip_tags(first_match(r"<p\b[^>]*>(.*?)</p>", detail, re.I | re.S))
        result.append((question, answer))
    return result


def json_faq(node: dict) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    entities = node.get("mainEntity", [])
    if not isinstance(entities, list):
        return result
    for item in entities:
        if not isinstance(item, dict):
            continue
        answer = item.get("acceptedAnswer", {})
        if isinstance(answer, list):
            answer = answer[0] if answer else {}
        result.append(
            (
                clean_text(str(item.get("name", ""))),
                clean_text(str(answer.get("text", "") if isinstance(answer, dict) else "")),
            )
        )
    return result


def breadcrumb_labels(text: str) -> list[str]:
    content = first_match(
        r"<nav\b[^>]*class=[\"'][^\"']*breadcrumb-box[^\"']*[\"'][^>]*>(.*?)</nav>",
        text,
        re.I | re.S,
    )
    return [part.strip() for part in strip_tags(content).split("›") if part.strip()]


def json_breadcrumb(node: dict) -> tuple[list[str], list[str]]:
    labels: list[str] = []
    urls: list[str] = []
    items = node.get("itemListElement", [])
    if not isinstance(items, list):
        return labels, urls
    for item in items:
        if not isinstance(item, dict):
            continue
        labels.append(clean_text(str(item.get("name", ""))))
        target = item.get("item") or item.get("url")
        if isinstance(target, dict):
            target = target.get("@id") or target.get("url")
        urls.append(str(target or ""))
    return labels, urls


def section_html(text: str, class_name: str) -> str:
    return first_match(
        rf"<section\b[^>]*class=[\"'][^\"']*{re.escape(class_name)}[^\"']*[\"'][^>]*>(.*?)</section>",
        text,
        re.I | re.S,
    )


def visible_related_urls(text: str, base: str) -> list[str]:
    section = section_html(text, "local-page-nav")
    values: list[str] = []
    for tag in re.findall(r"<a\b[^>]*>", section, flags=re.I | re.S):
        href = attrs(tag).get("href", "")
        if href:
            values.append(normalize_url(href, base))
    return values


def itemlist_urls(node: dict, base: str) -> list[str]:
    values: list[str] = []
    items = node.get("itemListElement", [])
    if not isinstance(items, list):
        return values
    for item in items:
        if not isinstance(item, dict):
            continue
        target = item.get("url") or item.get("item")
        if isinstance(target, dict):
            target = target.get("@id") or target.get("url")
        if isinstance(target, str) and target:
            values.append(normalize_url(target, base))
    return values


def manuscript_html(text: str) -> str:
    return first_match(
        r"<section\b[^>]*class=[\"'][^\"']*manuscript-panel[^\"']*[\"'][^>]*>(.*?)"
        r"</section>\s*<section\b[^>]*class=[\"'][^\"']*subject-local-facts",
        text,
        re.I | re.S,
    )


def checklist_fingerprint(text: str) -> str:
    section = section_html(text, "geo-checklist-panel")
    cards = [
        strip_tags(card)
        for card in re.findall(
            r"<article\b[^>]*class=[\"'][^\"']*geo-check-card[^\"']*[\"'][^>]*>(.*?)</article>",
            section,
            flags=re.I | re.S,
        )
    ]
    return " | ".join(cards)


def neutralize(value: str, row: dict[str, str]) -> str:
    candidates = [
        row_value(row, "근처 수업가능 동네"),
        row_value(row, "센터명"),
        row_value(row, "시or구"),
        row_value(row, "지역"),
        row_value(row, "센터 주소"),
    ]
    normalized = clean_text(value)
    for candidate in sorted({item for item in candidates if item}, key=len, reverse=True):
        normalized = normalized.replace(candidate, "<LOCAL_FACT>")
    normalized = re.sub(r"\d+(?:[-~–]\d+)*", "<NUM>", normalized)
    return normalized


def shingles(value: str, size: int = 5) -> set[tuple[str, ...]]:
    words = re.findall(r"[가-힣A-Za-z0-9]+", value.lower())
    return {tuple(words[index : index + size]) for index in range(max(0, len(words) - size + 1))}


def all_anchor_urls(text: str, base: str) -> list[str]:
    values: list[str] = []
    for tag in re.findall(r"<a\b[^>]*>", text, flags=re.I | re.S):
        href = attrs(tag).get("href", "")
        if not href or href.startswith(("#", "tel:", "mailto:", "javascript:")):
            continue
        values.append(normalize_url(href, base))
    return values


def check_page_head(text: str, expected_title: str, expected_url: str, errors: list[str], label: str) -> None:
    h1_values = [strip_tags(value) for value in re.findall(r"<h1\b[^>]*>(.*?)</h1>", text, flags=re.I | re.S)]
    if h1_values != [expected_title]:
        errors.append(f"{label}: H1 불일치/중복 ({h1_values})")
    canonical_urls = [normalize_url(value, expected_url) for value in canonical_values(text) if value]
    if canonical_urls != [normalize_url(expected_url)]:
        errors.append(f"{label}: canonical 불일치 ({canonical_urls})")
    og_urls = [normalize_url(value, expected_url) for value in meta_value(text, "og:url", "property") if value]
    if og_urls != [normalize_url(expected_url)]:
        errors.append(f"{label}: og:url 불일치 ({og_urls})")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    if not DATA.exists():
        print(f"ERROR: 센터 CSV 없음: {DATA}")
        return 1
    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    locals_ = [row_value(row, "근처 수업가능 동네") for row in rows]
    row_by_local = {row_value(row, "근처 수업가능 동네"): row for row in rows}
    if len(locals_) != 371 or len(set(locals_)) != 371 or any(not local for local in locals_):
        errors.append(f"센터 CSV 동네 집합 오류: 전체 {len(locals_)}, 고유 {len(set(locals_))}")

    expected_urls = {normalize_url(canonical(local)) for local in locals_}
    page_by_url = {normalize_url(canonical(local)): HUB / local / "index.html" for local in locals_}

    if not HUB.exists():
        errors.append(f"중3 수학 허브 폴더 없음: {HUB}")
        hub_text = ""
        actual_dirs: set[str] = set()
    else:
        actual_dirs = {
            path.name
            for path in HUB.iterdir()
            if path.is_dir() and (path / "index.html").exists()
        }
        hub_file = HUB / "index.html"
        hub_text = hub_file.read_text(encoding="utf-8") if hub_file.exists() else ""
        if not hub_file.exists():
            errors.append(f"중3 수학 허브 index.html 없음: {hub_file}")
    if actual_dirs != set(locals_):
        errors.append(
            f"상세 지역 폴더 불일치: 누락 {len(set(locals_) - actual_dirs)}, "
            f"추가 {len(actual_dirs - set(locals_))}"
        )

    hub_url = canonical()
    if hub_text:
        check_page_head(hub_text, CATEGORY_LABEL, hub_url, errors, "허브")
        expected_hub_breadcrumb = ["홈", "과목별학원", CATEGORY_LABEL]
        if breadcrumb_labels(hub_text) != expected_hub_breadcrumb:
            errors.append(f"허브: 화면 Breadcrumb 불일치 ({breadcrumb_labels(hub_text)})")
        hub_blocks, hub_json_errors = json_ld_blocks(hub_text)
        if hub_json_errors:
            errors.append(f"허브: JSON-LD 파싱 오류 ({hub_json_errors})")
        hub_breadcrumb_nodes = typed_nodes(hub_blocks, "BreadcrumbList")
        if len(hub_breadcrumb_nodes) != 1:
            errors.append(f"허브: BreadcrumbList 개수 오류 ({len(hub_breadcrumb_nodes)})")
        else:
            labels, _urls = json_breadcrumb(hub_breadcrumb_nodes[0])
            if labels != expected_hub_breadcrumb:
                errors.append(f"허브: JSON Breadcrumb 불일치 ({labels})")

        card_tags = [
            tag
            for tag in re.findall(r"<a\b[^>]*>", hub_text, flags=re.I | re.S)
            if "subject-town-card" in attrs(tag).get("class", "").split()
        ]
        card_urls = [
            normalize_url(attrs(tag).get("href", ""), hub_url)
            for tag in card_tags
            if attrs(tag).get("href")
        ]
        if len(card_urls) != 371 or set(card_urls) != expected_urls or len(set(card_urls)) != 371:
            errors.append(
                f"허브 카드 오류: 카드 {len(card_urls)}, 고유 {len(set(card_urls))}, "
                f"기대 URL과 차이 {len(set(card_urls) ^ expected_urls)}"
            )
        hub_itemlists = typed_nodes(hub_blocks, "ItemList")
        matching_hub_itemlists = [
            node for node in hub_itemlists if set(itemlist_urls(node, hub_url)) == expected_urls
        ]
        if len(matching_hub_itemlists) != 1:
            errors.append(f"허브: 371개 상세 URL을 담은 ItemList 개수 오류 ({len(matching_hub_itemlists)})")
    else:
        card_urls = []

    meta_descriptions: list[str] = []
    neutral_meta: Counter[str] = Counter()
    manuscripts: list[str] = []
    manuscript_names: list[str] = []
    manuscript_exact: Counter[str] = Counter()
    checklist_exact: Counter[str] = Counter()
    normalized_paragraphs: Counter[str] = Counter()
    peer_links: dict[str, set[str]] = defaultdict(set)
    internal_targets: set[Path] = set()
    detail_count = 0

    for local in locals_:
        row = row_by_local[local]
        page = HUB / local / "index.html"
        url = normalize_url(canonical(local))
        expected_title = f"{local} {CATEGORY_LABEL}"
        if not page.exists():
            errors.append(f"{local}: 상세 페이지 없음")
            continue
        detail_count += 1
        text = page.read_text(encoding="utf-8")
        check_page_head(text, expected_title, url, errors, local)

        descriptions = meta_value(text, "description")
        if len(descriptions) != 1 or not descriptions[0]:
            errors.append(f"{local}: meta description 개수/내용 오류 ({descriptions})")
            description = descriptions[0] if descriptions else ""
        else:
            description = clean_text(descriptions[0])
        meta_descriptions.append(description)
        neutral_meta[neutralize(description, row)] += 1
        if not 55 <= len(description) <= 170:
            warnings.append(f"{local}: 메타 설명 길이 {len(description)}자")

        expected_breadcrumb = ["홈", "과목별학원", CATEGORY_LABEL, expected_title]
        screen_breadcrumb = breadcrumb_labels(text)
        if screen_breadcrumb != expected_breadcrumb:
            errors.append(f"{local}: 화면 Breadcrumb 불일치 ({screen_breadcrumb})")

        blocks, json_errors = json_ld_blocks(text)
        if json_errors:
            errors.append(f"{local}: JSON-LD 파싱 오류 ({json_errors})")
        found_types = json_types(blocks)
        missing_types = REQUIRED_TYPES - found_types
        if missing_types:
            errors.append(f"{local}: JSON-LD 타입 누락 ({sorted(missing_types)})")
        forbidden_types = FORBIDDEN_SCHEMA_TYPES & found_types
        if forbidden_types:
            errors.append(f"{local}: 근거 없는 후기/평점 스키마 포함 ({sorted(forbidden_types)})")

        breadcrumb_nodes = typed_nodes(blocks, "BreadcrumbList")
        if len(breadcrumb_nodes) != 1:
            errors.append(f"{local}: BreadcrumbList 개수 오류 ({len(breadcrumb_nodes)})")
        else:
            labels, urls = json_breadcrumb(breadcrumb_nodes[0])
            if labels != expected_breadcrumb:
                errors.append(f"{local}: JSON Breadcrumb 라벨 불일치 ({labels})")
            if not urls or normalize_url(urls[-1], url) != url:
                errors.append(f"{local}: JSON Breadcrumb 마지막 URL이 자기 URL이 아님")

        screen_faq = visible_faq(text)
        faq_nodes = typed_nodes(blocks, "FAQPage")
        if len(faq_nodes) != 1:
            errors.append(f"{local}: FAQPage 개수 오류 ({len(faq_nodes)})")
            schema_faq: list[tuple[str, str]] = []
        else:
            schema_faq = json_faq(faq_nodes[0])
        if len(screen_faq) != 7:
            errors.append(f"{local}: 화면 FAQ가 7개가 아님 ({len(screen_faq)}개)")
        if screen_faq != schema_faq:
            errors.append(f"{local}: 화면 FAQ와 FAQPage JSON-LD 불일치")

        visible_related = visible_related_urls(text, url)
        related_itemlists = [
            node
            for node in typed_nodes(blocks, "ItemList")
            if str(node.get("@id", "")).endswith("#related-pages")
        ]
        if len(related_itemlists) != 1:
            errors.append(f"{local}: #related-pages ItemList 개수 오류 ({len(related_itemlists)})")
            schema_related: list[str] = []
        else:
            schema_related = itemlist_urls(related_itemlists[0], url)
        if visible_related != schema_related:
            errors.append(
                f"{local}: 화면 관련 링크와 ItemList URL/순서 불일치 "
                f"(화면 {len(visible_related)}, JSON {len(schema_related)})"
            )
        if len(visible_related) != len(set(visible_related)):
            errors.append(f"{local}: 화면 관련 링크 중복")

        peers = {
            target
            for target in visible_related
            if target != url and target in expected_urls
        }
        peer_links[url] = peers
        if len(peers) < 6:
            errors.append(f"{local}: 같은 카테고리 peer가 6개 미만 ({len(peers)}개)")

        middle2_url = normalize_url(middle2_canonical(local))
        if middle2_url not in visible_related:
            errors.append(f"{local}: 같은 동네 중2 수학학원 관련 링크 누락")
        middle2_path = MIDDLE2_HUB / local / "index.html"
        if not middle2_path.exists():
            errors.append(f"{local}: 중2 수학학원 링크 대상 페이지 없음 ({middle2_path})")

        for target_url in all_anchor_urls(text, url):
            target_path = local_path_from_url(target_url)
            if target_path is not None:
                internal_targets.add(target_path)

        manuscript_raw = manuscript_html(text)
        body = strip_tags(manuscript_raw)
        if len(body) < 1800:
            errors.append(f"{local}: 원고·보강 영역이 너무 짧음 ({len(body)}자)")
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(body):
                errors.append(f"{local}: 원고에 {label} 표현 포함")
        manuscripts.append(body)
        manuscript_names.append(local)
        manuscript_exact[body] += 1
        for paragraph in re.findall(r"<p\b[^>]*>(.*?)</p>", manuscript_raw, flags=re.I | re.S):
            normalized = neutralize(strip_tags(paragraph), row)
            if len(normalized) >= 45:
                normalized_paragraphs[normalized] += 1

        checklist = checklist_fingerprint(text)
        if not checklist:
            errors.append(f"{local}: 상담 체크리스트를 찾을 수 없음")
        checklist_exact[checklist] += 1

    for source, targets in peer_links.items():
        for target in targets:
            if source not in peer_links.get(target, set()):
                errors.append(f"peer 비대칭: {source} -> {target}")

    for target in sorted(internal_targets):
        if not target.exists():
            errors.append(f"깨진 내부링크: {target}")

    duplicate_meta = sum(count - 1 for count in Counter(meta_descriptions).values() if count > 1)
    if duplicate_meta:
        errors.append(f"메타 설명 완전 중복 {duplicate_meta}개")
    if neutral_meta:
        max_neutral_meta = max(neutral_meta.values())
        if max_neutral_meta > 8:
            errors.append(f"지역 사실 치환 후 메타 템플릿 최대 반복 {max_neutral_meta}회 (허용 8회)")
    else:
        max_neutral_meta = 0

    duplicate_manuscripts = sum(count - 1 for count in manuscript_exact.values() if count > 1)
    if duplicate_manuscripts:
        errors.append(f"원고 완전 중복 {duplicate_manuscripts}개")
    duplicate_checklists = sum(count - 1 for count in checklist_exact.values() if count > 1)
    if duplicate_checklists:
        errors.append(f"상담 체크리스트 완전 중복 {duplicate_checklists}개")
    frequent_paragraphs = {
        paragraph: count for paragraph, count in normalized_paragraphs.items() if count > 20
    }
    if frequent_paragraphs:
        errors.append(
            f"지역 사실 치환 후 원고 문단 20회 초과 반복 {len(frequent_paragraphs)}종 "
            f"(최대 {max(frequent_paragraphs.values())}회)"
        )

    shingle_sets = [shingles(body) for body in manuscripts]
    similarities: list[float] = []
    highest = (0.0, "", "")
    for left in range(len(shingle_sets)):
        for right in range(left + 1, len(shingle_sets)):
            union = shingle_sets[left] | shingle_sets[right]
            score = len(shingle_sets[left] & shingle_sets[right]) / len(union) if union else 0.0
            similarities.append(score)
            if score > highest[0]:
                highest = (score, manuscript_names[left], manuscript_names[right])
    mean_similarity = statistics.fmean(similarities) if similarities else 0.0
    if highest[0] > 0.25:
        errors.append(
            f"원고 5-shingle 최대 유사도 과다 {highest[0]:.4f} "
            f"({highest[1]} / {highest[2]}, 허용 0.25)"
        )
    if mean_similarity > 0.15:
        errors.append(f"원고 5-shingle 평균 유사도 과다 {mean_similarity:.4f} (허용 0.15)")

    sitemap_urls: list[str] = []
    if not SITEMAP.exists():
        errors.append(f"사이트맵 없음: {SITEMAP}")
    else:
        try:
            sitemap = ET.parse(SITEMAP)
            sitemap_urls = [
                normalize_url(node.text.strip())
                for node in sitemap.getroot().iter()
                if node.tag.endswith("loc") and node.text
            ]
        except ET.ParseError as exc:
            errors.append(f"사이트맵 XML 파싱 실패 ({exc})")
    sitemap_counts = Counter(sitemap_urls)
    sitemap_duplicates = [url for url, count in sitemap_counts.items() if count > 1]
    if sitemap_duplicates:
        errors.append(f"사이트맵 중복 URL {len(sitemap_duplicates)}개")
    expected_sitemap = {normalize_url(hub_url)} | expected_urls
    missing_sitemap = expected_sitemap - set(sitemap_urls)
    if missing_sitemap:
        errors.append(f"중3 수학 사이트맵 URL 누락 {len(missing_sitemap)}개")

    peer_counts = [len(peer_links.get(url, set())) for url in expected_urls]
    print(f"DETAIL_EXPECTED=371")
    print(f"DETAIL_PARSED={detail_count}")
    print(f"HUB_CARDS={len(card_urls)}")
    print(f"META_EXACT_UNIQUE={len(set(meta_descriptions))}/{len(meta_descriptions)}")
    print(f"META_NEUTRAL_UNIQUE={len(neutral_meta)}/{len(meta_descriptions)} MAX_REPEAT={max_neutral_meta}")
    print(f"MANUSCRIPT_EXACT_UNIQUE={len(manuscript_exact)}/{len(manuscripts)}")
    print(f"CHECKLIST_EXACT_UNIQUE={len(checklist_exact)}/{sum(checklist_exact.values())}")
    if peer_counts:
        print(
            f"PEER_MIN={min(peer_counts)} PEER_AVG={statistics.fmean(peer_counts):.3f} "
            f"PEER_MAX={max(peer_counts)}"
        )
    if similarities:
        print(f"SHINGLE_JACCARD_MAX={highest[0]:.4f} ({highest[1]} / {highest[2]})")
        print(f"SHINGLE_JACCARD_MEAN={mean_similarity:.4f}")
    else:
        print("SHINGLE_JACCARD_MAX=0.0000")
        print("SHINGLE_JACCARD_MEAN=0.0000")
    print(f"REPEATED_PARAGRAPH_TYPES_OVER_20={len(frequent_paragraphs)}")
    print(f"INTERNAL_TARGETS_CHECKED={len(internal_targets)}")
    print(f"SITEMAP_URLS={len(sitemap_urls)}")
    print(f"SITEMAP_DUPLICATES={len(sitemap_duplicates)}")
    print(f"WARNINGS={len(warnings)}")
    for warning in warnings[:20]:
        print(f"WARN: {warning}")
    print(f"ERRORS={len(errors)}")
    for error in errors[:100]:
        print(f"ERROR: {error}")
    if len(errors) > 100:
        print(f"ERROR: ... 외 {len(errors) - 100}개")
    if errors:
        return 1
    print("AUDIT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
