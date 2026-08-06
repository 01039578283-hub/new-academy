from __future__ import annotations

"""중2 영어 생성기의 검증 구조를 재사용하는 중3 영어 전용 생성기.

실행 시 ``과목별학원/중3영어학원``만 생성합니다. 전국학원 페이지는
참고용으로 읽을 뿐 쓰지 않습니다.
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import quote


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import generate_middle2_english_pages as source


base = source.base
SITE = source.SITE
DOMAIN = source.DOMAIN
SITE_NAME = source.SITE_NAME
PARENT = "과목별학원"
CATEGORY = "중3영어학원"
CATEGORY_LABEL = "중3 영어학원"
PUBLISH_DATE = "2026-08-07"
MIDDLE2_LABEL_TOKEN = "__SAME_TOWN_MIDDLE2_ENGLISH__"

esc = base.esc
row_value = base.row_value
split_items = base.split_items
canonical = base.canonical


_source_page_profile = source.page_profile
_source_study_record = source.build_distinctive_study_record
_source_enrichment = source.build_english_enrichment
_source_manuscript = source.build_manuscript
_source_faqs = source.build_faqs
_source_parent_notes = source.build_parent_notes
_source_checklist = source.build_checklist
_source_json_ld = source.page_json_ld
_source_detail_html = source.detail_html
_source_hub_page = source.hub_page


def choose(local: str, label: str, values: list[str]) -> str:
    return values[base.seed_for(CATEGORY, local, label) % len(values)]


def source_safe_row(row: dict[str, str]) -> dict[str, str]:
    """영어 원고에 다른 과목 상호가 섞인 위치 설명은 추정·변형하지 않고 생략합니다."""
    safe = dict(row)
    for key, value in safe.items():
        if "위치안내" in key and re.search(r"수학|국어|영수|국영수", value or ""):
            safe[key] = ""
    return safe


def meta_description(row: dict[str, str], page_index: int) -> str:
    local = row_value(row, "근처 수업가능 동네")
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    openings = [
        f"{region} {district} {local} 중3 영어학원 비교를 위해",
        f"{local} 중3 영어 학습 방향을 정하기 전에",
        f"{center} 공개 정보와 학생 답안을 바탕으로",
        f"{region} {local}에서 중3 영어 수업을 살필 때",
        f"{district} {local} 중3 영어 상담을 준비하며",
        f"{local} 학생의 중3 내신과 고교 전환 준비를 위해",
        f"공개된 {center} 자료 범위에서",
        f"{local} 중3 영어학원 선택 기준으로",
    ]
    focuses = [
        "학교 자료, 누적 어휘와 문법 적용, 독해 근거, 서술형 재작성의 확인 순서를 정리했습니다.",
        "현재 내신 범위와 중1·2 누적 공백을 구분하고 고교 진입 전 점검 항목을 안내합니다.",
        "교과서·프린트 학습과 어휘·문장 구조·독해 기록을 상담 전에 확인할 수 있게 구성했습니다.",
        "학생의 실제 오류와 주간 복습 시간을 기준으로 내신 마무리와 누적 학습을 나누어 설명합니다.",
        "문법 규칙 암기보다 새 문장 적용, 지문 근거와 서술형 수정 기록을 비교 기준으로 제시합니다.",
        "시험 범위 확정 전후의 학습 순서와 해설 없는 재현 여부를 확인하는 방법을 담았습니다.",
        "검증된 센터·학교·가능 학년 정보와 영어 학습 상담 체크리스트를 함께 정리했습니다.",
        "선행 범위를 단정하지 않고 현재 답안에서 고교 영어로 연결할 준비 상태를 살피는 기준을 안내합니다.",
    ]
    return f"{openings[page_index % len(openings)]} {focuses[(page_index // len(openings)) % len(focuses)]}"


def diversify_manuscript_paragraphs(markup: str, row: dict[str, str]) -> str:
    """공통 판단 문단도 페이지마다 다른 검증 행동과 결합해 템플릿 반복을 줄입니다."""
    local = row_value(row, "근처 수업가능 동네")
    evidences = [
        "학생이 표시한 주어와 동사를", "지문에서 찾은 답의 근거 위치를", "교과서와 학교 프린트의 완료 기록을",
        "처음 쓴 서술형과 수정 답안을", "어휘를 처음 외운 결과와 며칠 뒤 재현 결과를", "문법 설명 뒤 새 문장에 적용한 결과를",
        "시간 제한 전후의 독해 결과를", "질문한 문장과 유사 문장의 독립 해결 결과를", "시험 범위 발표 전후의 남은 분량을",
        "누적 오답과 현재 교재의 연결 지점을", "설명 직후와 다음 확인일의 답안을", "학생이 실제로 확보한 주중 복습 시간을",
        "본문 암기 결과와 문장 구조 설명 결과를", "틀린 선택지와 이를 제외한 근거를", "어순·동사 형태·내용 누락의 수정 흔적을",
        "학교 진도와 별도로 남긴 누적 복습표를",
    ]
    actions = [
        "같은 기준으로 대조해 다음 분량을 조정합니다", "별도 칸에 기록해 완료 여부를 판단합니다",
        "학생 설명과 함께 놓고 재학습 순서를 정합니다", "다음 확인 날짜와 연결해 일시적인 암기와 구분합니다",
        "학교 범위와 누적 복습으로 나눠 주간표에 반영합니다", "해설을 가린 재확인 결과와 비교해 다음 단계를 정합니다",
        "상담 질문으로 남겨 실제 피드백 방식과 대조합니다", "오류가 시작된 지점별로 나눠 보완 범위를 좁힙니다",
        "정확도와 소요 시간을 분리해 무리 없는 순서를 계산합니다", "새 문장에서도 같은 기준이 재현되는지 다시 확인합니다",
        "완료 날짜와 재확인 날짜를 함께 적어 다음 계획에 반영합니다", "학생이 혼자 처리한 범위만 따로 표시해 의존도를 확인합니다",
        "시험 전후 일정에 배치해 과제가 한날에 몰리지 않게 합니다", "현재 답안의 근거와 비교해 선행보다 먼저 볼 항목을 정합니다",
        "수정 이유를 학생 말로 남겨 비슷한 오류의 재발 여부를 봅니다", "실제 운영 일정과 함께 놓고 실행 가능한지 상담에서 확인합니다",
    ]
    paragraph_index = 0

    def add_context(match: re.Match[str]) -> str:
        nonlocal paragraph_index
        attrs, body = match.group(1) or "", match.group(2)
        visible = re.sub(r"<[^>]+>", " ", body)
        visible = re.sub(r"\s+", " ", visible).strip()
        current = paragraph_index
        paragraph_index += 1
        if len(visible) < 35:
            return match.group(0)
        code = base.seed_for(CATEGORY, local, "paragraph-context", str(current), visible[:120])
        evidence = evidences[code % len(evidences)]
        action = actions[(code // len(evidences)) % len(actions)]
        return f"<p{attrs}>{body.rstrip()} {esc(evidence)} {esc(action)}.</p>"

    return re.sub(r"<p(\s[^>]*)?>(.*?)</p>", add_context, markup, flags=re.I | re.S)


def restore_grade_facts(markup: str, row: dict[str, str]) -> str:
    """중3 문구 변환 중 실제 영어 가능 학년의 중2 값이 바뀌지 않도록 원자료를 복원합니다."""
    grades = split_items(row_value(row, "가능학년\n(영어)"))
    if not grades:
        return markup
    adapted = [adapt_middle3(grade) for grade in grades]
    markup = markup.replace(", ".join(adapted), ", ".join(grades))
    adapted_spans = "".join(f"<span>{esc(grade)}</span>" for grade in adapted)
    original_spans = "".join(f"<span>{esc(grade)}</span>" for grade in grades)
    markup = markup.replace(adapted_spans, original_spans)
    adapted_json = json.dumps(adapted, ensure_ascii=False, separators=(",", ":"))
    original_json = json.dumps(grades, ensure_ascii=False, separators=(",", ":"))
    return markup.replace(adapted_json, original_json)


def adapt_middle3(value):
    """중2 구조 문구를 중3 의도로 바꾸되 URL·사실 데이터는 보존합니다."""
    if isinstance(value, dict):
        return {key: adapt_middle3(item) for key, item in value.items()}
    if isinstance(value, list):
        return [adapt_middle3(item) for item in value]
    if isinstance(value, tuple):
        return tuple(adapt_middle3(item) for item in value)
    if not isinstance(value, str):
        return value
    replacements = (
        ("중학교 2학년", "중학교 3학년"),
        ("중2 영어", "중3 영어"),
        ("중2 학생", "중3 학생"),
        ("중2가", "중3이"),
        ("중2를", "중3을"),
        ("중2", "중3"),
        (
            "교과서·문법·독해·어휘·서술형 학습 및 상담 기준",
            "현재 학교 내신·누적 어휘·문법·독해·서술형·고교 진입 전 연결 기준",
        ),
        (
            "교과서·문법·독해·어휘·서술형 상담 항목",
            "현재 학교 내신·누적 어휘·문법·독해·서술형·고교 진입 전 상담 항목",
        ),
    )
    for before, after in replacements:
        value = value.replace(before, after)
    return value


def page_profile(row: dict[str, str]) -> dict[str, str]:
    local = row_value(row, "근처 수업가능 동네")
    profile = adapt_middle3(_source_page_profile(row))
    bridge_bank = [
        "누적 어휘가 긴 지문에서 바로 떠오르는지와 문맥 속 품사·의미를 함께 확인합니다.",
        "중학교 문법을 규칙 암기에 두지 않고 교과서 문장 해석과 서술형 수정에 적용합니다.",
        "지문에서 답의 근거를 표시하고 문단 관계를 설명하는 독해 습관을 고교 과정 전에 점검합니다.",
        "서술형은 철자만 고치지 않고 어순·동사 형태·내용 누락의 원인을 나누어 다시 씁니다.",
        "학교 내신 복습과 고교 진입 전 누적 학습을 별도 일정으로 나누어 무리한 선행을 피합니다.",
        "시험 범위가 정해지기 전에는 누적 어휘와 문장 구조를, 확정 뒤에는 학교 자료를 우선합니다.",
        "설명을 들은 문장을 며칠 뒤 해설 없이 다시 해석하고 바꾸어 쓸 수 있는지 확인합니다.",
        "현재 학교 답안에서 어휘·문법·독해·서술형의 연결이 끊기는 지점을 먼저 찾습니다.",
        "읽는 속도보다 문장 구조와 지문 근거가 안정된 뒤 시간 제한을 적용합니다.",
        "고교 영어 준비 범위는 중학교 교과서 문장과 누적 어휘를 독립적으로 재현한 뒤 판단합니다.",
    ]
    profile["highschool_bridge"] = choose(local, "highschool-bridge", bridge_bank)
    return profile


def build_distinctive_study_record(row: dict[str, str], profile: dict[str, str]) -> str:
    return adapt_middle3(_source_study_record(row, profile))


def build_english_enrichment(row: dict[str, str], profile: dict[str, str]) -> str:
    return adapt_middle3(_source_enrichment(row, profile))


def middle3_transition_section(row: dict[str, str], profile: dict[str, str]) -> str:
    local = row_value(row, "근처 수업가능 동네")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    evidence = schools[base.seed_for(CATEGORY, local, "transition-school") % len(schools)] if schools else "현재 학교의 시험지와 교재"
    openings = [
        f"{local} 중3 영어는 현재 학교 내신과 고교 진입 전 누적 학습을 한꺼번에 늘리기보다 서로 다른 기록으로 관리해야 합니다.",
        f"{evidence}에서 확인되는 오류를 어휘·문법·독해·서술형으로 나누면 {local} 학생의 고교 전환 준비 순서가 구체적으로 보입니다.",
        f"{center} 상담에서는 선행 교재의 난이도보다 학생이 중학교 영어 문장을 혼자 읽고 고치는 범위를 먼저 확인하는 편이 안전합니다.",
        f"중3 영어는 학교 시험 범위와 누적 공백을 함께 다루되, 실제 주간 시간 안에서 완료할 순서를 정하는 것이 중요합니다.",
        f"{local} 학생의 최근 답안과 재풀이 기록을 비교하면 내신 준비와 고교 연결 학습의 비중을 사실에 근거해 조정할 수 있습니다.",
        f"교과서 본문 암기만 확인하지 않고 문장 구조, 지문 근거와 서술형 수정 이유가 남는지 살펴야 합니다.",
    ]
    card_banks = [
        ("누적 어휘", "단어 뜻만 외우지 않고 품사·문맥 의미·파생 형태를 문장 안에서 다시 확인합니다."),
        ("문법 적용", "배운 규칙을 교과서 문장 해석, 선택지 판단과 서술형 수정에 실제로 사용합니다."),
        ("독해 근거", "문단 관계와 답의 근거 문장을 표시하고 선택지를 고른 이유를 학생이 설명합니다."),
        ("서술형 수정", "내용 누락·어순·동사 형태·철자를 나누고 며칠 뒤 같은 의미를 다시 씁니다."),
        ("내신 일정", "시험 범위 확정 전 누적 복습과 확정 후 학교 자료 중심 계획을 구분합니다."),
        ("고교 연결", "중학교 문장을 독립적으로 해석하고 바꾸어 쓸 수 있는지 확인한 뒤 다음 범위를 정합니다."),
        ("시간 관리", "정확한 해석과 근거 찾기가 안정된 뒤 지문 시간과 검토 시간을 따로 기록합니다."),
        ("오답 재현", "정답을 가리고 다시 고친 결과가 다음 과제와 재확인 날짜에 반영되는지 봅니다."),
    ]
    ordered = sorted(card_banks, key=lambda item: base.seed_for(CATEGORY, local, "transition-card", item[0]))[:4]
    card_notes = [
        "최근 답안과 다음 확인일 기록을 함께 봅니다.", "학생이 혼자 설명한 범위를 완료 기준으로 둡니다.",
        "학교 범위와 누적 복습의 날짜를 구분합니다.", "해설을 가린 재현 결과로 다음 단계를 정합니다.",
        "오류가 시작된 문장에 표시를 남깁니다.", "정확도와 소요 시간을 별도 칸에 기록합니다.",
        "새 문장에서 같은 기준이 적용되는지 확인합니다.", "실제 주중 시간 안에서 가능한 분량으로 조정합니다.",
        "수정 이유를 학생 말로 남겨 재발 여부를 봅니다.", "시험 범위 확정 전후의 우선순위를 나눕니다.",
        "질문한 문장과 유사 문장의 해결 결과를 대조합니다.", "상담에서는 기록이 다음 과제에 반영되는지 확인합니다.",
        "어휘·구조·근거·쓰기 중 막힌 지점을 한 가지로 좁힙니다.", "완료 날짜와 다시 확인할 날짜를 함께 정합니다.",
        "현재 교재와 학교 자료에서 확인되는 범위만 사용합니다.", "고교 선행보다 중학교 문장의 독립 재현을 먼저 봅니다.",
    ]
    cards = "".join(
        f'<article class="article-target-card"><h3>{esc(title)}</h3><p>{esc(body)} {esc(choose(local, "transition-note-" + title, card_notes))}</p></article>'
        for title, body in ordered
    )
    opening = choose(local, "transition-opening", openings)
    return f'''<section class="article-section middle3-transition-panel">
      <p class="article-eyebrow">HIGH SCHOOL BRIDGE</p>
      <h2>{esc(local)} 중3 영어의 내신과 고교 진입 전 연결</h2>
      <p>{esc(opening)} {esc(profile['highschool_bridge'])}</p>
      <div class="article-target-list">{cards}</div>
    </section>'''


def build_manuscript(row: dict[str, str], profile: dict[str, str]) -> str:
    markup = adapt_middle3(_source_manuscript(row, profile))
    section = middle3_transition_section(row, profile)
    head, separator, tail = markup.rpartition("</section>")
    combined = f"{head}{section}</section>{tail}" if separator else f"{markup}{section}"
    return diversify_manuscript_paragraphs(combined, row)


def build_faqs(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    local = row_value(row, "근처 수업가능 동네")
    faqs = list(adapt_middle3(_source_faqs(row, profile)))
    bridge = (
        f"{local} 중3 영어에서 고교 진입 전에 무엇을 먼저 확인하나요?",
        f"선행 범위를 임의로 정하지 않고 현재 학교 답안에서 누적 어휘·문법 적용·독해 근거·서술형 수정이 독립적으로 이어지는지 확인합니다. {profile['highschool_bridge']} 실제 범위는 학생 자료와 주간 학습 가능 시간을 기준으로 조정합니다.",
    )
    if len(faqs) < 7:
        faqs.append(bridge)
    else:
        faqs[-1] = bridge
    if len(faqs) != 7:
        raise ValueError(f"{local} 중3 영어 FAQ가 7개가 아닙니다: {len(faqs)}")
    return faqs


def build_parent_notes(row: dict[str, str], profile: dict[str, str]) -> list[str]:
    local = row_value(row, "근처 수업가능 동네")
    notes = list(adapt_middle3(_source_parent_notes(row, profile)))
    bridge_note = f"{local} 상담에서는 선행 진도보다 누적 어휘·문장 구조·독해 근거와 서술형 수정 기록이 고교 준비 계획에 어떻게 반영되는지 질문해 볼 수 있습니다."
    return (notes[:2] + [bridge_note]) if len(notes) >= 2 else (notes + [bridge_note])


def build_checklist(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    checklist = list(adapt_middle3(_source_checklist(row, profile)))
    checklist.append(("고교 연결 기준", profile["highschool_bridge"]))
    return checklist


def _node_has_type(node: dict, expected: str) -> bool:
    value = node.get("@type")
    return value == expected or isinstance(value, list) and expected in value


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
    adjusted_related: list[tuple[str, str]] = []
    for name, url in related:
        if name == f"{local} 중2 수학학원":
            adjusted_related.append((f"{local} 중3 수학학원", canonical(PARENT, "중3수학학원", local)))
        else:
            adjusted_related.append((adapt_middle3(name), url))
    adjusted_related.append((MIDDLE2_LABEL_TOKEN, canonical(PARENT, "중2영어학원", local)))
    schema = adapt_middle3(
        _source_json_ld(
            row,
            adapt_middle3(description),
            page_url,
            rep_image,
            body_image,
            map_image,
            adapt_middle3(faqs),
            adjusted_related,
        )
    )
    graph = schema.get("@graph", [])
    for node in graph:
        if not isinstance(node, dict):
            continue
        if _node_has_type(node, "EducationalOrganization") or _node_has_type(node, "LocalBusiness"):
            topics = node.setdefault("knowsAbout", [])
            for topic in ("중3 영어", "현재 학교 내신", "누적 어휘", "문법 적용", "독해 근거", "서술형", "고교 진입 전 영어"):
                if topic not in topics:
                    topics.append(topic)
        if _node_has_type(node, "Service"):
            node["about"] = ["중3 영어", "학교 내신", "누적 어휘", "문법", "독해", "서술형", "고교 진입 전 연결"]
        if _node_has_type(node, "Article"):
            sections = node.setdefault("articleSection", [])
            for topic in ("현재 학교 내신", "누적 어휘", "고교 진입 전 연결"):
                if topic not in sections:
                    sections.append(topic)
    return schema


def _append_middle2_link(markup: str, local: str) -> str:
    anchor = (
        f'<a class="child-page-button" href="../../중2영어학원/{quote(local, safe="")}/index.html">'
        f'{esc(local)} 중2 영어학원</a>'
    )
    pattern = re.compile(
        r'(<section\b[^>]*class="[^"]*local-page-nav[^"]*".*?<div class="child-button-grid">)(.*?)(</div>\s*</section>)',
        re.I | re.S,
    )
    return pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}{anchor}{match.group(3)}", markup, count=1)


def detail_html(
    row: dict[str, str],
    image_row: dict[str, str],
    rep_image: str,
    map_name: str,
    index: int,
    rows: list[dict[str, str]],
    peer_locals: list[str],
) -> str:
    local = row_value(row, "근처 수업가능 동네")
    safe_row = source_safe_row(row)
    markup = adapt_middle3(_source_detail_html(safe_row, image_row, rep_image, map_name, index, rows, peer_locals))
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    previous_description = (
        f"{region} {district} {local} 중3 영어학원 선택을 위해 {center} 공개 정보와 "
        "현재 학교 내신·누적 어휘·문법·독해·서술형·고교 진입 전 연결 기준을 정리했습니다."
    )
    markup = markup.replace(previous_description, meta_description(row, index))
    markup = restore_grade_facts(markup, row)
    markup = _append_middle2_link(markup, local)
    return markup.replace(MIDDLE2_LABEL_TOKEN, f"{local} 중2 영어학원")


def hub_page(rows: list[dict[str, str]]) -> str:
    return adapt_middle3(_source_hub_page(rows))


def activate_middle3_generator() -> None:
    """중2 생성 모듈의 파일·링크 검증 흐름을 중3 전용 함수로 교체합니다."""
    source.CATEGORY = CATEGORY
    source.CATEGORY_LABEL = CATEGORY_LABEL
    source.PUBLISH_DATE = PUBLISH_DATE
    source.page_profile = page_profile
    source.build_distinctive_study_record = build_distinctive_study_record
    source.build_english_enrichment = build_english_enrichment
    source.build_manuscript = build_manuscript
    source.build_faqs = build_faqs
    source.build_parent_notes = build_parent_notes
    source.build_checklist = build_checklist
    source.page_json_ld = page_json_ld
    source.detail_html = detail_html
    source.hub_page = hub_page


def main() -> None:
    activate_middle3_generator()
    source.main()


if __name__ == "__main__":
    main()
