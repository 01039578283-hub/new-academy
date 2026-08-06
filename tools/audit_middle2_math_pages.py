from __future__ import annotations

import csv
import html as html_lib
import json
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "참고자료" / "공통자료" / "센터정보 정리.csv"
HUB = ROOT / "과목별학원" / "중2수학학원"
DOMAIN = "https://xn--z92bu9jx8cwzc.com"
REQUIRED_TYPES = {
    "EducationalOrganization",
    "LocalBusiness",
    "Article",
    "Service",
    "FAQPage",
    "BreadcrumbList",
    "ItemList",
}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def row_value(row: dict[str, str], key: str) -> str:
    return (row.get(key) or "").strip()


def strip_tags(value: str) -> str:
    value = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html_lib.unescape(value)).strip()


def attrs(tag: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, _quote, value in re.findall(r"([:\w-]+)\s*=\s*([\"'])(.*?)\2", tag, flags=re.S):
        result[name.lower()] = html_lib.unescape(value)
    return result


def canonical(local: str) -> str:
    parts = ["과목별학원", "중2수학학원", local]
    return DOMAIN + "/" + "/".join(quote(part, safe="") for part in parts) + "/"


def first_match(pattern: str, text: str, flags: int = 0) -> str:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else ""


def meta_value(text: str, key: str, attribute: str = "name") -> str:
    for tag in re.findall(r"<meta\b[^>]*>", text, flags=re.I):
        data = attrs(tag)
        if data.get(attribute) == key:
            return data.get("content", "")
    return ""


def canonical_value(text: str) -> str:
    for tag in re.findall(r"<link\b[^>]*>", text, flags=re.I):
        data = attrs(tag)
        if data.get("rel", "").lower() == "canonical":
            return data.get("href", "")
    return ""


def json_ld_blocks(text: str) -> list[dict]:
    blocks: list[dict] = []
    for raw in re.findall(
        r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        text,
        flags=re.I | re.S,
    ):
        blocks.append(json.loads(html_lib.unescape(raw.strip())))
    return blocks


def walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


def json_types(blocks: list[dict]) -> set[str]:
    found: set[str] = set()
    for block in blocks:
        for node in walk_json(block):
            value = node.get("@type")
            if isinstance(value, str):
                found.add(value)
            elif isinstance(value, list):
                found.update(item for item in value if isinstance(item, str))
    return found


def find_typed_node(blocks: list[dict], type_name: str) -> dict | None:
    for block in blocks:
        for node in walk_json(block):
            value = node.get("@type")
            if value == type_name or isinstance(value, list) and type_name in value:
                return node
    return None


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


def json_faq(blocks: list[dict]) -> list[tuple[str, str]]:
    node = find_typed_node(blocks, "FAQPage") or {}
    result: list[tuple[str, str]] = []
    for item in node.get("mainEntity", []):
        result.append((item.get("name", ""), item.get("acceptedAnswer", {}).get("text", "")))
    return result


def resolve_local(base: Path, href: str) -> Path | None:
    split = urlsplit(html_lib.unescape(href))
    if split.scheme or split.netloc or href.startswith(("#", "tel:", "mailto:", "javascript:")):
        return None
    raw_path = unquote(split.path)
    if not raw_path:
        return None
    if raw_path.startswith("/"):
        target = ROOT / raw_path.lstrip("/")
    else:
        target = base.parent / raw_path
    if raw_path.endswith("/"):
        target = target / "index.html"
    return target.resolve()


def manuscript_text(text: str) -> str:
    section = first_match(
        r"<section\b[^>]*class=[\"'][^\"']*manuscript-panel[^\"']*[\"'][^>]*>(.*?)</section>\s*<section\b[^>]*class=[\"'][^\"']*subject-local-facts",
        text,
        re.I | re.S,
    )
    return strip_tags(section)


def shingles(value: str, size: int = 5) -> set[tuple[str, ...]]:
    words = re.findall(r"[가-힣A-Za-z0-9]+", value.lower())
    return {tuple(words[index : index + size]) for index in range(max(0, len(words) - size + 1))}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    locals_ = [row_value(row, "근처 수업가능 동네") for row in rows]
    expected = set(locals_)

    directories = {path.name for path in HUB.iterdir() if path.is_dir()}
    if directories != expected:
        errors.append(f"동네 폴더 불일치: 누락={sorted(expected - directories)}, 초과={sorted(directories - expected)}")

    hub_text = (HUB / "index.html").read_text(encoding="utf-8")
    if len(re.findall(r'class="subject-town-card"', hub_text)) != 371:
        errors.append("중2 수학학원 허브의 동네 카드 수가 371개가 아닙니다.")
    if len(re.findall(r'class="subject-region-group"', hub_text)) != 13:
        errors.append("중2 수학학원 허브의 광역 그룹 수가 13개가 아닙니다.")
    if len(re.findall(r'class="subject-district-group"', hub_text)) != 76:
        errors.append("중2 수학학원 허브의 시군구 그룹 수가 76개가 아닙니다.")

    meta_descriptions: list[str] = []
    manuscripts: list[str] = []
    manuscript_names: list[str] = []
    exact_fingerprints: Counter[str] = Counter()
    link_targets: set[Path] = set()
    unknown_grade = {
        row_value(row, "근처 수업가능 동네")
        for row in rows
        if not row_value(row, "가능학년\n(수학)")
    }

    for row in rows:
        local = row_value(row, "근처 수업가능 동네")
        page = HUB / local / "index.html"
        if not page.exists():
            errors.append(f"페이지 누락: {local}")
            continue
        text = page.read_text(encoding="utf-8")
        expected_title = f"{local} 중2 수학학원"
        title = strip_tags(first_match(r"<title>(.*?)</title>", text, re.I | re.S))
        if title != f"{expected_title} | 와와센터":
            errors.append(f"{local}: title 불일치 ({title})")
        h1_values = [strip_tags(item) for item in re.findall(r"<h1\b[^>]*>(.*?)</h1>", text, flags=re.I | re.S)]
        if h1_values != [expected_title]:
            errors.append(f"{local}: H1 불일치/중복 ({h1_values})")

        description = meta_value(text, "description")
        meta_descriptions.append(description)
        if not 50 <= len(description) <= 170:
            warnings.append(f"{local}: 메타 설명 길이 {len(description)}자")
        expected_url = canonical(local)
        actual_canonical = canonical_value(text)
        og_url = meta_value(text, "og:url", "property")
        if actual_canonical != expected_url or og_url != expected_url:
            errors.append(f"{local}: canonical/og:url 불일치")

        breadcrumb = first_match(
            r"<nav\b[^>]*class=[\"'][^\"']*breadcrumb-box[^\"']*[\"'][^>]*>(.*?)</nav>",
            text,
            re.I | re.S,
        )
        breadcrumb_labels = [part.strip() for part in strip_tags(breadcrumb).split("›")]
        expected_breadcrumb = ["홈", "과목별학원", "중2 수학학원", expected_title]
        if breadcrumb_labels != expected_breadcrumb:
            errors.append(f"{local}: 화면 브레드크럼 불일치 ({breadcrumb_labels})")

        try:
            blocks = json_ld_blocks(text)
        except json.JSONDecodeError as exc:
            errors.append(f"{local}: JSON-LD 파싱 실패 ({exc})")
            blocks = []
        missing_types = REQUIRED_TYPES - json_types(blocks)
        if missing_types:
            errors.append(f"{local}: JSON-LD 타입 누락 ({sorted(missing_types)})")
        breadcrumb_node = find_typed_node(blocks, "BreadcrumbList") or {}
        json_breadcrumb = [item.get("name", "") for item in breadcrumb_node.get("itemListElement", [])]
        if json_breadcrumb != expected_breadcrumb:
            errors.append(f"{local}: JSON 브레드크럼 불일치 ({json_breadcrumb})")
        if visible_faq(text) != json_faq(blocks):
            errors.append(f"{local}: 화면 FAQ와 JSON-LD FAQ 불일치")

        media = first_match(
            r"<section\b[^>]*class=[\"'][^\"']*local-media-section[^\"']*[\"'][^>]*>(.*?)</section>",
            text,
            re.I | re.S,
        )
        first_element = re.search(r"<([a-z0-9]+)\b([^>]*)>", media, flags=re.I | re.S)
        if not first_element or first_element.group(1).lower() != "img":
            errors.append(f"{local}: 숨김 대표 이미지가 이미지 섹션 첫 요소가 아님")
        else:
            image_data = attrs(first_element.group(0))
            if "display:none" not in image_data.get("style", "").replace(" ", ""):
                errors.append(f"{local}: 대표 이미지 display:none 누락")
            if image_data.get("loading", "").lower() == "lazy":
                errors.append(f"{local}: 대표 이미지에 loading=lazy가 적용됨")
            if image_data.get("alt") != f"{expected_title} 와와센터 대표":
                errors.append(f"{local}: 대표 이미지 alt 불일치")

        local_images = []
        for image_tag in re.findall(r"<img\b[^>]*>", media, flags=re.I):
            source = attrs(image_tag).get("src", "")
            if source and not urlsplit(source).scheme:
                local_images.append(resolve_local(page, source))
        if len(local_images) < 2:
            errors.append(f"{local}: 본문/지도 이미지가 모두 들어있지 않음")
        for target in local_images:
            if target is not None and not target.exists():
                errors.append(f"{local}: 이미지 경로 깨짐 ({target})")

        if local in unknown_grade and "상담 확인 필요" not in text:
            errors.append(f"{local}: 수학 가능학년 미공개 안내 누락")

        for anchor in re.findall(r"<a\b[^>]*href=[\"'].*?[\"'][^>]*>", text, flags=re.I | re.S):
            href = attrs(anchor).get("href", "")
            target = resolve_local(page, href)
            if target is not None:
                link_targets.add(target)

        body = manuscript_text(text)
        manuscripts.append(body)
        manuscript_names.append(local)
        exact_fingerprints[body] += 1

    for target in sorted(link_targets):
        if not target.exists():
            errors.append(f"내부링크 대상 누락: {target}")

    if len(set(meta_descriptions)) != len(meta_descriptions):
        errors.append(f"메타 설명 중복 {len(meta_descriptions) - len(set(meta_descriptions))}개")
    duplicate_bodies = sum(count - 1 for count in exact_fingerprints.values() if count > 1)
    if duplicate_bodies:
        errors.append(f"원고 본문 완전 중복 {duplicate_bodies}개")

    shingle_sets = [shingles(value) for value in manuscripts]
    similarities: list[float] = []
    highest = (0.0, "", "")
    for left in range(len(shingle_sets)):
        for right in range(left + 1, len(shingle_sets)):
            union = shingle_sets[left] | shingle_sets[right]
            score = len(shingle_sets[left] & shingle_sets[right]) / len(union) if union else 0.0
            similarities.append(score)
            if score > highest[0]:
                highest = (score, manuscript_names[left], manuscript_names[right])

    sitemap = ET.parse(ROOT / "sitemap.xml")
    sitemap_urls = [node.text.strip() for node in sitemap.getroot().iter() if node.tag.endswith("loc") and node.text]
    expected_new_urls = {DOMAIN + "/"} | {
        DOMAIN + "/" + "/".join(quote(part, safe="") for part in ["과목별학원"]) + "/",
        DOMAIN + "/" + "/".join(quote(part, safe="") for part in ["과목별학원", "중2수학학원"]) + "/",
    } | {canonical(local) for local in locals_}
    missing_sitemap = expected_new_urls - set(sitemap_urls)
    if missing_sitemap:
        errors.append(f"사이트맵 신규 URL 누락 {len(missing_sitemap)}개")
    if len(sitemap_urls) != len(set(sitemap_urls)):
        errors.append(f"사이트맵 중복 URL {len(sitemap_urls) - len(set(sitemap_urls))}개")

    core_pages = [ROOT / "index.html", ROOT / "학습가이드" / "index.html", ROOT / "상담문의" / "index.html", ROOT / "전국학원" / "index.html"]
    for page in core_pages:
        if "과목별학원" not in page.read_text(encoding="utf-8"):
            errors.append(f"핵심 페이지 메뉴에 과목별학원 누락: {page}")

    print(f"DETAIL_PAGES={len(manuscripts)}")
    print(f"HUB_CARDS={len(re.findall(r'class=\"subject-town-card\"', hub_text))}")
    print(f"META_UNIQUE={len(set(meta_descriptions))}/{len(meta_descriptions)}")
    print(f"MANUSCRIPT_EXACT_UNIQUE={len(exact_fingerprints)}/{len(manuscripts)}")
    print(f"SHINGLE_JACCARD_MAX={highest[0]:.4f} ({highest[1]} / {highest[2]})")
    print(f"SHINGLE_JACCARD_MEAN={statistics.fmean(similarities):.4f}")
    print(f"SITEMAP_URLS={len(sitemap_urls)}")
    print(f"INTERNAL_TARGETS_CHECKED={len(link_targets)}")
    print(f"WARNINGS={len(warnings)}")
    for warning in warnings[:20]:
        print(f"WARN: {warning}")
    print(f"ERRORS={len(errors)}")
    for error in errors[:100]:
        print(f"ERROR: {error}")
    if len(errors) > 100:
        print(f"ERROR: ... 외 {len(errors) - 100}개")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
