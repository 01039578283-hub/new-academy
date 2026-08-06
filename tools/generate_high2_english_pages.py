from __future__ import annotations

"""센터 사실을 유지하면서 고2 영어 371개 지역 페이지를 생성한다.

고1 영어 생성기의 검증된 이미지·센터·학교·교습비·내부링크 골격을 재사용하되,
검색 의도는 고2 내신 심화, 수능형 독해, 모의평가, 서술형과 시간 관리로 분리한다.
기존 전국학원 및 이전 과목별학원 페이지는 읽기만 하며 URL을 변경하지 않는다.
"""

import json
import re
from urllib.parse import quote

import generate_high1_english_pages as high1


engine = high1.engine
middle3 = high1.middle3
base = high1.base
DOMAIN = base.DOMAIN
SITE_NAME = base.SITE_NAME
PARENT = "과목별학원"
CATEGORY = "고2영어학원"
CATEGORY_LABEL = "고2 영어학원"
PUBLISH_DATE = "2026-08-07"
PREVIOUS_TOKEN = "__SAME_TOWN_HIGH1_ENGLISH__"
SAME_GRADE_MATH_LABEL = "__SAME_TOWN_HIGH2_MATH__"
SAME_GRADE_MATH_PATH = "__HIGH2_MATH_PATH__"

esc = base.esc
row_value = base.row_value
split_items = base.split_items
canonical = base.canonical

_adapt_high1 = high1.adapt_high1
_build_manuscript_high1 = high1.build_manuscript


def choose(local: str, label: str, values: list[str]) -> str:
    return values[base.seed_for(CATEGORY, local, label) % len(values)]


def adapt_high2(value):
    if isinstance(value, dict):
        return {key: adapt_high2(item) for key, item in value.items()}
    if isinstance(value, list):
        return [adapt_high2(item) for item in value]
    if isinstance(value, tuple):
        return tuple(adapt_high2(item) for item in value)
    if not isinstance(value, str):
        return value
    value = _adapt_high1(value)
    replacements = (
        ("고등학교 1학년", "고등학교 2학년"),
        ("고교 첫 학년 적응", "고2 학습 심화"),
        ("고교 내신 적응", "고2 내신 심화"),
        ("고교 첫 시험", "고2 학기 시험"),
        ("첫 모의고사", "고2 모의고사"),
        ("첫 모의평가", "고2 모의평가"),
        ("첫 내신", "고2 내신"),
        ("첫 시험", "학기 시험"),
        ("첫 학기", "학기 초"),
        ("중학교 누적 공백", "고1까지의 누적 공백"),
        ("중학교 영어 지식", "고1까지의 영어 지식"),
        ("중학교 지식 전이", "누적 영어 재연결"),
        ("FIRST-YEAR", "SECOND-YEAR"),
        ("고1 영어", "고2 영어"),
        ("고1 학생", "고2 학생"),
        ("고1 과목", "고2 과목"),
        ("고1 가능", "고2 가능"),
        ("고1 포함", "고2 포함"),
        ("고1 개설", "고2 개설"),
        ("고1", "고2"),
        ("1학년 학생", "2학년 학생"),
    )
    for before, after in replacements:
        value = value.replace(before, after)
    return value


