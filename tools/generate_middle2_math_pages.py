from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote

from openpyxl import load_workbook


SITE = Path(__file__).resolve().parents[1]
REFERENCE = SITE.parent / "참고자료"
COMMON = REFERENCE / "공통자료"
MANUSCRIPT = REFERENCE / "원고모음(엑셀)" / "중2 수학학원 원고.xlsx"
CENTER_CSV = COMMON / "센터정보 정리.csv"
IMAGE_CSV = COMMON / "이미지링크.csv"
REPRESENTATIVE_CSV = COMMON / "대표 이미지 url.csv"

DOMAIN = "https://xn--z92bu9jx8cwzc.com"
SITE_NAME = "와와센터"
PHONE_DISPLAY = "010-3957-8283"
PHONE_LINK = "01039578283"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdb2oE5Qk5YS0TfYDxyV1w-IOTkhkjOCmmpAKTI9FmqpVj6Yg/viewform"
SMS_URL = "https://blogsms.net/01039578283"
PUBLISH_DATE = "2026-08-06"

PARENT = "과목별학원"
CATEGORY = "중2수학학원"
CATEGORY_LABEL = "중2 수학학원"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def row_value(row: dict[str, str], needle: str) -> str:
    for key, value in row.items():
        if needle in key:
            return (value or "").strip()
    return ""


