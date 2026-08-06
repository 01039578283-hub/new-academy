from __future__ import annotations

"""검증된 전국학원 센터 사실과 영어 학습 구조로 고1 영어 371개 페이지를 생성한다.

엑셀 원고는 사용하지 않는다. 기존 중등 영어 생성기의 데이터 검증·내부링크 골격만
재사용하고, 고교 첫 내신 적응·모의고사·긴 지문·서술형·시간 관리에 맞는 별도 원고를
구성한다. ``전국학원`` 아래의 기존 파일은 읽기만 하며 수정하지 않는다.
"""

import json
import re
from pathlib import Path
from urllib.parse import quote

import generate_middle3_english_pages as middle3


engine = middle3.source
base = middle3.base
SITE = base.SITE
DOMAIN = base.DOMAIN
SITE_NAME = base.SITE_NAME
PARENT = "과목별학원"
CATEGORY = "고1영어학원"
CATEGORY_LABEL = "고1 영어학원"
PUBLISH_DATE = "2026-08-07"
PREVIOUS_LABEL_TOKEN = "__SAME_TOWN_MIDDLE3_ENGLISH__"
MIDDLE2_MATH_LABEL_TOKEN = "__SAME_TOWN_MIDDLE2_MATH__"
MIDDLE2_MATH_PATH_TOKEN = "__MIDDLE2_MATH_PATH__"

esc = base.esc
row_value = base.row_value
split_items = base.split_items
canonical = base.canonical

_middle2_profile = engine.page_profile
_middle2_study_record = engine.build_distinctive_study_record
_middle2_enrichment = engine.build_english_enrichment
_middle2_manuscript = engine.build_manuscript
_middle2_faqs = engine.build_faqs
_middle2_parent_notes = engine.build_parent_notes
_middle2_checklist = engine.build_checklist
_middle2_json_ld = engine.page_json_ld
_middle2_detail_html = engine.detail_html
_middle2_hub_page = engine.hub_page


def choose(local: str, label: str, values: list[str]) -> str:
    return values[base.seed_for(CATEGORY, local, label) % len(values)]


def adapt_high1(value):
    """중2 골격의 페이지 문맥을 고1 영어로 바꾸되 이전 단계 링크는 별도로 보존한다."""
    value = middle3.adapt_middle3(value)
    if isinstance(value, dict):
        return {key: adapt_high1(item) for key, item in value.items()}
    if isinstance(value, list):
        return [adapt_high1(item) for item in value]
    if isinstance(value, tuple):
        return tuple(adapt_high1(item) for item in value)
    if not isinstance(value, str):
        return value
    replacements = (
        ("중학교 3학년", "고등학교 1학년"),
        ("중3 영어", "고1 영어"),
        ("중3 학생", "고1 학생"),
        ("중3 과목", "고1 과목"),
        ("중3", "고1"),
        ("고교 진입 전", "고교 첫 학년 적응"),
        ("고등학교 진입 전", "고등학교 1학년 적응"),
        ("중학교 영어 내신", "고등학교 1학년 영어 내신"),
        ("중학교 안내", "고등학교 안내"),
        ("개 중학교", "개 고등학교"),
        ("중학교명이", "고등학교명이"),
        ("중학교명", "고등학교명"),
        ("현재 중학교", "현재 고등학교"),
        ("중학교 자료", "고등학교 자료"),
        ("중학교 교과서", "고등학교 교과서"),
        ("MIDDLE SCHOOL ENGLISH GUIDE", "HIGH SCHOOL FIRST-YEAR ENGLISH GUIDE"),
        ("MIDDLE SCHOOL ENGLISH DIRECTORY", "HIGH SCHOOL FIRST-YEAR ENGLISH DIRECTORY"),
    )
    for before, after in replacements:
        value = value.replace(before, after)
    return value