def high2_row(row: dict[str, str], index: int | None = None) -> dict[str, str]:
    proxy = dict(row)
    grades = split_items(row_value(row, "가능학년\n(영어)"))
    proxy["가능학년\n(영어)"] = ", ".join(
        "중2" if grade == "고2" else ("중학교 2학년" if grade == "중2" else grade)
        for grade in grades
    )
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
        f"{region} {district} {local} 고2 영어학원 선택을 위해",
        f"{local} 고2 영어의 내신과 모의평가 학습을 점검하며",
        f"공개된 {center} 정보와 학생의 최근 영어 답안을 기준으로",
        f"{region} {local}에서 고등학교 2학년 영어 수업을 살필 때",
        f"{district} {local} 고2 영어 상담 전에",
        f"{local} 학생의 누적 영어 공백과 독해 시간을 함께 확인하도록",
        f"{center}의 공개 자료 범위에서",
        f"{local} 고2 영어학원 비교 기준으로",
    ]
    focuses = [
        "학교 내신, 수능형 독해, 어휘·구문, 서술형과 오답 재학습을 어떤 순서로 확인할지 정리했습니다.",
        "고1까지의 누적 공백과 고2 진도를 구분하고 긴 지문에서 근거와 시간을 기록하는 방법을 안내합니다.",
        "검증된 센터·고등학교·가능 학년 정보와 내신·모의평가 상담 체크리스트를 함께 제공합니다.",
        "문장 구조를 설명하고 문단 관계와 선택지 근거를 찾은 뒤 서술형을 다시 쓰는 학습 흐름을 담았습니다.",
        "학교 자료와 모의평가의 오류를 섞지 않고 실제 주간 시간 안에서 복습 우선순위를 정하는 기준입니다.",
        "학교별 출제나 성적을 단정하지 않고 현재 자료로 확인할 학습 상태와 상담 질문을 제시합니다.",
        "고2 가능 여부, 공개 학교와 교습비를 확인하면서 내신 심화와 시간 관리 기준을 함께 살펴봅니다.",
        "무리한 진도 확대보다 누적 지식을 새 지문에 적용하고 해설 없이 재현하는 과정을 비교합니다.",
    ]
    return f"{openings[page_index % len(openings)]} {focuses[(page_index // len(openings)) % len(focuses)]}"


def page_profile(row: dict[str, str]) -> dict[str, str]:
    local = row_value(row, "근처 수업가능 동네")
    profile = adapt_high2(high1._middle2_profile(row))
    profile["high1_focus"] = choose(local, "high2-focus", [
        "고1까지 배운 문법과 어휘가 고2의 긴 문장과 선택지 판단에 실제로 연결되는지 확인합니다.",
        "학교 자료와 모의평가 답안을 나눠 보고 두 자료에서 함께 흔들리는 구문과 독해 근거를 찾습니다.",
        "본문 암기 여부와 낯선 변형 지문에서 문장 구조를 설명하는 능력을 분리해 살핍니다.",
        "연결어·대명사·중심 문장을 표시해 긴 지문에서 판단이 늦어지는 위치를 좁힙니다.",
        "서술형은 정답 문장을 외우기보다 내용 조건, 어순과 동사 형태의 수정 기록을 남깁니다.",
        "정확도와 지문별 소요 시간을 따로 적어 내신 복습과 모의평가 시간 배분을 조정합니다.",
        "학교 범위가 확정되기 전 누적 복습과 확정된 뒤의 교과 자료 완료 계획을 나눕니다.",
        "시험 결과 하나보다 해설 없이 다시 설명하고 작성할 수 있는 범위를 다음 계획에 반영합니다.",
    ])
    profile["mock_focus"] = choose(local, "high2-mock", [
        "모의평가는 정답 수보다 어휘·구문·문단 관계·근거 선택 중 시간이 늘어난 지점을 기록합니다.",
        "긴 지문을 전부 번역하기보다 문장 뼈대와 문단 역할을 먼저 정리하고 선택지 근거를 찾습니다.",
        "내신과 모의평가 결과가 다르면 자료 유형별 오류를 섞지 않고 별도 복습 항목으로 둡니다.",
        "시간 제한 없이 정확히 읽은 결과와 제한 시간 안 결과를 비교해 풀이 순서를 조정합니다.",
        "오답 선택지는 지문 근거 부족, 구문 오독과 어휘 착각으로 나눠 재학습합니다.",
        "연결어와 대명사, 중심 문장을 표시한 뒤 문단 사이 관계를 한 문장으로 설명합니다.",
        "모의평가 복습일을 학교 영어 과제와 분리해 한날에 학습이 몰리지 않도록 배치합니다.",
        "해설을 본 문항은 새 지문에서 같은 근거 찾기 순서를 적용해야 완료로 기록합니다.",
    ])
    profile["time_focus"] = choose(local, "high2-time", [
        "통학과 학교 과제를 제외한 실제 주중 시간으로 내신·어휘·모의평가 복습을 나눕니다.",
        "수업 당일 재현, 주중 재확인과 주말 표본 복습 날짜를 각각 정해 몰아 공부를 줄입니다.",
        "시험 범위 발표 전에는 누적 공백을, 발표 뒤에는 교과서·프린트·서술형 완료를 우선합니다.",
        "계획한 문제 수보다 완료 기준을 통과한 문장과 지문 수로 다음 주 분량을 정합니다.",
        "수행평가 준비일과 지필·모의 복습일을 분리해 읽기와 쓰기 과제가 겹치지 않게 합니다.",
        "정확도가 안정되기 전에는 시간 제한을 늦추고 이후 지문별 소요 시간을 단계적으로 줄입니다.",
        "학교 일정이 바뀌면 미완료 항목과 재배치 날짜까지 함께 기록합니다.",
        "질문을 해결한 날과 해설 없이 다시 푸는 날을 다르게 두어 설명 의존도를 확인합니다.",
    ])
    return profile