def split_items(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[,/|]", value or "") if item.strip()]


def seed_for(*parts: str) -> int:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def choose(local: str, label: str, values: list[str]) -> str:
    return values[seed_for(CATEGORY, local, label) % len(values)]


def canonical(*parts: str) -> str:
    path = "/" + "/".join(part.strip("/") for part in parts if part) + "/"
    return DOMAIN + quote(path, safe="/")


def load_manuscripts() -> list[str]:
    if not MANUSCRIPT.exists():
        raise FileNotFoundError(MANUSCRIPT)
    workbook = load_workbook(MANUSCRIPT, read_only=True, data_only=True)
    sheet = workbook.active
    values = [str(row[0] or "").strip() for row in sheet.iter_rows(values_only=True)]
    workbook.close()
    return values


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def paragraph_signature(value: str, local: str) -> str:
    text = strip_tags(value).replace(local, "<LOCAL>")
    text = re.sub(r"\d+(?:[-~–]\d+)*", "<NUM>", text)
    return text


def repeated_paragraphs(manuscripts: list[str], rows: list[dict[str, str]]) -> set[str]:
    counts: Counter[str] = Counter()
    for raw, row in zip(manuscripts, rows):
        local = row_value(row, "근처 수업가능 동네")
        for body in re.findall(r"<p(?:\s[^>]*)?>(.*?)</p>", raw, re.DOTALL | re.I):
            signature = paragraph_signature(body, local)
            if len(signature) >= 35:
                counts[signature] += 1
    return {signature for signature, count in counts.items() if count > 1}


def sanitize_manuscript(value: str) -> str:
    replacements = {
        "바로 성적이 오르는 방식으로": "학습 과정을 점검하는 방식으로",
        "시험 점수로 연결되도록": "시험 대비 흐름에 반영되도록",
        "점수로 연결되도록": "시험 준비에 반영되도록",
        "다시는 반복되지 않게": "같은 실수가 줄어들도록",
        "실력을 완성합니다": "실력을 단계적으로 정리합니다",
        "성적 향상을": "학습 개선을",
    }
    for before, after in replacements.items():
        value = value.replace(before, after)
    return value


def contextualize_manuscript(
    raw: str,
    row: dict[str, str],
    repeated: set[str],
) -> str:
    local = row_value(row, "근처 수업가능 동네")
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    school_reference = schools[seed_for(local, "school") % len(schools)] if schools else "현재 학교 자료"

    raw = sanitize_manuscript(raw.strip())
    raw = re.sub(
        r'^\s*<main class="article-main">',
        '<section class="shell academy-section article-main manuscript-panel">',
        raw,
        count=1,
        flags=re.I,
    )
    raw = re.sub(r"</main>\s*$", "</section>", raw, count=1, flags=re.I)
    inner_heading = f"{region} {district} {local} 중2 수학 학습 설계"
    raw = re.sub(r"<h1>.*?</h1>", f"<h2>{esc(inner_heading)}</h2>", raw, count=1, flags=re.DOTALL | re.I)

    context_templates = [
        "{local}에서는 {evidence}의 최근 풀이 기록과 학교 진도를 함께 놓고 다음 점검 순서를 정하는 것이 좋습니다.",
        "이 기준을 {local} 학생에게 적용할 때는 {evidence} 자료와 오답 원인을 나란히 확인해야 우선순위가 분명해집니다.",
        "{region} {district} {local} 상담에서는 {evidence}에서 확인되는 단원과 주간 복습 가능 시간을 함께 기록해 두는 편이 실용적입니다.",
        "{local} 학부모는 이 항목을 비교할 때 {evidence} 자료를 어떤 방식으로 수업과 재점검에 반영하는지 질문할 수 있습니다.",
        "학생별 차이를 확인하려면 {local}에서 {evidence}의 풀이 흔적과 혼자 다시 풀 수 있는 문제를 구분해 보는 과정이 필요합니다.",
        "{center} 상담에서는 {evidence}를 기준으로 설명이 필요한 개념과 반복할 문제를 따로 정리할 수 있습니다.",
        "{local}의 실제 학습표에는 {evidence} 점검 결과와 다음 오답 확인 날짜가 함께 적혀야 수업 뒤의 복습까지 이어집니다.",
        "같은 중2 과정이라도 {local} 학생의 학교 진도와 {evidence} 기록에 따라 먼저 보완할 내용은 달라질 수 있습니다.",
        "{district} 지역에서 이 기준을 살필 때는 {evidence} 자료를 근거로 현재 이해와 단순 암기를 구분해 보는 것이 중요합니다.",
        "{local}에서는 설명을 들은 문제와 스스로 해결한 문제를 {evidence}와 함께 비교하면 다음 학습량을 더 구체적으로 정할 수 있습니다.",
    ]
    paragraph_index = 0

    def replace_paragraph(match: re.Match[str]) -> str:
        nonlocal paragraph_index
        attrs, body = match.group(1) or "", match.group(2)
        signature = paragraph_signature(body, local)
        if signature not in repeated or len(signature) < 35:
            paragraph_index += 1
            return match.group(0)
        template = context_templates[seed_for(local, str(paragraph_index), signature) % len(context_templates)]
        context = template.format(
            local=local,
            region=region,
            district=district,
            center=center,
            evidence=school_reference,
        )
        paragraph_index += 1
        return f"<p{attrs}>{body.rstrip()} {esc(context)}</p>"

    return re.sub(
        r"<p(\s[^>]*)?>(.*?)</p>",
        replace_paragraph,
        raw,
        flags=re.DOTALL | re.I,
    )


def load_image_rows() -> dict[str, dict[str, str]]:
    return {row.get("제목", "").strip(): row for row in read_csv(IMAGE_CSV)}


def representative_urls() -> list[str]:
    text = REPRESENTATIVE_CSV.read_text(encoding="utf-8-sig")
    urls = re.findall(r'https://[^"\s,>]+\.(?:jpe?g|png|webp|gif)', text, re.I)
    return list(dict.fromkeys(urls))


def find_parent_page(row: dict[str, str]) -> Path | None:
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    local = row_value(row, "근처 수업가능 동네")
    candidates = [
        SITE / "전국학원" / region / district / local / "index.html",
        SITE / "전국학원" / region / "시" / local / "index.html",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = list((SITE / "전국학원" / region).glob(f"*/{local}/index.html"))
    return matches[0] if matches else None


def parent_relative_url(row: dict[str, str], child: str | None = None) -> str:
    parent = find_parent_page(row)
    if parent:
        relative = parent.parent.relative_to(SITE).as_posix()
    else:
        relative = "/".join(
            [
                "전국학원",
                row_value(row, "지역"),
                row_value(row, "시or구"),
                row_value(row, "근처 수업가능 동네"),
            ]
        )
    if child:
        relative += f"/{child}"
    return "../../../" + "/".join(quote(part, safe="") for part in relative.split("/")) + "/index.html"


def parent_canonical_url(row: dict[str, str], child: str | None = None) -> str:
    parent = find_parent_page(row)
    if parent:
        parts = list(parent.parent.relative_to(SITE).parts)
    else:
        parts = [
            "전국학원",
            row_value(row, "지역"),
            row_value(row, "시or구"),
            row_value(row, "근처 수업가능 동네"),
        ]
    if child:
        parts.append(child)
    return canonical(*parts)


def representative_for(row: dict[str, str], fallback_urls: list[str]) -> str:
    parent = find_parent_page(row)
    candidates: list[Path] = []
    if parent:
        candidates.extend([parent.parent / "중1수학학원" / "index.html", parent])
    for candidate in candidates:
        if not candidate.exists():
            continue
        source = candidate.read_text(encoding="utf-8")
        match = re.search(
            r'data-role="representative-image"[^>]*src="([^"]+)"', source, re.I
        )
        if match:
            return html.unescape(match.group(1))
    local = row_value(row, "근처 수업가능 동네")
    return fallback_urls[seed_for(local, "representative") % len(fallback_urls)]


def map_filename(row: dict[str, str], image_row: dict[str, str]) -> str:
    parent = find_parent_page(row)
    if parent:
        source = parent.read_text(encoding="utf-8")
        match = re.search(r'assets/maps/([^"?#]+)', source, re.I)
        if match and (SITE / "assets" / "maps" / match.group(1)).exists():
            return match.group(1)
    requested = (image_row.get("지도") or "").strip()
    if requested and (SITE / "assets" / "maps" / requested).exists():
        return requested
    slug = row_value(row, "동 영어")
    for suffix in (".jpg", ".jpeg", ".png", ".webp"):
        candidate = SITE / "assets" / "maps" / f"{slug}{suffix}"
        if candidate.exists():
            return candidate.name
    raise FileNotFoundError(f"지도 이미지 없음: {row_value(row, '근처 수업가능 동네')}")


def page_profile(row: dict[str, str]) -> dict[str, str]:
    local = row_value(row, "근처 수업가능 동네")
    profiles = [
        "개념 설명은 이해하지만 문제 조건을 식으로 옮기는 데 시간이 오래 걸리는 학생",
        "숙제는 끝내지만 틀린 문제를 다시 풀지 않아 같은 유형을 반복해서 놓치는 학생",
        "계산은 빠르지만 풀이 단계를 생략해 서술형에서 감점이 생기는 학생",
        "시험 범위가 정해진 뒤에도 복습 순서를 잡지 못해 앞 단원을 놓치는 학생",
        "어려운 문제보다 기본 유형의 작은 실수가 점수를 흔드는 학생",
        "수업 중에는 풀지만 며칠 뒤 혼자 풀 때 풀이가 이어지지 않는 학생",
        "문제량은 충분하지만 풀이 근거를 설명하는 연습이 부족한 학생",
        "현재 진도와 이전 학년의 개념 공백을 함께 점검해야 하는 학생",
        "시험 직전에만 공부해 단원별 오답이 누적되는 학생",
        "풀이 시간이 일정하지 않아 시험 시간 배분이 어려운 학생",
        "응용 문제에서 어떤 개념을 꺼내야 하는지 판단이 느린 학생",
        "학습 계획은 세우지만 완료 여부를 기록하지 않아 복습이 밀리는 학생",
    ]
    priorities = [
        "최근 풀이에서 개념·계산·조건 해석 오류를 먼저 구분합니다.",
        "학교 진도와 누적 오답을 한 표에 놓고 복습 순서를 정합니다.",
        "답만 맞히는 연습보다 풀이 근거를 말하고 쓰는 과정을 확인합니다.",
        "기본 유형의 재풀이 성공 여부를 확인한 뒤 응용 범위를 넓힙니다.",
        "시험일까지 남은 기간을 기준으로 단원별 완료 기준을 나눕니다.",
        "수업 직후·주중·시험 전으로 오답을 다시 볼 시점을 정합니다.",
        "문제별 풀이 시간과 검산 순서를 기록해 시간 배분을 점검합니다.",
        "현재 단원을 설명하는 데 필요한 이전 개념부터 짧게 복원합니다.",
    ]
    checks = [
        "최근 시험지에서 틀린 이유를 학생이 직접 설명할 수 있는지",
        "현재 교재의 진도와 학교 시험 범위가 얼마나 연결되어 있는지",
        "오답을 다시 풀었을 때 해설 없이 해결할 수 있는지",
        "주중에 확보할 수 있는 실제 수학 공부 시간이 어느 정도인지",
        "개념 문제와 응용 문제 중 어느 구간에서 풀이가 멈추는지",
        "풀이 과정에서 부호·조건·계산 순서를 어떻게 검산하는지",
        "시험 전 복습 계획이 단원별 완료 기준으로 적혀 있는지",
        "질문이 생겼을 때 표시하고 다음 수업에서 확인하는 습관이 있는지",
    ]
    return {
        "student": choose(local, "student", profiles),
        "priority": choose(local, "priority", priorities),
        "check": choose(local, "check", checks),
    }


def build_faqs(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    local = row_value(row, "근처 수업가능 동네")
    title = f"{local} 중2 수학학원"
    center = row_value(row, "센터명") or f"{local} 학습센터"
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    grades = split_items(row_value(row, "가능학년\n(수학)"))
    available = "중2" in grades
    school_answer = (
            f"공개 센터 자료에는 {', '.join(schools)} 등이 수업 가능 학교로 안내되어 있습니다. "
        "학교별 시험 범위와 일정은 달라질 수 있으므로 상담할 때 현재 학교 자료를 함께 확인하는 것이 좋습니다."
        if schools
        else "공개 센터 자료에는 중학교명이 별도로 기재되어 있지 않습니다. 학교명을 임의로 단정하지 않고 상담 시 현재 학교와 시험 범위를 확인합니다."
    )
    availability_answer = (
        f"공개된 {center} 가능 학년 정보에 중2 수학이 포함되어 있습니다. 실제 시간표, 반 편성 및 시작 가능일은 변동될 수 있어 상담 시 다시 확인해야 합니다."
        if available
        else f"공개된 {center} 자료에는 수학 가능 학년이 기재되어 있지 않습니다. 중2 수학 개설 여부와 수업 일정은 상담을 통해 확인해야 합니다."
    )
    bank = [
        (
            f"{title} 상담 전에 무엇을 준비하면 좋나요?",
            f"최근 시험지, 현재 수학 교재, 학교 진도와 반복 오답을 준비하면 좋습니다. 특히 {profile['check']}를 메모해 가면 상담 기준을 구체적으로 세울 수 있습니다.",
        ),
        (
            f"{local} 중2 수학학원은 어떤 학생에게 맞는지 어떻게 판단하나요?",
            f"{profile['student']}이라면 진단 과정과 재풀이 확인 방식을 먼저 살펴보세요. 학원 이름이나 문제량만 비교하기보다 학생이 혼자 풀 수 있게 되는 과정을 확인해야 합니다.",
        ),
        (
            "중2 수학 내신은 진도와 복습 중 무엇을 먼저 봐야 하나요?",
            f"현재 학교 진도만 앞서가기보다 이전 단원의 공백과 최근 오답을 먼저 구분해야 합니다. {profile['priority']}",
        ),
        (
            "오답 관리는 어떤 방식인지 확인해야 하나요?",
            "틀린 문제를 다시 푸는 것에 그치지 않고 개념 부족, 계산 실수, 조건 해석, 풀이 순서 중 원인을 구분하는지 확인하세요. 이후 해설 없이 재풀이하는 날짜가 정해지는지도 중요합니다.",
        ),
        (
            "학교별 내신 대비 자료도 확인할 수 있나요?",
            school_answer,
        ),
        (
            "중2 수학 수강 가능 여부는 어디에서 확인하나요?",
            availability_answer,
        ),
        (
            "선행보다 복습이 필요한 학생도 상담할 수 있나요?",
            "현재 학년 진도를 무조건 앞당기기보다 문제를 푸는 데 필요한 이전 개념을 찾아 현재 단원과 연결하는 방향으로 상담할 수 있습니다. 실제 적용 범위는 진단 결과를 바탕으로 확인합니다.",
        ),
        (
            "상담할 때 수업 시간표와 교습비도 확인해야 하나요?",
            "네. 공개된 교습비 자료와 함께 주당 횟수, 시작·종료 시각, 결석·보강 기준, 시험 기간 일정 변동을 같은 표에 적어 비교하는 것이 좋습니다.",
        ),
    ]
    start = seed_for(local, "faq") % len(bank)
    ordered = bank[start:] + bank[:start]
    selected = ordered[:5]
    required = [bank[0], bank[1]]
    for item in required:
        if item not in selected:
            selected[-1] = item
    return selected


def build_parent_notes(row: dict[str, str], profile: dict[str, str]) -> list[str]:
    local = row_value(row, "근처 수업가능 동네")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    options = [
        f"{local} 상담에서는 문제를 많이 푸는지보다 아이가 왜 틀렸는지 설명하고 다시 풀 수 있는지를 확인하는 과정이 중요하다고 느꼈습니다.",
        f"{profile['student']}에게는 진도를 서두르기보다 주간 복습과 오답 확인 날짜를 먼저 정하는 설명이 이해하기 쉬웠습니다.",
        f"{center} 정보를 볼 때 학교 진도, 수학 가능 학년, 교습비 자료를 한 번에 확인하니 상담에서 물어볼 항목을 정리하기 편했습니다.",
        f"{local} 중2 수학학원을 비교하면서 수업 시간뿐 아니라 숙제 실행과 재풀이를 어떻게 확인하는지도 함께 질문해야 한다는 점을 알게 됐습니다.",
        f"최근 시험지를 기준으로 개념 부족과 계산 실수를 나눠 설명하니 아이에게 필요한 복습 순서를 더 구체적으로 생각할 수 있었습니다.",
        f"학교 시험 범위가 나오기 전과 나온 뒤의 공부 계획이 달라야 한다는 안내가 중2 내신 준비 일정을 세우는 데 도움이 됐습니다.",
        f"수업에서 맞힌 문제도 며칠 뒤 혼자 다시 풀 수 있는지 확인해야 한다는 기준이 학원 비교에 유용했습니다.",
        f"{local}에서 통학 가능한지만 보지 않고 종료 시각, 보강 기준과 시험 기간 시간표까지 확인하니 실제 일정 판단이 쉬워졌습니다.",
    ]
    start = seed_for(local, "parent-notes") % len(options)
    return (options[start:] + options[:start])[:3]


def page_json_ld(
    row: dict[str, str],
    description: str,
    page_url: str,
    rep_image: str,
    body_image: str,
    map_image: str,
    faqs: list[tuple[str, str]],
    related: list[tuple[str, str]],
) -> dict:
    local = row_value(row, "근처 수업가능 동네")
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    title = f"{local} 중2 수학학원"
    center = row_value(row, "센터명") or f"{local} 학습센터"
    address = row_value(row, "센터 주소")
    registration = row_value(row, "교육지원청 등록번호")
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    grades = split_items(row_value(row, "가능학년\n(수학)"))
    tuition_url = row_value(row, "센터 교습비")

    organization = {
        "@type": ["EducationalOrganization", "LocalBusiness"],
        "@id": f"{page_url}#organization",
        "name": center,
        "url": page_url,
        "telephone": PHONE_DISPLAY,
        "areaServed": {"@type": "Place", "name": f"{region} {district} {local}"},
        "address": {"@type": "PostalAddress", "streetAddress": address, "addressCountry": "KR"},
        "educationalLevel": grades,
        "knowsAbout": ["중2 수학", "중학교 내신", "개념 진단", "오답 재학습", "학습 플래너"],
        "contactPoint": {
            "@type": "ContactPoint",
            "telephone": f"+82-{PHONE_DISPLAY[1:]}",
            "contactType": "교육 상담",
            "availableLanguage": "Korean",
            "url": FORM_URL,
        },
        "makesOffer": [
            {
                "@type": "Offer",
                "name": f"{title} 학습 상담",
                "category": "중2 수학 학습 진단",
                "url": tuition_url or page_url,
                "itemOffered": {"@id": f"{page_url}#service"},
            }
        ],
    }
    if registration:
        organization["identifier"] = registration
    organization["mentions"] = [
        {"@type": "School", "name": school} for school in schools
    ]

    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{DOMAIN}/#website",
                "url": f"{DOMAIN}/",
                "name": SITE_NAME,
                "inLanguage": "ko-KR",
            },
            organization,
            {
                "@type": "WebPage",
                "@id": f"{page_url}#webpage",
                "url": page_url,
                "name": title,
                "description": description,
                "inLanguage": "ko-KR",
                "isPartOf": {"@id": f"{DOMAIN}/#website"},
                "breadcrumb": {"@id": f"{page_url}#breadcrumb"},
                "mainEntity": {"@id": f"{page_url}#service"},
                "primaryImageOfPage": {"@id": f"{page_url}#primaryimage"},
                "about": [
                    {"@type": "Place", "name": f"{region} {district} {local}"},
                    {"@type": "Thing", "name": "중2 수학학원"},
                    {"@type": "Thing", "name": "중학교 2학년 수학 내신"},
                ],
                "mentions": [
                    {"@type": "EducationalOrganization", "name": center},
                    *[{"@type": "School", "name": school} for school in schools],
                ],
                "hasPart": [
                    {"@type": "WebPageElement", "name": name}
                    for name in ["핵심 답변", "중2 수학 학습 설계", "센터 정보", "상담 전 체크리스트", "FAQ", "학부모 상담 관점", "내부링크"]
                ],
            },
            {
                "@type": "ImageObject",
                "@id": f"{page_url}#primaryimage",
                "url": rep_image,
                "caption": f"{title} {SITE_NAME} 대표",
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{page_url}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{DOMAIN}/"},
                    {"@type": "ListItem", "position": 2, "name": PARENT, "item": canonical(PARENT)},
                    {"@type": "ListItem", "position": 3, "name": CATEGORY_LABEL, "item": canonical(PARENT, CATEGORY)},
                    {"@type": "ListItem", "position": 4, "name": title, "item": page_url},
                ],
            },
            {
                "@type": "Service",
                "@id": f"{page_url}#service",
                "name": f"{title} 학습 상담 및 안내",
                "serviceType": "중학교 2학년 수학 학습관리",
                "provider": {"@id": f"{page_url}#organization"},
                "areaServed": {"@type": "Place", "name": f"{region} {district} {local}"},
                "audience": {"@type": "EducationalAudience", "educationalRole": "중학교 2학년 학생 및 학부모"},
                "about": ["중2 수학", "내신 대비", "오답 관리", "학습 습관"],
            },
            {
                "@type": "Article",
                "@id": f"{page_url}#article",
                "url": page_url,
                "headline": title,
                "description": description,
                "datePublished": PUBLISH_DATE,
                "dateModified": PUBLISH_DATE,
                "inLanguage": "ko-KR",
                "mainEntityOfPage": {"@id": f"{page_url}#webpage"},
                "author": {"@id": f"{page_url}#organization"},
                "publisher": {"@id": f"{page_url}#organization"},
                "image": [rep_image, body_image, map_image],
                "articleSection": [region, district, local, "중2 수학", "내신 대비", "오답 재학습"],
                "about": [{"@type": "Thing", "name": title}],
                "mentions": [{"@type": "EducationalOrganization", "name": center}],
            },
            {
                "@type": "FAQPage",
                "@id": f"{page_url}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    }
                    for question, answer in faqs
                ],
            },
            {
                "@type": "ItemList",
                "@id": f"{page_url}#related-pages",
                "name": f"{local} 관련 학습 페이지",
                "itemListElement": [
                    {"@type": "ListItem", "position": index, "name": name, "url": url}
                    for index, (name, url) in enumerate(related, 1)
                ],
            },
        ],
    }


