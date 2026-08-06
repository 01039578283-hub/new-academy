from __future__ import annotations

import csv
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote

import audit_middle3_english_pages as shared


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "참고자료" / "공통자료" / "센터정보 정리.csv"
SUBJECT_ROOT = ROOT / "과목별학원"
HUB = SUBJECT_ROOT / "고1영어학원"
PREVIOUS_HUB = SUBJECT_ROOT / "중3영어학원"
SITEMAP = ROOT / "sitemap.xml"
DOMAIN = "https://xn--z92bu9jx8cwzc.com"
CATEGORY = "고1영어학원"
CATEGORY_LABEL = "고1 영어학원"
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
REQUIRED_SECTIONS = {
    "local-media-section",
    "subject-answer-panel",
    "manuscript-panel",
    "subject-local-facts",
    "geo-checklist-panel",
    "local-proof-section",
    "local-page-nav",
}
HIGH1_INTENT_GROUPS = {
    "고교 내신 적응": re.compile(r"고1|고등학교\s*1학년|고교\s*내신|고등\s*내신|내신\s*적응"),
    "모의고사": re.compile(r"모의고사|전국연합|학력평가"),
    "어휘": re.compile(r"어휘|단어|품사"),
    "구문·문장 구조": re.compile(r"구문|문장\s*구조|문법|어순|동사\s*형태"),
    "독해": re.compile(r"독해|지문|문단|근거\s*문장"),
    "수행·서술형": re.compile(r"수행평가|서술형|영작|쓰기|답안\s*수정|문장\s*작성"),
    "학습 시간관리": re.compile(
        r"시간\s*관리|학습\s*시간|주간\s*(?:계획|일정)|복습\s*(?:간격|일정|날짜)|시간\s*배분"
    ),
}
FORBIDDEN_PATTERNS = {
    "교차과목": re.compile(r"수학|(?<!한)국어|영수|국영수"),
    "수학 중심 용어": re.compile(r"방정식|함수|도형|공식\s*암기|계산\s*실수|풀이\s*과정|수학\s*내신"),
    "근거 없는 성과·점수 보장": re.compile(
        r"(?:"
        r"(?:성적|점수|등급|합격)[^.!?<>]{0,35}(?:보장|상승|향상|오르|올리|끌어올리|완성|달성|연결)|"
        r"(?:보장|상승|향상|오르|올리|끌어올리)[^.!?<>]{0,25}(?:성적|점수|등급|합격)|"
        r"100\s*%|전교\s*1등|단기간\s*(?:성적|점수)|바로\s*(?:성적|점수)|"
        r"무조건\s*(?:성적|점수|등급|합격)|최고의\s*(?:학원|수업|강사진)|유일한\s*(?:학원|수업)"
        r")"
    ),
    "근거 없는 학교·출제 단정": re.compile(
        r"(?:학교별|지역\s*학생들의?)[^.!?<>]{0,35}(?:출제\s*(?:흐름|경향)|시험\s*범위)[^.!?<>]{0,35}(?:맞춰|반영|분석|대비)|"
        r"출제\s*(?:흐름|경향)[^.!?<>]{0,25}(?:정확|완벽|반드시)"
    ),
}


def canonical(local: str | None = None) -> str:
    parts = ["과목별학원", CATEGORY]
    if local:
        parts.append(local)
    return DOMAIN + "/" + "/".join(quote(part, safe="") for part in parts) + "/"


def previous_canonical(local: str) -> str:
    parts = ["과목별학원", "중3영어학원", local]
    return DOMAIN + "/" + "/".join(quote(part, safe="") for part in parts) + "/"


def split_items(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,/|]", value or "") if item.strip()]


def verify_head(text: str, title: str, url: str, label: str, errors: list[str]) -> None:
    h1_values = [
        shared.strip_tags(value)
        for value in re.findall(r"<h1\b[^>]*>(.*?)</h1>", text, flags=re.I | re.S)
    ]
    if h1_values != [title]:
        errors.append(f"{label}: H1 불일치/중복 ({h1_values})")
    canonicals = [
        shared.normalize_url(value, url)
        for value in shared.canonical_values(text)
        if value
    ]
    if canonicals != [shared.normalize_url(url)]:
        errors.append(f"{label}: canonical 불일치 ({canonicals})")
    og_urls = [
        shared.normalize_url(value, url)
        for value in shared.meta_values(text, "og:url", "property")
        if value
    ]
    if og_urls != [shared.normalize_url(url)]:
        errors.append(f"{label}: og:url 불일치 ({og_urls})")


