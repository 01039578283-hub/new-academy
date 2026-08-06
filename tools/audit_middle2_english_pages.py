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
HUB = ROOT / "과목별학원" / "중2영어학원"
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
    parts = ["과목별학원", "중2영어학원", local]
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


def manuscript_html(text: str) -> str:
    return first_match(
        r"<section\b[^>]*class=[\"'][^\"']*manuscript-panel[^\"']*[\"'][^>]*>(.*?)</section>\s*<section\b[^>]*class=[\"'][^\"']*subject-local-facts",
        text,
        re.I | re.S,
    )


def manuscript_text(text: str) -> str:
    return strip_tags(manuscript_html(text))


def links_to(source: Path, target: Path) -> bool:
    text = source.read_text(encoding="utf-8")
    for anchor in re.findall(r"<a\b[^>]*href=[\"'].*?[\"'][^>]*>", text, flags=re.I | re.S):
        resolved = resolve_local(source, attrs(anchor).get("href", ""))
        if resolved == target.resolve():
            return True
    return False


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

    generator_text = (ROOT / "tools" / "generate_middle2_english_pages.py").read_text(encoding="utf-8")
    if any(token in generator_text for token in ("load_manuscripts(", "openpyxl", "MANUSCRIPT")):
        errors.append("영어 생성기가 원고 엑셀 로더를 참조하고 있습니다.")
    for row in rows:
        local = row_value(row, "근처 수업가능 동네")
        region = row_value(row, "지역")
        district = row_value(row, "시or구")
        candidates = [
            ROOT / "전국학원" / region / district / local,
            ROOT / "전국학원" / region / "시" / local,
        ]
        parent = next((candidate for candidate in candidates if (candidate / "index.html").exists()), None)
        if parent is None or not (parent / "중1영어학원" / "index.html").exists() or not (parent / "초6영어학원" / "index.html").exists():
            errors.append(f"{local}: 기존 전국학원 영어 참고 페이지 누락")

    directories = {path.name for path in HUB.iterdir() if path.is_dir()}
    if directories != expected:
        errors.append(f"동네 폴더 불일치: 누락={sorted(expected - directories)}, 초과={sorted(directories - expected)}")

    hub_text = (HUB / "index.html").read_text(encoding="utf-8")
    if len(re.findall(r'class="subject-town-card"', hub_text)) != 371:
        errors.append("중2 영어학원 허브의 동네 카드 수가 371개가 아닙니다.")
    if len(re.findall(r'class="subject-region-group"', hub_text)) != 13:
        errors.append("중2 영어학원 허브의 광역 그룹 수가 13개가 아닙니다.")
    if len(re.findall(r'class="subject-district-group"', hub_text)) != 76:
        errors.append("중2 영어학원 허브의 시군구 그룹 수가 76개가 아닙니다.")
    category_text = (ROOT / "과목별학원" / "index.html").read_text(encoding="utf-8")
    if "중2수학학원/index.html" not in category_text or "중2영어학원/index.html" not in category_text:
        errors.append("과목별학원 통합 허브에 수학·영어 카드가 모두 있지 않습니다.")

    meta_descriptions: list[str] = []
    manuscripts: list[str] = []
    manuscript_names: list[str] = []
    exact_fingerprints: Counter[str] = Counter()
    faq_answer_fingerprints: Counter[str] = Counter()
    within_page_repeated_sentences = 0
    copied_paragraphs = 0
    link_targets: set[Path] = set()
    unknown_grade = {
        row_value(row, "근처 수업가능 동네")
        for row in rows
        if not row_value(row, "가능학년\n(영어)")
    }

    for row in rows:
        local = row_value(row, "근처 수업가능 동네")
        page = HUB / local / "index.html"
        if not page.exists():
            errors.append(f"페이지 누락: {local}")
            continue
        text = page.read_text(encoding="utf-8")
        expected_title = f"{local} 중2 영어학원"
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
        expected_breadcrumb = ["홈", "과목별학원", "중2 영어학원", expected_title]
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
        forbidden_types = {"Review", "AggregateRating"} & json_types(blocks)
        if forbidden_types:
            errors.append(f"{local}: 검증되지 않은 후기/평점 스키마 발견 ({sorted(forbidden_types)})")
        breadcrumb_node = find_typed_node(blocks, "BreadcrumbList") or {}
        json_breadcrumb = [item.get("name", "") for item in breadcrumb_node.get("itemListElement", [])]
        if json_breadcrumb != expected_breadcrumb:
            errors.append(f"{local}: JSON 브레드크럼 불일치 ({json_breadcrumb})")
        screen_faq = visible_faq(text)
        if screen_faq != json_faq(blocks):
            errors.append(f"{local}: 화면 FAQ와 JSON-LD FAQ 불일치")
        if len(screen_faq) != 7:
            errors.append(f"{local}: FAQ가 7개가 아님 ({len(screen_faq)})")
        faq_answer_fingerprints.update(answer for _question, answer in screen_faq)

        checklist = first_match(
            r"<section\b[^>]*class=[\"'][^\"']*geo-checklist-panel[^\"']*[\"'][^>]*>(.*?)</section>",
            text,
            re.I | re.S,
        )
        if len(re.findall(r'class=["\'][^"\']*geo-check-card', checklist, re.I)) != 4:
            errors.append(f"{local}: 개별 체크리스트가 4개가 아님")

        subject_nav = first_match(
            r"<section\b[^>]*class=[\"'][^\"']*local-page-nav[^\"']*[\"'][^>]*>(.*?)</section>",
            text,
            re.I | re.S,
        )
        peer_targets: list[Path] = []
        for anchor in re.findall(r"<a\b[^>]*href=[\"'].*?[\"'][^>]*>", subject_nav, flags=re.I | re.S):
            target = resolve_local(page, attrs(anchor).get("href", ""))
            if target is not None and target.parent.parent == HUB:
                peer_targets.append(target)
        if len(set(peer_targets)) != 6:
            errors.append(f"{local}: 중2 영어 상호 지역 링크가 6개가 아님 ({len(set(peer_targets))})")
        math_page = ROOT / "과목별학원" / "중2수학학원" / local / "index.html"
        if not links_to(page, math_page) or not links_to(math_page, page):
            errors.append(f"{local}: 같은 동네 중2 수학·영어 상호 링크 누락")
        for peer_page in set(peer_targets):
            if not links_to(peer_page, page):
                errors.append(f"{local}: 영어 지역 링크가 상호 연결되지 않음 ({peer_page.parent.name})")

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
        generated_body_name = first_match(r"assets/centers/common/([^\"?#]+)", media, re.I)
        reference_parent_candidates = [
            ROOT / "전국학원" / row_value(row, "지역") / row_value(row, "시or구") / local,
            ROOT / "전국학원" / row_value(row, "지역") / "시" / local,
        ]
        reference_parent_for_image = next(candidate for candidate in reference_parent_candidates if (candidate / "index.html").exists())
        reference_english_text = (reference_parent_for_image / "중1영어학원" / "index.html").read_text(encoding="utf-8")
        expected_body_name = first_match(r"assets/centers/common/([^\"?#]+)", reference_english_text, re.I)
        if generated_body_name != expected_body_name:
            errors.append(f"{local}: 기존 영어 페이지와 본문 이미지 불일치 ({generated_body_name} / {expected_body_name})")

        if local in unknown_grade and "상담 확인 필요" not in text:
            errors.append(f"{local}: 영어 가능학년 미공개 안내 누락")
        tuition = row_value(row, "센터 교습비")
        if tuition and tuition not in html_lib.unescape(text):
            errors.append(f"{local}: 검증된 교습비 링크 누락")
        location_guide = row_value(row, "위치안내")
        if location_guide and strip_tags(location_guide) not in strip_tags(text):
            errors.append(f"{local}: 검증된 위치안내 누락")
        schools = [item.strip() for item in re.split(r"[,/|;\n]+", row_value(row, "타깃학교\n(중)")) if item.strip()]
        if f"공개 자료의 중학교 안내 · {len(schools)}개" not in strip_tags(text):
            errors.append(f"{local}: 공개 중학교 수 표기 불일치")

        for anchor in re.findall(r"<a\b[^>]*href=[\"'].*?[\"'][^>]*>", text, flags=re.I | re.S):
            href = attrs(anchor).get("href", "")
            target = resolve_local(page, href)
            if target is not None:
                link_targets.add(target)

        body = manuscript_text(text)
        if len(body) < 2500:
            errors.append(f"{local}: 핵심 원고 분량 부족 ({len(body)}자)")
        raw_manuscript = manuscript_html(text)
        sentence_values: list[str] = []
        for paragraph in re.findall(r"<p\b[^>]*>(.*?)</p>", raw_manuscript, flags=re.I | re.S):
            paragraph_text = strip_tags(paragraph)
            sentence_values.extend(
                sentence.strip()
                for sentence in re.split(r"(?<=[.!?])\s+", paragraph_text)
                if len(sentence.strip()) >= 25
            )
        repeated_here = sum(count - 1 for count in Counter(sentence_values).values() if count > 1)
        within_page_repeated_sentences += repeated_here
        if repeated_here:
            errors.append(f"{local}: 원고 안에서 동일 문장 {repeated_here}회 반복")
        generated_paragraphs = {
            strip_tags(paragraph)
            for paragraph in re.findall(r"<p\b[^>]*>(.*?)</p>", raw_manuscript, flags=re.I | re.S)
            if len(strip_tags(paragraph)) >= 40
        }
        parent_candidates = [
            ROOT / "전국학원" / row_value(row, "지역") / row_value(row, "시or구") / local,
            ROOT / "전국학원" / row_value(row, "지역") / "시" / local,
        ]
        reference_parent = next(candidate for candidate in parent_candidates if (candidate / "index.html").exists())
        reference_paragraphs: set[str] = set()
        for source in (reference_parent / "중1영어학원" / "index.html", reference_parent / "초6영어학원" / "index.html"):
            source_text = source.read_text(encoding="utf-8")
            reference_paragraphs.update(
                strip_tags(paragraph)
                for paragraph in re.findall(r"<p\b[^>]*>(.*?)</p>", source_text, flags=re.I | re.S)
                if len(strip_tags(paragraph)) >= 40
            )
        overlap = generated_paragraphs & reference_paragraphs
        copied_paragraphs += len(overlap)
        if overlap:
            errors.append(f"{local}: 기존 전국학원 영어 원문과 동일한 문단 {len(overlap)}개")
        for phrase in ("성적 상승", "점수 향상", "성적 보장", "상위권 보장"):
            if phrase in body:
                errors.append(f"{local}: 결과 보장성 표현 발견 ({phrase})")
        for phrase in ("국어 중심", "수학 중심", "영수학원"):
            if phrase in body:
                errors.append(f"{local}: 영어 원고에 교차과목 중심 문구 발견 ({phrase})")
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
    duplicate_faq_answers = sum(count - 1 for count in faq_answer_fingerprints.values() if count > 1)
    if duplicate_faq_answers:
        errors.append(f"FAQ 답변 완전 중복 {duplicate_faq_answers}개")

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
    if highest[0] > 0.25:
        errors.append(f"원고 최대 5-shingle 유사도 초과 ({highest[0]:.4f}, 목표 0.2500 이하)")

    sitemap = ET.parse(ROOT / "sitemap.xml")
    sitemap_urls = [node.text.strip() for node in sitemap.getroot().iter() if node.tag.endswith("loc") and node.text]
    expected_new_urls = {DOMAIN + "/"} | {
        DOMAIN + "/" + "/".join(quote(part, safe="") for part in ["과목별학원"]) + "/",
        DOMAIN + "/" + "/".join(quote(part, safe="") for part in ["과목별학원", "중2영어학원"]) + "/",
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
    print(f"COPIED_SOURCE_PARAGRAPHS={copied_paragraphs}")
    print(f"FAQ_ANSWERS_EXACT_UNIQUE={len(faq_answer_fingerprints)}/{sum(faq_answer_fingerprints.values())}")
    print(f"WITHIN_PAGE_REPEATED_SENTENCES={within_page_repeated_sentences}")
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