def head_html(title: str, description: str, page_url: str, image: str, schema: dict, asset_prefix: str, og_type: str = "article") -> str:
    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} | {SITE_NAME}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{page_url}">
  <meta property="og:type" content="{esc(og_type)}">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:title" content="{esc(title)} | {SITE_NAME}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{page_url}">
  <meta property="og:image" content="{esc(image)}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{asset_prefix}assets/favicon.png" type="image/png">
  <link rel="stylesheet" href="{asset_prefix}assets/site.css">
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(",", ":"))}</script>
</head>'''


def nav_html(prefix: str, active: str) -> str:
    items = [
        ("홈", f"{prefix}index.html", "home"),
        ("학습가이드", f"{prefix}학습가이드/index.html", "guide"),
        ("상담문의", f"{prefix}상담문의/index.html", "contact"),
        ("과목별학원", f"{prefix}과목별학원/index.html", "subject"),
        ("전국학원", f"{prefix}전국학원/index.html", "nationwide"),
    ]
    links = "".join(
        f'<a{" class=\"active\"" if key == active else ""} href="{href}">{label}</a>'
        for label, href, key in items
    )
    return f'''  <a class="skip-link" href="#main">본문 바로가기</a>
  <header class="site-header">
    <a class="brand" href="{prefix}index.html" aria-label="와와센터 홈"><span class="brand-mark">W</span><span><strong>와와센터</strong><small>Learning Control Studio</small></span></a>
    <nav class="top-nav" aria-label="상단 메뉴">{links}</nav>
  </header>'''


def footer_html(asset_prefix: str) -> str:
    return f'''  <aside class="floating-actions" aria-label="빠른 상담 버튼"><a href="tel:{PHONE_LINK}">전화문의</a><a href="{SMS_URL}" target="_blank" rel="noopener noreferrer">문자문의</a><a href="{FORM_URL}" target="_blank" rel="noopener noreferrer">상담신청</a></aside>
  <footer class="site-footer"><div><strong>{SITE_NAME}</strong><p>영어·수학·국어 학습코칭 안내</p></div><a href="tel:{PHONE_LINK}">{PHONE_DISPLAY}</a></footer>
  <script src="{asset_prefix}assets/site.js"></script>'''


def detail_html(
    row: dict[str, str],
    manuscript: str,
    image_row: dict[str, str],
    rep_image: str,
    map_name: str,
    index: int,
    rows: list[dict[str, str]],
) -> str:
    local = row_value(row, "근처 수업가능 동네")
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    address = row_value(row, "센터 주소")
    registration_name = row_value(row, "교육지원청명칭")
    registration_number = row_value(row, "교육지원청 등록번호")
    tuition = row_value(row, "센터 교습비")
    grades = split_items(row_value(row, "가능학년\n(수학)"))
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    available = "중2" in grades
    title = f"{local} 중2 수학학원"
    profile = page_profile(row)
    description = (
        f"{region} {district} {local} 중2 수학학원 선택을 위해 {center} 공개 정보와 "
        f"중2 내신·오답 관리 기준, 수업 가능 학교와 상담 체크 항목을 정리했습니다."
    )
    page_url = canonical(PARENT, CATEGORY, local)
    body_name = "seoul.jpg" if region == "서울" else "local.jpg"
    body_url = f"{DOMAIN}/assets/centers/common/{body_name}"
    map_url = f"{DOMAIN}/assets/maps/{quote(map_name)}"

    parent_link = parent_relative_url(row)
    middle1_link = parent_relative_url(row, "중1수학학원")
    previous_local = row_value(rows[index - 1], "근처 수업가능 동네") if index else row_value(rows[-1], "근처 수업가능 동네")
    next_local = row_value(rows[(index + 1) % len(rows)], "근처 수업가능 동네")
    related = [
        (CATEGORY_LABEL, canonical(PARENT, CATEGORY)),
        (f"{local} 중2 영어학원", canonical(PARENT, "중2영어학원", local)),
        (f"{local}학원", parent_canonical_url(row)),
        (f"{local} 중1 수학학원", parent_canonical_url(row, "중1수학학원")),
        (f"{previous_local} 중2 수학학원", canonical(PARENT, CATEGORY, previous_local)),
        (f"{next_local} 중2 수학학원", canonical(PARENT, CATEGORY, next_local)),
    ]
    faqs = build_faqs(row, profile)
    notes = build_parent_notes(row, profile)
    schema = page_json_ld(row, description, page_url, rep_image, body_url, map_url, faqs, related)

    school_html = (
        "".join(f"<span>{esc(school)}</span>" for school in schools)
        if schools
        else "<p class=\"subject-empty-note\">공개 자료에 중학교명이 별도로 기재되어 있지 않아 상담 시 현재 학교와 시험 범위를 확인합니다.</p>"
    )
    grade_html = "".join(f"<span>{esc(grade)}</span>" for grade in grades) if grades else "<span>상담 확인</span>"
    availability_text = (
        f"공개 센터 자료의 수학 가능 학년에 중2가 포함되어 있습니다. 실제 반 편성과 일정은 {center} 상담에서 확인해야 합니다."
        if available
        else f"공개된 {center} 자료에는 수학 가능 학년이 비어 있어 중2 수학 개설 여부를 상담에서 확인해야 합니다."
    )
    faq_html = "".join(
        f"<details><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>"
        for question, answer in faqs
    )
    notes_html = "".join(f"<article class=\"subject-parent-note\"><p>{esc(note)}</p></article>" for note in notes)
    tuition_html = (
        f'<a class="btn ghost" href="{esc(tuition)}" target="_blank" rel="noopener noreferrer">센터 교습비 자료 확인</a>'
        if tuition
        else '<span class="subject-empty-note">교습비 자료는 상담 시 확인해 주세요.</span>'
    )
    manuscript = contextualize_manuscript(manuscript, row, REPEATED_SIGNATURES)

    return f'''{head_html(title, description, page_url, rep_image, schema, "../../../")}