def high2_transition_section(row: dict[str, str], profile: dict[str, str]) -> str:
    local = row_value(row, "근처 수업가능 동네")
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    evidence = schools[base.seed_for(CATEGORY, local, "school") % len(schools)] if schools else "학생이 가져온 현재 고등학교 자료"
    intro = choose(local, "high2-intro", [
        f"{local} 고2 영어는 내신과 모의평가를 같은 방식으로 반복하기보다 자료별 오류와 공통 공백을 나눠 읽어야 합니다.",
        f"{evidence}처럼 공개 자료에 학교명이 있어도 실제 교과서와 시험 범위는 학생이 가져온 최신 자료로 확인합니다.",
        f"{local} 학생의 누적 지식은 문법 규칙 암기보다 긴 문장에서 구조와 근거를 찾는 행동으로 점검합니다.",
        "고2 영어는 학교 자료 완료와 수능형 독해 기록을 구분하되 어휘·구문·근거 찾기의 공통 오류를 연결합니다.",
        f"{local} 고2 계획은 학교 과제와 통학 시간을 뺀 실제 학습 시간 안에서 서술형과 독해 복습을 배치합니다.",
        "최근 점수만으로 진도를 정하지 않고 답안에서 어휘 재현, 문장 구조, 독해 근거와 시간 부족을 먼저 구분합니다.",
        "학교 범위 확정 전에는 누적 어휘와 구문을, 확정 뒤에는 교과서·프린트·서술형 완료 날짜를 우선합니다.",
        "많은 지문을 한 번 푸는 것보다 수정한 근거를 며칠 뒤 다시 설명하고 적용할 수 있는지 확인합니다.",
    ])
    cards = [
        ("내신 심화", "학생이 가져온 교과서·프린트·수행평가의 범위와 완료 날짜를 구분합니다."),
        ("모의평가", profile["mock_focus"]),
        ("어휘·구문", "문맥 속 의미를 확인한 뒤 주어·동사·수식 관계를 표시해 긴 문장의 뼈대를 설명합니다."),
        ("독해 근거", "문단 역할과 선택지 근거 문장을 표시해 추측으로 고른 답안을 구분합니다."),
        ("서술형 재작성", "내용 누락, 어순과 동사 형태를 나눠 고친 뒤 해설 없이 다시 작성합니다."),
        ("시간 관리", profile["time_focus"]),
        ("누적 영어 연결", "고1까지 배운 문법과 어휘를 새로운 지문에 적용하고 수정 이유를 말로 남깁니다."),
        ("간격 재확인", "수업 직후 정답과 며칠 뒤 재현 결과를 함께 기록해 다음 분량을 조정합니다."),
    ]
    cards.sort(key=lambda item: base.seed_for(CATEGORY, local, "card", item[0]))
    card_html = "".join(
        f'<article class="article-target-card"><h3>{esc(title)}</h3><p>{esc(body)}</p></article>'
        for title, body in cards
    )
    return f'''<section class="article-section high1-transition-panel">
      <p class="article-eyebrow">SECOND-YEAR ENGLISH ROADMAP</p>
      <h2>{esc(local)} 고2 영어의 내신·모의평가·수능형 독해 설계</h2>
      <p>{esc(intro)} {esc(profile['high1_focus'])}</p>
      <div class="article-target-list">{card_html}</div>
    </section>'''