def verify_facts(row: dict[str, str], local: str, text: str, errors: list[str]) -> None:
    center = shared.row_value(row, "센터명")
    address = shared.row_value(row, "센터 주소")
    office = shared.row_value(row, "교육지원청명칭")
    registration = shared.row_value(row, "교육지원청 등록번호")
    tuition = shared.row_value(row, "센터 교습비")
    location = shared.row_value(row, "위치안내")
    grades = split_items(shared.row_value(row, "가능학년\n(영어)"))
    schools = split_items(shared.row_value(row, "타깃학교\n(고)"))

    visible_text = re.sub(r"\s+", " ", shared.strip_tags(text)).strip()
    for field, value in {
        "센터명": center,
        "센터 주소": address,
        "교육지원청명칭": office,
        "교육지원청 등록번호": registration,
    }.items():
        normalized_value = re.sub(r"\s+", " ", value or "").strip()
        if normalized_value and normalized_value not in visible_text:
            errors.append(f"{local}: 공개 {field} 누락 ({value})")
    if tuition and tuition not in text:
        errors.append(f"{local}: 공개 교습비 링크 누락")
    if location and shared.strip_tags(location) not in shared.strip_tags(text):
        errors.append(f"{local}: 공개 위치안내 누락")

    if "고1" in grades:
        if "고1" not in text or not re.search(r"자료에\s*기재|가능\s*학년|수강\s*가능", text):
            errors.append(f"{local}: 고1 영어 가능학년 사실 표시 누락")
    elif "상담 확인 필요" not in text:
        errors.append(f"{local}: 고1 영어 가능학년 미기재 지역의 상담 확인 안내 누락")

    if schools:
        missing = [school for school in schools if school not in text]
        if missing:
            errors.append(f"{local}: 공개 고등학교 정보 누락 ({missing})")
    elif not re.search(r"고등학교명[^.!?<>]{0,30}(?:미기재|기재되어 있지|상담\s*시\s*확인)", text):
        errors.append(f"{local}: 고등학교 정보 미기재 안내 누락")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    if not DATA.exists():
        print(f"ERROR: 센터 CSV 없음: {DATA}")
        return 1
    with DATA.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    locals_ = [shared.row_value(row, "근처 수업가능 동네") for row in rows]
    row_by_local = {shared.row_value(row, "근처 수업가능 동네"): row for row in rows}
    if len(locals_) != 371 or len(set(locals_)) != 371 or any(not local for local in locals_):
        errors.append(f"센터 CSV 동네 집합 오류: 전체 {len(locals_)}, 고유 {len(set(locals_))}")

    expected_urls = {shared.normalize_url(canonical(local)) for local in locals_}
    if HUB.exists():
        actual_dirs = {
            path.name for path in HUB.iterdir() if path.is_dir() and (path / "index.html").exists()
        }
        hub_file = HUB / "index.html"
        hub_text = hub_file.read_text(encoding="utf-8") if hub_file.exists() else ""
        if not hub_file.exists():
            errors.append(f"허브 index.html 없음: {hub_file}")
    else:
        actual_dirs = set()
        hub_text = ""
        errors.append(f"고1 영어 허브 폴더 없음: {HUB}")
    if actual_dirs != set(locals_):
        errors.append(
            f"상세 지역 폴더 불일치: 누락 {len(set(locals_) - actual_dirs)}, "
            f"추가 {len(actual_dirs - set(locals_))}"
        )

    hub_url = canonical()
    card_urls: list[str] = []
    if hub_text:
        verify_head(hub_text, CATEGORY_LABEL, hub_url, "허브", errors)
        expected_hub_breadcrumb = ["홈", "과목별학원", CATEGORY_LABEL]
        if shared.breadcrumb_labels(hub_text) != expected_hub_breadcrumb:
            errors.append(f"허브: 화면 Breadcrumb 불일치 ({shared.breadcrumb_labels(hub_text)})")
        hub_blocks, hub_json_errors = shared.json_ld_blocks(hub_text)
        if hub_json_errors:
            errors.append(f"허브: JSON-LD 파싱 오류 ({hub_json_errors})")
        hub_breadcrumbs = shared.typed_nodes(hub_blocks, "BreadcrumbList")
        if len(hub_breadcrumbs) != 1 or shared.json_breadcrumb(hub_breadcrumbs[0])[0] != expected_hub_breadcrumb:
            errors.append("허브: BreadcrumbList 라벨 불일치")
        card_tags = [
            tag
            for tag in re.findall(r"<a\b[^>]*>", hub_text, flags=re.I | re.S)
            if "subject-town-card" in shared.attrs(tag).get("class", "").split()
        ]
        card_urls = [
            shared.normalize_url(shared.attrs(tag).get("href", ""), hub_url)
            for tag in card_tags
            if shared.attrs(tag).get("href")
        ]
        if len(card_urls) != 371 or len(set(card_urls)) != 371 or set(card_urls) != expected_urls:
            errors.append(
                f"허브 카드 오류: 전체 {len(card_urls)}, 고유 {len(set(card_urls))}, "
                f"URL 차이 {len(set(card_urls) ^ expected_urls)}"
            )
        matching_itemlists = [
            node
            for node in shared.typed_nodes(hub_blocks, "ItemList")
            if set(shared.itemlist_urls(node, hub_url)) == expected_urls
        ]
        if len(matching_itemlists) != 1:
            errors.append(f"허브: 371개 URL ItemList 개수 오류 ({len(matching_itemlists)})")

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
        url = shared.normalize_url(canonical(local))
        expected_title = f"{local} {CATEGORY_LABEL}"
        if not page.exists():
            errors.append(f"{local}: 상세 페이지 없음")
            continue
        detail_count += 1
        text = page.read_text(encoding="utf-8")
        verify_head(text, expected_title, url, local, errors)

        missing_sections = [
            name for name in sorted(REQUIRED_SECTIONS) if not shared.section_html(text, name)
        ]
        if missing_sections:
            errors.append(f"{local}: 고1 영어 상세 필수 섹션 누락 ({missing_sections})")

        descriptions = shared.meta_values(text, "description")
        description = shared.clean_text(descriptions[0]) if len(descriptions) == 1 else ""
        if len(descriptions) != 1 or not description:
            errors.append(f"{local}: meta description 개수/내용 오류 ({descriptions})")
        meta_descriptions.append(description)
        neutral_meta[shared.neutralize(description, row)] += 1
        if not 55 <= len(description) <= 170:
            warnings.append(f"{local}: 메타 설명 길이 {len(description)}자")

        expected_breadcrumb = ["홈", "과목별학원", CATEGORY_LABEL, expected_title]
        if shared.breadcrumb_labels(text) != expected_breadcrumb:
            errors.append(f"{local}: 화면 Breadcrumb 불일치 ({shared.breadcrumb_labels(text)})")

        blocks, json_errors = shared.json_ld_blocks(text)
        if json_errors:
            errors.append(f"{local}: JSON-LD 파싱 오류 ({json_errors})")
        found_types = shared.json_types(blocks)
        missing_types = REQUIRED_TYPES - found_types
        if missing_types:
            errors.append(f"{local}: JSON-LD 타입 누락 ({sorted(missing_types)})")
        forbidden_types = FORBIDDEN_SCHEMA_TYPES & found_types
        if forbidden_types:
            errors.append(f"{local}: 후기/평점 스키마 포함 ({sorted(forbidden_types)})")

        breadcrumb_nodes = shared.typed_nodes(blocks, "BreadcrumbList")
        if len(breadcrumb_nodes) != 1:
            errors.append(f"{local}: BreadcrumbList 개수 오류 ({len(breadcrumb_nodes)})")
        else:
            labels, urls = shared.json_breadcrumb(breadcrumb_nodes[0])
            if labels != expected_breadcrumb:
                errors.append(f"{local}: JSON Breadcrumb 라벨 불일치 ({labels})")
            if not urls or shared.normalize_url(urls[-1], url) != url:
                errors.append(f"{local}: JSON Breadcrumb 마지막 URL이 자기 URL이 아님")

        screen_faq = shared.visible_faq(text)
        faq_nodes = shared.typed_nodes(blocks, "FAQPage")
        schema_faq = shared.json_faq(faq_nodes[0]) if len(faq_nodes) == 1 else []
        if len(faq_nodes) != 1:
            errors.append(f"{local}: FAQPage 개수 오류 ({len(faq_nodes)})")
        if len(screen_faq) != 7:
            errors.append(f"{local}: 화면 FAQ가 7개가 아님 ({len(screen_faq)}개)")
        if screen_faq != schema_faq:
            errors.append(f"{local}: 화면 FAQ와 FAQPage JSON-LD 불일치")

        visible_related = shared.visible_related_urls(text, url)
        related_itemlists = [
            node
            for node in shared.typed_nodes(blocks, "ItemList")
            if str(node.get("@id", "")).endswith("#related-pages")
        ]
        schema_related = shared.itemlist_urls(related_itemlists[0], url) if len(related_itemlists) == 1 else []
        if len(related_itemlists) != 1:
            errors.append(f"{local}: #related-pages ItemList 개수 오류 ({len(related_itemlists)})")
        if visible_related != schema_related:
            errors.append(
                f"{local}: 화면 관련 링크와 ItemList URL/순서 불일치 "
                f"(화면 {len(visible_related)}, JSON {len(schema_related)})"
            )
        if len(visible_related) != len(set(visible_related)):
            errors.append(f"{local}: 화면 관련 링크 중복")

        peers = {target for target in visible_related if target != url and target in expected_urls}
        peer_links[url] = peers
        if len(peers) < 6:
            errors.append(f"{local}: 같은 카테고리 peer가 6개 미만 ({len(peers)}개)")

        previous_url = shared.normalize_url(previous_canonical(local))
        if previous_url not in visible_related:
            errors.append(f"{local}: 같은 동네 중3 영어학원 관련 링크 누락")
        if not (PREVIOUS_HUB / local / "index.html").exists():
            errors.append(f"{local}: 중3 영어학원 링크 대상 페이지 없음")

        for target_url in shared.all_anchor_urls(text, url):
            target_path = shared.local_path_from_url(target_url)
            if target_path is not None:
                internal_targets.add(target_path)

        verify_facts(row, local, text, errors)

        manuscript_raw = shared.manuscript_html(text)
        body = shared.strip_tags(manuscript_raw)
        if len(body) < 1900:
            errors.append(f"{local}: 고1 영어 원고·보강 영역이 너무 짧음 ({len(body)}자)")
        for intent, pattern in HIGH1_INTENT_GROUPS.items():
            if not pattern.search(body):
                errors.append(f"{local}: 고1 영어 학습 의도 필수 요소 누락 ({intent})")
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(body):
                errors.append(f"{local}: 원고에 {label} 표현 포함")
        manuscripts.append(body)
        manuscript_names.append(local)
        manuscript_exact[body] += 1
        for paragraph in re.findall(r"<p\b[^>]*>(.*?)</p>", manuscript_raw, flags=re.I | re.S):
            normalized = shared.neutralize(shared.strip_tags(paragraph), row)
            if len(normalized) >= 45:
                normalized_paragraphs[normalized] += 1

        checklist = shared.checklist_fingerprint(text)
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
    max_neutral_meta = max(neutral_meta.values()) if neutral_meta else 0
    if max_neutral_meta > 8:
        errors.append(f"지역 사실 치환 후 메타 템플릿 최대 반복 {max_neutral_meta}회 (허용 8회)")
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

    shingle_sets = [shared.shingles(body) for body in manuscripts]
    similarities: list[float] = []
    highest = (0.0, "", "")
    for left in range(len(shingle_sets)):
        for right in range(left + 1, len(shingle_sets)):
            union = shingle_sets[left] | shingle_sets[right]
            score = len(shingle_sets[left] & shingle_sets[right]) / len(union) if union else 0.0
            similarities.append(score)
            if score > highest[0]:
                highest = (score, manuscript_names[left], manuscript_names[right])
    if highest[0] > 0.55:
        errors.append(
            f"원고 5-shingle 최대 유사도 과다 {highest[0]:.4f} "
            f"({highest[1]} / {highest[2]}, 허용 0.55)"
        )

    sitemap_urls: list[str] = []
    if not SITEMAP.exists():
        errors.append(f"사이트맵 없음: {SITEMAP}")
    else:
        try:
            sitemap = ET.parse(SITEMAP)
            sitemap_urls = [
                shared.normalize_url(node.text.strip())
                for node in sitemap.getroot().iter()
                if node.tag.endswith("loc") and node.text
            ]
        except ET.ParseError as exc:
            errors.append(f"사이트맵 XML 파싱 실패 ({exc})")
    sitemap_counts = Counter(sitemap_urls)
    sitemap_duplicates = [url for url, count in sitemap_counts.items() if count > 1]
    if sitemap_duplicates:
        errors.append(f"사이트맵 중복 URL {len(sitemap_duplicates)}개")
    missing_sitemap = ({shared.normalize_url(hub_url)} | expected_urls) - set(sitemap_urls)
    if missing_sitemap:
        errors.append(f"고1 영어 사이트맵 URL 누락 {len(missing_sitemap)}개")

    peer_counts = [len(peer_links.get(url, set())) for url in expected_urls]
    print("DETAIL_EXPECTED=371")
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
        print(f"SHINGLE_JACCARD_MEAN={statistics.fmean(similarities):.4f}")
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