<body>
{nav_html("../../../", "subject")}
  <main id="main">
    <nav class="breadcrumb-box" aria-label="현재 위치"><a href="../../../index.html">홈</a><span>›</span><a href="../../index.html">과목별학원</a><span>›</span><a href="../index.html">중2 수학학원</a><span>›</span>{esc(title)}</nav>

    <section class="sub-hero shell directory-hero subject-detail-hero">
      <div class="reveal">
        <p class="eyebrow">MIDDLE SCHOOL MATH GUIDE</p>
        <h1>{esc(title)}</h1>
        <p>{esc(description)}</p>
        <div class="hero-actions"><a class="btn primary" href="{FORM_URL}" target="_blank" rel="noopener noreferrer">상담 준비하기</a><a class="btn ghost" href="../index.html">다른 지역 찾기</a></div>
      </div>
      <div class="stat-console reveal"><div class="stat-pill"><strong>{esc(local)}</strong><span>{esc(region)} {esc(district)}</span></div><div class="stat-pill"><strong>{'확인' if not available else '중2'}</strong><span>{'개설 여부 상담 필요' if not available else '수학 가능 학년 기재'}</span></div></div>
    </section>

    <section class="shell csv-body-stack csv-top-media local-media-section subject-media" aria-label="{esc(title)} 이미지 안내">
      <img data-role="representative-image" style="display:none;" src="{esc(rep_image)}" alt="{esc(title)} {SITE_NAME} 대표">
      <figure class="csv-media-card"><img src="../../../assets/centers/common/{body_name}" alt="{esc(title)} 본문 {SITE_NAME}" loading="eager" decoding="async"></figure>
      <figure class="csv-media-card"><img src="../../../assets/maps/{quote(map_name)}" alt="{esc(title)} 지도 {SITE_NAME}" loading="lazy" decoding="async"></figure>
    </section>

    <section class="shell geo-summary-panel subject-answer-panel reveal" aria-labelledby="answer-title">
      <p class="eyebrow">핵심 답변</p>
      <h2 id="answer-title">{esc(title)}, 무엇부터 확인해야 할까요?</h2>
      <p>{esc(local)}에서 중2 수학학원을 비교할 때는 현재 진도만 보지 말고 이전 개념 공백, 풀이 과정, 오답 재확인 방식과 시험 전 계획을 함께 살펴야 합니다. {esc(profile['student'])}이라면 특히 관리 기록이 다음 수업에 어떻게 반영되는지 확인하는 것이 좋습니다.</p>
      <div class="geo-fact-grid">
        <article class="geo-fact-card"><span>현재 학생 상황</span><strong>{esc(profile['student'])}</strong></article>
        <article class="geo-fact-card"><span>우선 확인</span><strong>{esc(profile['priority'])}</strong></article>
        <article class="geo-fact-card"><span>상담 질문</span><strong>{esc(profile['check'])}</strong></article>
      </div>
    </section>

    {manuscript}

    <section class="shell academy-section subject-local-facts reveal" aria-labelledby="local-facts-title">
      <div class="section-heading"><p class="eyebrow">VERIFIED LOCAL FACTS</p><h2 id="local-facts-title">{esc(local)} 센터 정보와 수업 확인 항목</h2><p>공개된 센터 자료만 사용했으며, 기재되지 않은 학교나 운영 조건은 임의로 만들지 않았습니다.</p></div>
      <div class="subject-fact-grid">
        <article><span>센터</span><strong>{esc(center)}</strong><p>{esc(address) if address else '주소는 상담 시 확인해 주세요.'}</p></article>
        <article><span>중2 수학 가능 학년</span><strong>{'자료에 기재됨' if available else '상담 확인 필요'}</strong><p>{esc(availability_text)}</p></article>
        <article><span>교육지원청 등록 정보</span><strong>{esc(registration_name) if registration_name else '상담 확인'}</strong><p>{esc(registration_number) if registration_number else '공개 자료에 등록번호가 별도로 기재되어 있지 않습니다.'}</p></article>
      </div>
      <div class="subject-school-panel"><h3>공개 자료의 중학교 안내</h3><div class="subject-school-tags">{school_html}</div></div>
      <div class="subject-grade-panel"><h3>공개 자료의 수학 가능 학년</h3><div class="subject-school-tags">{grade_html}</div>{tuition_html}</div>
    </section>

    <section class="shell geo-checklist-panel reveal" aria-labelledby="checklist-title">
      <p class="eyebrow">상담 전 체크리스트</p>
      <h2 id="checklist-title">{esc(title)} 비교 전에 적어둘 내용</h2>
      <div class="geo-checklist-grid">
        <article class="geo-check-card"><b>01</b><strong>학교 자료</strong><p>최근 시험지, 현재 교재와 학교 진도를 준비합니다.</p></article>
        <article class="geo-check-card"><b>02</b><strong>오답 원인</strong><p>{esc(profile['check'])}를 확인합니다.</p></article>
        <article class="geo-check-card"><b>03</b><strong>주간 일정</strong><p>수업 외에 복습할 수 있는 실제 시간을 계산합니다.</p></article>
        <article class="geo-check-card"><b>04</b><strong>운영 조건</strong><p>반 편성, 시간표, 결석·보강 기준과 교습비를 확인합니다.</p></article>
      </div>
    </section>

    <section class="shell academy-section local-proof-section" aria-labelledby="faq-title">
      <div class="section-heading"><p class="eyebrow">FAQ & PARENT VIEW</p><h2 id="faq-title">{esc(title)} 자주 묻는 질문과 학부모 상담 관점</h2><p>질문과 답변은 같은 내용으로 JSON-LD에도 반영했습니다. 아래 상담 관점은 특정 성과를 보장하는 후기가 아니라 학부모가 비교할 때 참고할 수 있도록 재구성한 예시입니다.</p></div>
      <div class="local-proof-layout">
        <section class="local-faq-card" aria-label="{esc(title)} 자주 묻는 질문"><div class="faq-list">{faq_html}</div></section>
        <aside class="local-review-card" aria-label="{esc(title)} 학부모 상담 관점"><div class="review-list">{notes_html}</div></aside>
      </div>
    </section>

    <section class="shell local-page-nav reveal" aria-labelledby="related-title">
      <div class="section-heading"><p class="eyebrow">RELATED GUIDES</p><h2 id="related-title">{esc(local)} 및 인접 학습 페이지</h2><p>과목 중심 안내와 기존 지역 중심 안내를 함께 확인할 수 있습니다.</p></div>
      <div class="child-button-grid">
        <a class="child-page-button" href="../index.html">중2 수학학원 지역 목록</a>
        <a class="child-page-button" href="../../중2영어학원/{quote(local, safe='')}/index.html">{esc(local)} 중2 영어학원</a>
        <a class="child-page-button" href="{parent_link}">{esc(local)}학원</a>
        <a class="child-page-button" href="{middle1_link}">{esc(local)} 중1 수학학원</a>
        <a class="child-page-button" href="../{quote(previous_local, safe='')}/index.html">{esc(previous_local)} 중2 수학학원</a>
        <a class="child-page-button" href="../{quote(next_local, safe='')}/index.html">{esc(next_local)} 중2 수학학원</a>
      </div>
    </section>
  </main>
{footer_html("../../../")}
</body>
</html>
'''


def collection_schema(title: str, description: str, url: str, breadcrumbs: list[tuple[str, str]], items: list[tuple[str, str]], faqs: list[tuple[str, str]] | None = None) -> dict:
    graph: list[dict] = [
        {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "url": f"{DOMAIN}/", "name": SITE_NAME, "inLanguage": "ko-KR"},
        {
            "@type": "CollectionPage",
            "@id": f"{url}#webpage",
            "url": url,
            "name": title,
            "description": description,
            "inLanguage": "ko-KR",
            "isPartOf": {"@id": f"{DOMAIN}/#website"},
            "breadcrumb": {"@id": f"{url}#breadcrumb"},
            "mainEntity": {"@id": f"{url}#itemlist"},
        },
        {
            "@type": "BreadcrumbList",
            "@id": f"{url}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": position, "name": name, "item": item_url}
                for position, (name, item_url) in enumerate(breadcrumbs, 1)
            ],
        },
        {
            "@type": "ItemList",
            "@id": f"{url}#itemlist",
            "name": title,
            "numberOfItems": len(items),
            "itemListElement": [
                {"@type": "ListItem", "position": position, "name": name, "url": item_url}
                for position, (name, item_url) in enumerate(items, 1)
            ],
        },
    ]
    if faqs:
        graph.append(
            {
                "@type": "FAQPage",
                "@id": f"{url}#faq",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in faqs
                ],
            }
        )
    return {"@context": "https://schema.org", "@graph": graph}


def category_page() -> str:
    title = "과목별학원"
    description = "학년과 과목을 먼저 선택한 뒤 지역별 학습 안내를 찾을 수 있도록 정리한 전문수업.com 과목별 학원 허브입니다."
    url = canonical(PARENT)
    items = [
        (CATEGORY_LABEL, canonical(PARENT, CATEGORY)),
        ("중2 영어학원", canonical(PARENT, "중2영어학원")),
    ]
    schema = collection_schema(title, description, url, [("홈", f"{DOMAIN}/"), (title, url)], items)
    return f'''{head_html(title, description, url, f"{DOMAIN}/assets/generated/academy-hero-v2.webp", schema, "../", "website")}