def build_manuscript(row: dict[str, str], profile: dict[str, str]) -> str:
    return adapt_high2(_build_manuscript_high1(row, profile))


def build_faqs(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    local = row_value(row, "근처 수업가능 동네")
    faqs = list(adapt_high2(high1._middle2_faqs(row, profile)))
    dedicated = (
        f"{local} 고2 영어에서 내신과 모의평가를 어떻게 나눠 준비하나요?",
        f"내신은 학생이 가져온 교과서·프린트·수행평가의 범위와 완료 기록을 중심으로, 모의평가는 어휘·구문·문단 관계·근거 선택과 시간 기록을 중심으로 관리합니다. {profile['mock_focus']} 두 기록은 실제 주간 영어 시간 안에서 겹치지 않게 조정합니다.",
    )
    if len(faqs) < 7:
        faqs.append(dedicated)
    else:
        faqs[-1] = dedicated
    if len(faqs) != 7:
        raise ValueError(f"{local} 고2 영어 FAQ가 7개가 아닙니다: {len(faqs)}")
    return faqs


def build_parent_notes(row: dict[str, str], profile: dict[str, str]) -> list[str]:
    local = row_value(row, "근처 수업가능 동네")
    notes = list(adapt_high2(high1._middle2_parent_notes(row, profile)))
    note = f"{local} 상담에서는 내신과 모의평가를 한 점수로 합치지 말고 어휘·구문·독해 근거·서술형·시간 중 차이가 시작된 지점을 확인할 수 있습니다."
    return (notes[:2] + [note]) if len(notes) >= 2 else (notes + [note])


def build_checklist(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    checklist = list(adapt_high2(high1._middle2_checklist(row, profile)))
    checklist.append(("내신·모의평가 시간", profile["time_focus"]))
    return checklist


def _has_type(node: dict, expected: str) -> bool:
    value = node.get("@type")
    return value == expected or isinstance(value, list) and expected in value


def _replace_tokens(value):
    if isinstance(value, dict):
        return {key: _replace_tokens(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_tokens(item) for item in value]
    if isinstance(value, str):
        return value.replace(SAME_GRADE_MATH_LABEL, "고2 수학학원").replace(SAME_GRADE_MATH_PATH, "고2수학학원").replace(PREVIOUS_TOKEN, "고1 영어학원")
    return value


def page_json_ld(
    row: dict[str, str], description: str, page_url: str, rep_image: str,
    body_image: str, map_image: str, faqs: list[tuple[str, str]],
    related: list[tuple[str, str]],
) -> dict:
    local = row_value(row, "근처 수업가능 동네")
    index = int(row.get("__high1_index", "0"))
    exact_description = meta_description(row, index)
    adjusted = []
    for name, url in related:
        if name == f"{local} 중2 수학학원":
            adjusted.append((f"{local} {SAME_GRADE_MATH_LABEL}", canonical(PARENT, "고2수학학원", local)))
        else:
            adjusted.append((name, url))
    adjusted.append((f"{local} {PREVIOUS_TOKEN}", canonical(PARENT, "고1영어학원", local)))
    schema = adapt_high2(high1._middle2_json_ld(row, exact_description, page_url, rep_image, body_image, map_image, faqs, adjusted))
    schema = _replace_tokens(schema)
    grades = original_grades(row)
    for node in schema.get("@graph", []):
        if not isinstance(node, dict):
            continue
        if _has_type(node, "EducationalOrganization") or _has_type(node, "LocalBusiness"):
            node["educationalLevel"] = grades
            node["knowsAbout"] = ["고2 영어", "내신 심화", "모의평가", "수능형 독해", "어휘·구문", "서술형", "오답 재학습", "시간 관리"]
        if _has_type(node, "WebPage") or _has_type(node, "Article"):
            node["description"] = exact_description
        if _has_type(node, "Service"):
            node["serviceType"] = "고등학교 2학년 영어 학습관리"
            node["audience"] = {"@type": "EducationalAudience", "educationalRole": "고등학교 2학년 학생 및 학부모"}
            node["about"] = ["고2 영어", "고교 내신", "모의평가", "수능형 독해", "어휘·구문", "서술형", "시간 관리"]
        if _has_type(node, "Article"):
            node["articleSection"] = [row_value(row, "지역"), row_value(row, "시or구"), local, "고2 영어", "내신 심화", "모의평가", "수능형 독해", "서술형", "시간 관리"]
            node["datePublished"] = PUBLISH_DATE
            node["dateModified"] = PUBLISH_DATE
    return schema


def append_previous_link(markup: str, local: str) -> str:
    anchor = (
        f'<a class="child-page-button" href="../../고1영어학원/{quote(local, safe="")}/index.html">'
        f'{esc(local)} 고1 영어학원</a>'
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
    proxy = high2_row(row, index)
    markup = high1._middle2_detail_html(proxy, image_row, rep_image, map_name, index, rows, peer_locals)
    markup = markup.replace(f"{local} 중2 수학학원", f"{local} {SAME_GRADE_MATH_LABEL}")
    markup = markup.replace("중2수학학원", SAME_GRADE_MATH_PATH)
    markup = adapt_high2(markup)
    markup = markup.replace(SAME_GRADE_MATH_LABEL, "고2 수학학원").replace(SAME_GRADE_MATH_PATH, "고2수학학원")
    exact_description = meta_description(row, index)
    current_meta = re.search(r'<meta name="description" content="([^"]*)">', markup, re.I)
    if current_meta:
        markup = markup.replace(current_meta.group(1), exact_description)
    markup = high1.restore_grade_facts(markup, proxy, row)
    grades = split_items(row_value(row, "가능학년\n(영어)"))
    if "고2" not in grades:
        markup = re.sub(
            r'(<div class="subject-grade-panel">.*?<div class="subject-school-tags">.*?</div>)',
            lambda match: f'{match.group(1)}<p class="subject-empty-note">고2 영어 개설 여부는 상담 확인 필요</p>',
            markup, count=1, flags=re.S,
        )
    return append_previous_link(markup, local)


def hub_page(rows: list[dict[str, str]]) -> str:
    proxies = [high2_row(row, index) for index, row in enumerate(rows)]
    markup = adapt_high2(high1._middle2_hub_page(proxies))
    old = "371개 지역의 고2 영어학원 선택 기준과 공개 센터 정보, 교과서·문법·독해·어휘·서술형 상담 항목을 지역별로 정리했습니다."
    new = "371개 지역의 고2 영어학원 선택 기준과 공개 센터 정보, 내신 심화·모의평가·수능형 독해·어휘·구문·서술형·시간 관리 상담 항목을 정리했습니다."
    return markup.replace(old, new)


def activate() -> None:
    high1.CATEGORY = CATEGORY
    high1.CATEGORY_LABEL = CATEGORY_LABEL
    high1.PUBLISH_DATE = PUBLISH_DATE
    high1.adapt_high1 = adapt_high2
    high1.high1_row = high2_row
    high1.original_grades = original_grades
    high1.meta_description = meta_description
    high1.page_profile = page_profile
    high1.high1_transition_section = high2_transition_section
    high1.build_manuscript = build_manuscript
    high1.build_faqs = build_faqs
    high1.build_parent_notes = build_parent_notes
    high1.build_checklist = build_checklist
    high1.page_json_ld = page_json_ld
    high1.detail_html = detail_html
    high1.hub_page = hub_page
    middle3.CATEGORY = CATEGORY
    middle3.CATEGORY_LABEL = CATEGORY_LABEL
    engine.CATEGORY = CATEGORY
    engine.CATEGORY_LABEL = CATEGORY_LABEL
    engine.PUBLISH_DATE = PUBLISH_DATE
    engine.page_profile = page_profile
    engine.build_distinctive_study_record = lambda row, profile: adapt_high2(high1._middle2_study_record(row, profile))
    engine.build_english_enrichment = lambda row, profile: adapt_high2(high1._middle2_enrichment(row, profile))
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