def high1_row(row: dict[str, str], index: int | None = None) -> dict[str, str]:
    """중2 엔진이 고1 가능 여부와 고등학교 자료를 판정하도록 사실 열만 대응한다."""
    proxy = dict(row)
    grades = split_items(row_value(row, "가능학년\n(영어)"))
    proxy_grades = ["중2" if grade == "고1" else ("중학교 2학년" if grade == "중2" else grade) for grade in grades]
    proxy["가능학년\n(영어)"] = ", ".join(proxy_grades)
    proxy["타깃학교\n(중)"] = row_value(row, "타깃학교\n(고)")
    proxy["__high1_original_grades"] = json.dumps(grades, ensure_ascii=False)
    proxy["__high1_index"] = str(index or 0)
    return proxy


def original_grades(row: dict[str, str]) -> list[str]:
    raw = row.get("__high1_original_grades", "")
    if raw:
        try:
            return list(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            pass
    return split_items(row_value(row, "가능학년\n(영어)"))


def meta_description(row: dict[str, str], page_index: int) -> str:
    local = row_value(row, "근처 수업가능 동네")
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    openings = [
        f"{region} {district} {local} 고1 영어학원 비교를 위해",
        f"{local} 고1 영어의 첫 내신과 모의고사 준비를 시작하기 전에",
        f"{center} 공개 정보와 학생의 실제 영어 답안을 바탕으로",
        f"{region} {local}에서 고등학교 1학년 영어 수업을 살필 때",
        f"{district} {local} 고1 영어 상담을 준비하며",
        f"{local} 학생의 고교 영어 적응 순서를 정할 수 있도록",
        f"공개된 {center} 자료 범위에서",
        f"{local} 고1 영어학원 선택 기준으로",
    ]
    focuses = [
        "학교 내신 자료, 모의고사, 어휘 재현, 구문 분석, 독해 근거와 서술형 수정의 확인 순서를 정리했습니다.",
        "중학교 누적 공백과 고교 첫 시험 준비를 구분하고 긴 지문과 시간 배분을 점검하는 기준을 안내합니다.",
        "검증된 센터·고등학교·가능 학년 정보와 내신·모의평가 학습 체크리스트를 함께 구성했습니다.",
        "어휘에서 문장 구조, 독해 근거, 수행평가와 서술형 재작성으로 이어지는 주간 학습 흐름을 설명합니다.",
        "학교 자료와 첫 모의고사의 오류를 나눠 읽고 실제 복습 시간 안에서 우선순위를 정하는 방법을 담았습니다.",
        "점수나 학교별 출제를 단정하지 않고 현재 답안과 공개 정보로 확인할 상담 항목을 제시합니다.",
        "고1 가능 학년, 공개 학교와 교습비를 확인하면서 내신 적응과 학습 시간 관리 기준을 함께 살펴봅니다.",
        "무리한 선행보다 고교 문장에 중학교 영어 지식을 적용하고 다시 설명하는 과정을 비교 기준으로 안내합니다.",
    ]
    return f"{openings[page_index % len(openings)]} {focuses[(page_index // len(openings)) % len(focuses)]}"


def page_profile(row: dict[str, str]) -> dict[str, str]:
    local = row_value(row, "근처 수업가능 동네")
    profile = adapt_high1(_middle2_profile(row))
    profile["high1_focus"] = choose(local, "high1-focus", [
        "중학교에서 배운 문법이 긴 고교 문장과 선택지 판단에 실제로 이어지는지 확인합니다.",
        "첫 내신 자료와 모의고사 답안을 나눠 보고 공통으로 흔들린 어휘·구문 지점을 찾습니다.",
        "본문 암기 결과와 문장 구조를 설명하는 결과를 분리해 변형 문항 준비 상태를 살핍니다.",
        "문맥 속 어휘 의미와 연결어·대명사 근거를 표시해 긴 지문에서 막히는 지점을 좁힙니다.",
        "수행평가와 서술형은 답을 외우기보다 조건·내용·어순·동사 형태의 수정 기록을 남깁니다.",
        "정확도와 풀이 시간을 따로 기록해 내신 복습과 모의고사 시간 배분을 현실적으로 조정합니다.",
        "학교 자료가 확정되기 전과 확정된 뒤의 계획을 나눠 누적 학습이 한꺼번에 밀리지 않게 합니다.",
        "첫 시험 결과 하나로 단정하지 않고 며칠 뒤 해설 없이 다시 설명한 범위를 다음 계획에 반영합니다.",
    ])
    profile["mock_focus"] = choose(local, "mock-focus", [
        "모의고사는 정답 수보다 어휘·구문·문단 관계·근거 선택 중 시간이 시작된 지점을 기록합니다.",
        "전국연합 학력평가 지문은 모두 번역하기보다 문장 뼈대와 문단 역할을 먼저 확인합니다.",
        "첫 모의평가와 학교 내신의 결과가 다르면 자료 유형별 오류를 섞지 않고 따로 분류합니다.",
        "시간 제한 없이 정확히 푼 결과와 제한 시간 안 결과를 비교해 읽기 순서를 조정합니다.",
        "틀린 선택지는 지문 근거가 없었는지, 문장 구조를 잘못 읽었는지 나눠 재학습합니다.",
        "긴 지문은 연결어와 대명사, 중심 문장을 표시해 문단 사이 관계를 한 문장으로 설명합니다.",
        "모의고사 복습일을 내신 과제와 분리해 한날에 영어 학습이 몰리지 않도록 배치합니다.",
        "해설을 본 문항은 유사한 새 지문에서 같은 근거 찾기 순서를 다시 적용해야 완료로 봅니다.",
    ])
    profile["time_focus"] = choose(local, "time-focus", [
        "통학과 학교 과제 시간을 제외한 실제 주중 여유 시간으로 어휘·내신·모의 복습을 나눕니다.",
        "수업 당일 재현, 주중 재확인, 주말 표본 복습 날짜를 각각 적어 몰아 공부를 줄입니다.",
        "시험 범위 발표 전에는 누적 공백을, 발표 후에는 교과서·프린트·서술형 완료를 우선합니다.",
        "계획한 문제 수보다 완료 기준을 통과한 어휘·문장·지문 수로 다음 주 분량을 정합니다.",
        "수행평가 준비일과 지필·모의 복습일을 분리해 읽기와 쓰기 과제가 겹치지 않게 합니다.",
        "정확도가 안정되기 전에는 시간 제한을 늦추고 이후 지문별 소요 시간을 단계적으로 줄입니다.",
        "학교 일정이 바뀌면 새 계획만 쓰지 않고 미완료 항목과 재배치 날짜를 함께 기록합니다.",
        "질문 해결일과 해설 없이 다시 푸는 날을 다르게 두어 설명 의존도를 확인합니다.",
    ])
    return profile


def build_distinctive_study_record(row: dict[str, str], profile: dict[str, str]) -> str:
    return adapt_high1(_middle2_study_record(row, profile))


def build_english_enrichment(row: dict[str, str], profile: dict[str, str]) -> str:
    return adapt_high1(_middle2_enrichment(row, profile))


def high1_transition_section(row: dict[str, str], profile: dict[str, str]) -> str:
    local = row_value(row, "근처 수업가능 동네")
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    evidence = schools[base.seed_for(CATEGORY, local, "high1-school") % len(schools)] if schools else "학생이 가져온 현재 고등학교 자료"
    intro = choose(local, "high1-intro", [
        f"{local} 고1 영어는 고교 내신 적응과 첫 모의고사를 같은 문제집으로 합치기보다 자료별 오류를 나눠 읽어야 합니다.",
        f"{evidence}처럼 공개 자료에 기재된 학교도 실제 교과서와 시험 범위는 학생이 가져온 최신 자료로 다시 확인해야 합니다.",
        f"{local} 학생의 중학교 영어 지식이 고교 문장에 적용되는지는 규칙 설명보다 긴 문장에서 구조와 근거를 찾는 행동으로 확인합니다.",
        f"고1 첫 학기에는 내신 자료 완료와 모의고사 독해 기록을 구분하되 어휘·구문·근거 찾기의 공통 오류는 함께 관리합니다.",
        f"{local} 고1 영어 계획은 학교 과제와 통학 시간을 뺀 실제 학습 시간 안에서 수행평가·서술형과 독해 복습을 배치해야 합니다.",
        f"첫 시험 결과만으로 선행 범위를 정하지 않고 최근 답안에서 어휘 재현, 문장 구조, 독해 근거와 시간 부족을 먼저 구분합니다.",
        f"학교 범위가 확정되기 전에는 누적 어휘와 구문을, 확정 후에는 교과서·프린트·서술형의 완료 날짜를 우선합니다.",
        f"고교 영어 적응은 많은 문제를 한 번 푸는 것보다 수정한 문장을 며칠 뒤 다시 설명하고 작성할 수 있는지 확인하는 과정입니다.",
    ])
    cards = [
        ("내신 적응", "학교 자료는 교과서·프린트·수행평가로 나눠 범위와 완료 날짜를 기록합니다."),
        ("모의고사", profile["mock_focus"]),
        ("어휘·구문", "문맥 속 어휘 의미를 확인한 뒤 주어·동사·수식 관계를 표시해 긴 문장의 뼈대를 설명합니다."),
        ("독해 근거", "정답만 남기지 않고 문단 역할과 선택지 근거가 있는 문장을 표시해 추측 답안을 구분합니다."),
        ("수행·서술형", "내용 누락, 어순, 동사 형태와 문법 조건을 나눠 고친 뒤 해설 없이 다시 작성합니다."),
        ("시간 관리", profile["time_focus"]),
        ("중학교 지식 전이", "배운 문법을 고교 문장과 변형 선택지에서 적용하고 수정 이유를 학생 말로 남깁니다."),
        ("재확인", "수업 직후 정답과 간격을 둔 재현 결과를 함께 기록해 다음 분량을 조정합니다."),
    ]
    ordered = sorted(cards, key=lambda item: base.seed_for(CATEGORY, local, "high1-card", item[0]))
    card_html = "".join(
        f'<article class="article-target-card"><h3>{esc(title)}</h3><p>{esc(body)}</p></article>'
        for title, body in ordered
    )
    return f'''<section class="article-section high1-transition-panel">
      <p class="article-eyebrow">FIRST-YEAR ENGLISH ROADMAP</p>
      <h2>{esc(local)} 고1 영어의 내신·모의고사 이중 학습 설계</h2>
      <p>{esc(intro)} {esc(profile['high1_focus'])}</p>
      <div class="article-target-list">{card_html}</div>
    </section>'''


def build_manuscript(row: dict[str, str], profile: dict[str, str]) -> str:
    manuscript_row = dict(row)
    if re.search(r"수학|(?<!한)국어|영수|국영수", row_value(row, "위치안내") or ""):
        manuscript_row["위치안내"] = ""
    markup = adapt_high1(_middle2_manuscript(manuscript_row, profile))
    section = high1_transition_section(row, profile)
    head, separator, tail = markup.rpartition("</section>")
    combined = f"{head}{section}</section>{tail}" if separator else f"{markup}{section}"
    return middle3.diversify_manuscript_paragraphs(combined, row)


def build_faqs(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    local = row_value(row, "근처 수업가능 동네")
    faqs = list(adapt_high1(_middle2_faqs(row, profile)))
    first_year = (
        f"{local} 고1 영어에서 내신과 모의고사를 어떻게 나눠 준비하나요?",
        f"내신은 학생이 가져온 교과서·프린트·수행평가 범위와 완료 날짜를 중심으로, 모의고사는 어휘·구문·문단 관계·근거 선택과 시간 기록을 중심으로 관리합니다. {profile['mock_focus']} 두 기록은 주간 영어 학습 시간 안에서 겹치지 않게 조정합니다.",
    )
    if len(faqs) < 7:
        faqs.append(first_year)
    else:
        faqs[-1] = first_year
    if len(faqs) != 7:
        raise ValueError(f"{local} 고1 영어 FAQ가 7개가 아닙니다: {len(faqs)}")
    return faqs


def build_parent_notes(row: dict[str, str], profile: dict[str, str]) -> list[str]:
    local = row_value(row, "근처 수업가능 동네")
    notes = list(adapt_high1(_middle2_parent_notes(row, profile)))
    note = f"{local} 상담에서는 첫 내신과 모의고사 결과를 한 점수로 보지 말고 어휘·구문·독해 근거·서술형·시간 중 어디서 차이가 시작됐는지 질문해 볼 수 있습니다."
    return (notes[:2] + [note]) if len(notes) >= 2 else (notes + [note])


def build_checklist(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    checklist = list(adapt_high1(_middle2_checklist(row, profile)))
    checklist.append(("내신·모의 시간 배분", profile["time_focus"]))
    return checklist


def _has_type(node: dict, expected: str) -> bool:
    value = node.get("@type")
    return value == expected or isinstance(value, list) and expected in value


def page_json_ld(
    row: dict[str, str], description: str, page_url: str, rep_image: str,
    body_image: str, map_image: str, faqs: list[tuple[str, str]],
    related: list[tuple[str, str]],
) -> dict:
    local = row_value(row, "근처 수업가능 동네")
    index = int(row.get("__high1_index", "0"))
    exact_description = meta_description(row, index)
    adjusted: list[tuple[str, str]] = []
    for name, url in related:
        if name == f"{local} 중2 수학학원":
            adjusted.append((MIDDLE2_MATH_LABEL_TOKEN, url))
        else:
            adjusted.append((name, url))
    adjusted.append((PREVIOUS_LABEL_TOKEN, canonical(PARENT, "중3영어학원", local)))
    schema = adapt_high1(
        _middle2_json_ld(row, exact_description, page_url, rep_image, body_image, map_image, faqs, adjusted)
    )
    grades = original_grades(row)
    for node in schema.get("@graph", []):
        if not isinstance(node, dict):
            continue
        if _has_type(node, "EducationalOrganization") or _has_type(node, "LocalBusiness"):
            node["educationalLevel"] = grades
            node["knowsAbout"] = ["고1 영어", "고교 첫 내신 적응", "모의고사", "어휘", "구문", "독해", "수행평가", "서술형", "학습 시간 관리"]
        if _has_type(node, "WebPage") or _has_type(node, "Article"):
            node["description"] = exact_description
        if _has_type(node, "Service"):
            node["serviceType"] = "고등학교 1학년 영어 학습관리"
            node["audience"] = {"@type": "EducationalAudience", "educationalRole": "고등학교 1학년 학생 및 학부모"}
            node["about"] = ["고1 영어", "고교 내신", "모의고사", "어휘", "구문", "독해", "수행평가", "서술형", "시간 관리"]
        if _has_type(node, "Article"):
            node["articleSection"] = [row_value(row, "지역"), row_value(row, "시or구"), local, "고1 영어", "고교 내신", "모의고사", "어휘·구문", "독해", "서술형", "시간 관리"]
            node["datePublished"] = PUBLISH_DATE
            node["dateModified"] = PUBLISH_DATE
    return schema


def restore_grade_facts(markup: str, proxy: dict[str, str], original: dict[str, str]) -> str:
    proxy_grades = split_items(row_value(proxy, "가능학년\n(영어)"))
    processed = [adapt_high1(grade) for grade in proxy_grades]
    actual = split_items(row_value(original, "가능학년\n(영어)"))
    markup = markup.replace(", ".join(processed), ", ".join(actual))
    markup = markup.replace(
        "".join(f"<span>{esc(grade)}</span>" for grade in processed),
        "".join(f"<span>{esc(grade)}</span>" for grade in actual),
    )
    markup = markup.replace(
        json.dumps(processed, ensure_ascii=False, separators=(",", ":")),
        json.dumps(actual, ensure_ascii=False, separators=(",", ":")),
    )
    actual_json = json.dumps(actual, ensure_ascii=False, separators=(",", ":"))
    markup = re.sub(
        r'("educationalLevel":)\[[^\]]*\]',
        lambda match: f"{match.group(1)}{actual_json}",
        markup,
        count=1,
    )
    grade_tags = "".join(f"<span>{esc(grade)}</span>" for grade in actual) if actual else "<span>상담 확인 필요</span>"
    markup = re.sub(
        r'(<div class="subject-grade-panel">.*?<div class="subject-school-tags">).*?(</div>)',
        lambda match: f"{match.group(1)}{grade_tags}{match.group(2)}",
        markup,
        count=1,
        flags=re.S,
    )
    return markup


def append_previous_link(markup: str, local: str) -> str:
    anchor = (
        f'<a class="child-page-button" href="../../중3영어학원/{quote(local, safe="")}/index.html">'
        f'{esc(local)} 중3 영어학원</a>'
    )
    pattern = re.compile(
        r'(<section\b[^>]*class="[^"]*local-page-nav[^"]*".*?<div class="child-button-grid">)(.*?)(</div>\s*</section>)',
        re.I | re.S,
    )
    return pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}{anchor}{match.group(3)}", markup, count=1)


def detail_html(
    row: dict[str, str], image_row: dict[str, str], rep_image: str, map_name: str,
    index: int, rows: list[dict[str, str]], peer_locals: list[str],
) -> str:
    local = row_value(row, "근처 수업가능 동네")
    proxy = high1_row(row, index)
    markup = _middle2_detail_html(proxy, image_row, rep_image, map_name, index, rows, peer_locals)
    markup = markup.replace(f"{local} 중2 수학학원", MIDDLE2_MATH_LABEL_TOKEN)
    markup = markup.replace("중2수학학원", MIDDLE2_MATH_PATH_TOKEN)
    markup = adapt_high1(markup)
    markup = markup.replace(MIDDLE2_MATH_LABEL_TOKEN, f"{local} 중2 수학학원")
    markup = markup.replace(MIDDLE2_MATH_PATH_TOKEN, "중2수학학원")
    markup = markup.replace(PREVIOUS_LABEL_TOKEN, f"{local} 중3 영어학원")
    exact_description = meta_description(row, index)
    current_meta = re.search(r'<meta name="description" content="([^"]*)">', markup, re.I)
    if current_meta:
        markup = markup.replace(current_meta.group(1), exact_description)
    markup = restore_grade_facts(markup, proxy, row)
    grades = split_items(row_value(row, "가능학년\n(영어)"))
    if "고1" not in grades:
        center = row_value(row, "센터명") or f"{local} 학습센터"
        transformed_false = f"공개된 {center} 자료에는 영어 가능 학년이 비어 있어 고1 영어 개설 여부를 상담에서 확인해야 합니다."
        replacement = (
            f"공개 영어 가능 학년은 {', '.join(grades)}이지만 고1 포함 여부가 확인되지 않습니다. {local} 고1 영어 개설 여부와 일정은 상담에서 확인해야 합니다."
            if grades else
            f"공개된 {center} 자료에는 영어 가능 학년이 기재되어 있지 않습니다. {local} 고1 영어 개설 여부와 일정은 상담에서 확인해야 합니다."
        )
        markup = markup.replace(transformed_false, replacement)
        markup = re.sub(
            r'(<div class="subject-grade-panel">.*?<div class="subject-school-tags">.*?</div>)',
            lambda match: f'{match.group(1)}<p class="subject-empty-note">고1 영어 개설 여부는 상담 확인 필요</p>',
            markup,
            count=1,
            flags=re.S,
        )
    return append_previous_link(markup, local)


def hub_page(rows: list[dict[str, str]]) -> str:
    markup = adapt_high1(_middle2_hub_page(rows))
    old = "371개 지역의 고1 영어학원 선택 기준과 공개 센터 정보, 교과서·문법·독해·어휘·서술형 상담 항목을 지역별로 정리했습니다."
    new = "371개 지역의 고1 영어학원 선택 기준과 공개 센터 정보, 첫 내신·모의고사·어휘·구문·독해·서술형·시간 관리 상담 항목을 정리했습니다."
    return markup.replace(old, new)


def activate() -> None:
    middle3.CATEGORY = CATEGORY
    middle3.CATEGORY_LABEL = CATEGORY_LABEL
    engine.CATEGORY = CATEGORY
    engine.CATEGORY_LABEL = CATEGORY_LABEL
    engine.PUBLISH_DATE = PUBLISH_DATE
    engine.page_profile = page_profile
    engine.build_distinctive_study_record = build_distinctive_study_record
    engine.build_english_enrichment = build_english_enrichment
    engine.build_manuscript = build_manuscript
    engine.build_faqs = build_faqs
    engine.build_parent_notes = build_parent_notes
    engine.build_checklist = build_checklist
    engine.page_json_ld = page_json_ld
    engine.detail_html = detail_html
    engine.hub_page = hub_page


def main() -> None:
    activate()
    engine.main()


if __name__ == "__main__":
    main()