<body>
{nav_html("../", "subject")}
  <main id="main">
    <nav class="breadcrumb-box" aria-label="현재 위치"><a href="../index.html">홈</a><span>›</span>과목별학원</nav>
    <section class="sub-hero shell directory-hero">
      <div class="reveal"><p class="eyebrow">SUBJECT ACADEMY DIRECTORY</p><h1>과목별학원</h1><p>{esc(description)}</p></div>
      <div class="stat-console reveal"><div class="stat-pill"><strong>학년·과목</strong><span>검색 의도에 맞춘 안내</span></div><div class="stat-pill"><strong>371</strong><span>지역별 상세 연결</span></div></div>
    </section>
    <section class="shell academy-section subject-category-section">
      <div class="section-heading"><p class="eyebrow">CURRENT GUIDE</p><h2>현재 확인할 수 있는 학년·과목</h2><p>실제로 생성된 허브만 표시하며, 존재하지 않는 카테고리는 노출하지 않습니다.</p></div>
      <div class="subject-category-grid">
        <a class="subject-category-card" href="중2수학학원/index.html"><span>중학교 2학년</span><strong>중2 수학학원</strong><p>내신 준비, 개념 공백, 풀이 과정과 오답 재학습 기준을 지역별로 확인합니다.</p><b>371개 지역 보기 →</b></a>
        <a class="subject-category-card" href="중2영어학원/index.html"><span>중학교 2학년</span><strong>중2 영어학원</strong><p>교과서·문법·독해·어휘와 서술형 준비 기준을 지역별로 확인합니다.</p><b>371개 지역 보기 →</b></a>
      </div>
    </section>
  </main>
{footer_html("../")}
</body>
</html>
'''


def hub_page(rows: list[dict[str, str]]) -> str:
    title = "중2 수학학원 지역별 안내"
    description = "371개 지역의 중2 수학학원 선택 기준과 공개 센터 정보, 학교·가능 학년·교습비 확인 항목을 지역별로 정리했습니다."
    url = canonical(PARENT, CATEGORY)
    items = [
        (f"{row_value(row, '근처 수업가능 동네')} 중2 수학학원", canonical(PARENT, CATEGORY, row_value(row, "근처 수업가능 동네")))
        for row in rows
    ]
    faqs = [
        ("지역별 중2 수학학원 페이지는 어떤 기준으로 구성했나요?", "센터정보 정리 자료의 지역, 센터명, 주소, 실제 기재 학교, 가능 학년과 교습비 링크를 기준으로 구성했습니다."),
        ("수학 가능 학년이 비어 있는 지역도 있나요?", "네. 공개 자료에 수학 가능 학년이 없는 지역은 개설을 임의로 단정하지 않고 상담 확인 필요로 표시했습니다."),
        ("동네 이름으로 바로 찾을 수 있나요?", "검색창에 동네명, 시군구 또는 센터명을 입력하면 해당 지역 버튼만 확인할 수 있습니다."),
    ]
    schema = collection_schema(
        title,
        description,
        url,
        [("홈", f"{DOMAIN}/"), (PARENT, canonical(PARENT)), (CATEGORY_LABEL, url)],
        items,
        faqs,
    )
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row_value(row, "지역")][row_value(row, "시or구")].append(row)

    region_sections: list[str] = []
    for region_index, (region, districts) in enumerate(grouped.items()):
        count = sum(len(values) for values in districts.values())
        district_sections: list[str] = []
        for district, district_rows in districts.items():
            cards = []
            for row in district_rows:
                local = row_value(row, "근처 수업가능 동네")
                center = row_value(row, "센터명")
                schools = row_value(row, "타깃학교\n(중)")
                search = " ".join([region, district, local, center, schools])
                cards.append(
                    f'<a class="subject-town-card" data-subject-town data-search="{esc(search)}" href="{quote(local, safe="")}/index.html"><strong>{esc(local)}</strong><span>{esc(district)} · 중2 수학</span></a>'
                )
            district_sections.append(
                f'<section class="subject-district-group" data-subject-district><h3>{esc(district)} <small>{len(district_rows)}개 지역</small></h3><div class="subject-town-grid">{"".join(cards)}</div></section>'
            )
        region_sections.append(
            f'<details class="subject-region-group" data-subject-region{" open" if region_index == 0 else ""}><summary><span>{esc(region)}</span><b>{count}개 지역</b></summary><div class="subject-region-body">{"".join(district_sections)}</div></details>'
        )
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)
    return f'''{head_html(title, description, url, f"{DOMAIN}/assets/generated/academy-hero-v2.webp", schema, "../../", "website")}
<body>
{nav_html("../../", "subject")}
  <main id="main">
    <nav class="breadcrumb-box" aria-label="현재 위치"><a href="../../index.html">홈</a><span>›</span><a href="../index.html">과목별학원</a><span>›</span>중2 수학학원</nav>
    <section class="sub-hero shell directory-hero">
      <div class="reveal"><p class="eyebrow">MIDDLE SCHOOL MATH DIRECTORY</p><h1>중2 수학학원</h1><p>{esc(description)}</p></div>
      <div class="stat-console reveal"><div class="stat-pill"><strong>371</strong><span>동네별 학습 안내</span></div><div class="stat-pill"><strong>13</strong><span>광역 지역 구분</span></div></div>
    </section>
    <section class="shell academy-section subject-directory" data-subject-directory>
      <div class="section-heading"><p class="eyebrow">LOCAL SEARCH</p><h2>동네 이름으로 중2 수학학원 찾기</h2><p>광역·시군구별로 접어 정리했습니다. 동네명이나 센터명을 검색하면 해당 결과만 남습니다.</p></div>
      <div class="subject-search-box"><label for="subject-town-search">동네·시군구·센터 검색</label><input id="subject-town-search" type="search" placeholder="예: 명일동, 강동구, 명일점" autocomplete="off" data-subject-search><p aria-live="polite" data-subject-search-status>전체 371개 지역</p></div>
      <div class="subject-region-list">{"".join(region_sections)}</div>
    </section>
    <section class="shell academy-section subject-hub-faq"><div class="section-heading"><p class="eyebrow">DIRECTORY FAQ</p><h2>지역 페이지 이용 전에 확인하세요</h2></div><div class="faq-list">{faq_html}</div></section>
  </main>
{footer_html("../../")}
</body>
</html>
'''


def update_sitemap(urls: list[tuple[str, str, str]]) -> None:
    path = SITE / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    existing = set(re.findall(r"<loc>(.*?)</loc>", text))
    additions: list[str] = []
    for url, changefreq, priority in urls:
        if url in existing:
            continue
        additions.append(
            "  <url>\n"
            f"    <loc>{url}</loc>\n"
            f"    <lastmod>{PUBLISH_DATE}</lastmod>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>\n"
        )
    if additions:
        text = text.replace("</urlset>", "".join(additions) + "</urlset>")
        path.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    global REPEATED_SIGNATURES
    rows = read_csv(CENTER_CSV)
    manuscripts = load_manuscripts()
    REPEATED_SIGNATURES = repeated_paragraphs(manuscripts, rows)
    if len(rows) != 371 or len(manuscripts) != 371:
        raise ValueError(f"371개 자료 불일치: center={len(rows)}, manuscript={len(manuscripts)}")
    if len({row_value(row, '근처 수업가능 동네') for row in rows}) != 371:
        raise ValueError("동네명이 중복되었습니다.")

    image_rows = load_image_rows()
    fallback_representatives = representative_urls()
    if not fallback_representatives:
        raise ValueError("대표 이미지 URL을 찾지 못했습니다.")

    target = SITE / PARENT / CATEGORY
    target.mkdir(parents=True, exist_ok=True)
    (SITE / PARENT).mkdir(parents=True, exist_ok=True)
    (SITE / PARENT / "index.html").write_text(category_page(), encoding="utf-8", newline="\n")
    (target / "index.html").write_text(hub_page(rows), encoding="utf-8", newline="\n")

    sitemap_urls = [
        (canonical(PARENT), "weekly", "0.9"),
        (canonical(PARENT, CATEGORY), "weekly", "0.9"),
    ]
    for index, (row, manuscript) in enumerate(zip(rows, manuscripts)):
        local = row_value(row, "근처 수업가능 동네")
        image_row = image_rows.get(local, {})
        map_name = map_filename(row, image_row)
        rep_image = representative_for(row, fallback_representatives)
        folder = target / local
        folder.mkdir(parents=True, exist_ok=True)
        page = detail_html(row, manuscript, image_row, rep_image, map_name, index, rows)
        (folder / "index.html").write_text(page, encoding="utf-8", newline="\n")
        sitemap_urls.append((canonical(PARENT, CATEGORY, local), "monthly", "0.8"))

    update_sitemap(sitemap_urls)
    print(f"generated_details={len(rows)}")
    print(f"generated_total={len(rows) + 2}")
    print(f"target={target}")


REPEATED_SIGNATURES: set[str] = set()


if __name__ == "__main__":
    main()
