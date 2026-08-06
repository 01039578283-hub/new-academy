from __future__ import annotations

"""검증된 센터 사실을 바탕으로 고2 수학 371개 지역 페이지를 생성한다.

고1 수학의 기술 골격은 유지하되 본문 의도는 고2 내신 심화, 누적 개념 연결,
모의평가, 과정형 풀이, 서술형과 제한 시간 관리로 분리한다.
"""

import json
import re
from urllib.parse import quote

import generate_high1_math_pages as high1


middle3 = high1.middle3
base = high1.base
PARENT = "과목별학원"
CATEGORY = "고2수학학원"
CATEGORY_LABEL = "고2 수학학원"
PUBLISH_DATE = "2026-08-07"
PREVIOUS_TOKEN = "__SAME_TOWN_HIGH1_MATH__"

esc = base.esc
row_value = base.row_value
split_items = base.split_items
canonical = middle3.canonical

_adapt_high1 = high1.adapt_high1
_seed_high1 = high1.seed_manuscript
_build_article_high1 = high1.build_learning_article


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
        ("고교 첫 내신", "고2 내신"),
        ("첫 내신", "고2 내신"),
        ("첫 모의평가", "고2 모의평가"),
        ("첫 시험", "학기 시험"),
        ("첫 학기", "학기 초"),
        ("공통수학 시작점", "고2 수학의 현재 시작점"),
        ("공통수학 개념", "누적 수학 개념"),
        ("공통수학", "누적 개념"),
        ("중학교 누적 공백", "고1까지의 누적 공백"),
        ("중학교 개념 연결", "고1 개념 재연결"),
        ("중학교 지식", "고1까지의 지식"),
        ("FIRST-YEAR", "SECOND-YEAR"),
        ("고1 수학", "고2 수학"),
        ("고1 학생", "고2 학생"),
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
    grades = split_items(row_value(row, "가능학년\n(수학)"))
    proxy["가능학년\n(수학)"] = ", ".join(
        "중3" if grade == "고2" else ("중학교 3학년" if grade == "중3" else grade)
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
    return split_items(row_value(row, "가능학년\n(수학)"))


def meta_description(row: dict[str, str], page_index: int) -> str:
    local = row_value(row, "근처 수업가능 동네")
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    openings = [
        f"{region} {district} {local} 고2 수학학원 선택을 위해",
        f"{local} 고2 수학의 내신과 모의평가 학습을 점검하며",
        f"공개된 {center} 정보와 학생의 최근 풀이를 기준으로",
        f"{region} {local}에서 고등학교 2학년 수학 수업을 살필 때",
        f"{district} {local} 고2 수학 상담 전에",
        f"{local} 학생의 누적 개념과 풀이 시간을 함께 확인하도록",
        f"{center}의 공개 자료 범위에서",
        f"{local} 고2 수학학원 비교 기준으로",
    ]
    focuses = [
        "내신 범위, 누적 개념, 과정형 풀이, 서술형, 오답 재학습과 모의평가 확인 순서를 정리했습니다.",
        "고1까지의 공백과 현재 진도를 구분하고 낯선 조건에서 개념 선택과 시간 배분을 점검합니다.",
        "검증된 센터·고등학교·가능 학년 정보와 내신·모의평가 상담 체크리스트를 함께 제공합니다.",
        "조건 해석에서 개념 선택, 식 전개, 검산과 간격 재풀이로 이어지는 학습 흐름을 설명합니다.",
        "학교 자료와 모의평가의 오류를 섞지 않고 실제 주간 시간 안에서 우선순위를 정하는 기준입니다.",
        "학교별 출제나 성적을 단정하지 않고 현재 답안으로 확인할 학습 상태와 상담 질문을 제시합니다.",
        "고2 가능 여부, 공개 학교와 교습비를 확인하면서 내신 심화와 학습 시간 관리 기준을 살펴봅니다.",
        "무리한 진도 확대보다 누적 개념을 새 문항에 적용하고 풀이 근거를 재현하는 과정을 비교합니다.",
    ]
    return f"{openings[page_index % len(openings)]} {focuses[(page_index // len(openings)) % len(focuses)]}"


def seed_manuscript(row: dict[str, str], page_index: int) -> str:
    return adapt_high2(_seed_high1(row, page_index))


def load_manuscripts() -> list[str]:
    rows = base.read_csv(base.CENTER_CSV)
    return [seed_manuscript(row, index) for index, row in enumerate(rows)]


def page_profile(row: dict[str, str]) -> dict[str, str]:
    local = row_value(row, "근처 수업가능 동네")
    profile = adapt_high2(high1._middle3_profile(row))
    profile["common_focus"] = choose(local, "high2-concept", [
        "이전 단원에서 배운 정의와 성질을 현재 조건에 맞게 선택하고 첫 식의 근거를 설명합니다.",
        "문항의 조건을 기호·식·그래프 중 적절한 표현으로 바꾸고 빠진 조건이 없는지 확인합니다.",
        "공식을 먼저 대입하기보다 어떤 개념을 선택했는지와 다른 접근이 어려운 이유를 남깁니다.",
        "여러 단원이 연결된 문항은 조건별 역할을 분리한 뒤 필요한 개념을 순서대로 배치합니다.",
        "계산 실수와 개념 선택 오류를 분리해 같은 유형이 아닌 새 조건에서도 다시 적용합니다.",
        "풀이가 길어질 때 중간 결과가 다음 식에서 어떤 정보로 쓰이는지 문장으로 설명합니다.",
        "낯선 표현을 익숙한 정의와 성질로 바꾼 뒤 조건과 결론 사이의 연결을 검토합니다.",
        "고1까지의 누적 개념 중 현재 단원에서 실제로 쓰인 부분만 골라 짧게 복습합니다.",
    ])
    profile["mock_focus"] = choose(local, "high2-mock", [
        "모의평가는 정답 수보다 조건 해석·개념 선택·식 전개·검산 중 시간이 늘어난 지점을 기록합니다.",
        "낯선 문항에서 첫 식을 세우기까지의 시간과 계산 이후의 시간을 나눠 풀이 순서를 조정합니다.",
        "내신과 모의평가 결과가 다르면 자료 유형별 오류를 섞지 않고 별도 복습 항목으로 둡니다.",
        "시간 제한 없이 정확히 푼 결과와 제한 시간 안 결과를 비교해 문항별 우선순위를 정합니다.",
        "틀린 문항은 개념 부족, 조건 누락, 계산과 검산 오류로 나눠 재학습합니다.",
        "해설의 식을 외우지 않고 조건이 달라진 새 문항에서 같은 판단 순서를 다시 적용합니다.",
        "모의평가 복습일을 학교 수학 과제와 분리해 한날에 풀이가 몰리지 않도록 배치합니다.",
        "어려운 문항만 반복하기보다 안정적으로 해결해야 할 문항의 정확도와 시간을 먼저 관리합니다.",
    ])
    profile["time_focus"] = choose(local, "high2-time", [
        "통학과 학교 과제를 제외한 실제 주중 시간으로 내신·누적 복습·모의평가를 나눕니다.",
        "수업 당일 재풀이, 주중 재확인과 주말 표본 복습 날짜를 각각 정해 몰아 공부를 줄입니다.",
        "시험 범위 발표 전에는 누적 공백을, 발표 뒤에는 학교 자료와 서술형 완료를 우선합니다.",
        "계획한 문제 수보다 풀이 근거를 설명하고 재현한 문항 수로 다음 주 분량을 정합니다.",
        "수행평가 준비일과 지필·모의 복습일을 분리해 과제가 겹치지 않게 합니다.",
        "정확도가 안정되기 전에는 시간 제한을 늦추고 이후 문항별 소요 시간을 단계적으로 줄입니다.",
        "학교 일정이 바뀌면 미완료 항목과 재배치 날짜까지 함께 기록합니다.",
        "질문을 해결한 날과 해설 없이 다시 푸는 날을 다르게 두어 풀이 의존도를 확인합니다.",
    ])
    profile["writing_focus"] = choose(local, "high2-writing", [
        "서술형은 조건·사용 개념·식 전개·결론이 답안 안에서 끊기지 않는지 확인합니다.",
        "정답이 맞아도 생략한 근거를 찾아 채우고 불필요한 계산은 줄여 풀이 흐름을 분명히 합니다.",
        "과정형 문항은 첫 식이 문제 조건에서 어떻게 나온 것인지 한 문장으로 설명합니다.",
        "검산 뒤에는 사용한 정의와 성질이 답안에 드러나는지 다시 확인합니다.",
        "같은 답에 이르는 다른 풀이를 비교해 시험에서 안정적으로 재현할 순서를 선택합니다.",
        "답안 작성 뒤 조건 누락, 기호 정의, 식의 연결과 결론 표현을 일정한 순서로 검토합니다.",
        "해설 문장을 옮기지 않고 학생이 실제로 사용한 개념과 근거만 다시 작성합니다.",
        "조건이 달라진 문항에서도 같은 서술 순서를 유지할 수 있어야 완료로 기록합니다.",
    ])
    return profile


def build_description(row: dict[str, str], profile: dict[str, str], page_index: int) -> str:
    return meta_description(row, page_index)


def high2_focus_section(row: dict[str, str], profile: dict[str, str]) -> str:
    local = row_value(row, "근처 수업가능 동네")
    cards = [
        ("내신 심화", "학생이 가져온 학교 자료의 범위와 완료 날짜를 확인하고 누적 개념 풀이 기록과 연결합니다."),
        ("누적 개념 연결", profile["common_focus"]),
        ("과정형 풀이", "조건 해석, 개념 선택, 첫 식, 식 전개와 검산을 나눠 막힌 단계를 표시합니다."),
        ("서술형 답안", profile["writing_focus"]),
        ("오답 재학습", "오류 원인을 고친 뒤 간격을 두고 다시 풀어 새 조건에서도 적용되는지 봅니다."),
        ("모의평가", profile["mock_focus"]),
        ("시간 관리", profile["time_focus"]),
        ("고1 개념 재연결", "현재 단원에 실제로 쓰이는 이전 개념을 골라 짧게 복습하고 새 문항에 적용합니다."),
    ]
    cards.sort(key=lambda item: base.seed_for(CATEGORY, local, "card", item[0]))
    card_html = "".join(
        f'<article class="article-target-card"><h3>{esc(title)}</h3><p>{esc(body)}</p></article>'
        for title, body in cards
    )
    intro = choose(local, "high2-intro", [
        f"{local} 고2 수학은 내신 진도와 모의평가를 한 기록으로 뭉치지 않고 자료별로 막힌 단계를 구분해야 합니다.",
        f"{local} 학생의 시작점은 선행 분량보다 최근 답안의 조건 해석과 풀이 근거에서 찾습니다.",
        "고등학교 2학년의 수학 계획은 학교 자료, 오답 재학습과 실제 주간 시간을 함께 놓고 정해야 합니다.",
        "내신과 모의평가 결과가 다르면 문제 이름보다 개념 선택·식 전개·검산·시간의 차이를 먼저 봅니다.",
        "현재 단원에서 막힌 문제는 고1까지의 공백과 새 조건 표현 중 어느 쪽이 원인인지 분리합니다.",
        "서술형 답안은 정답 여부와 별도로 조건, 사용 개념, 풀이 과정과 결론의 연결을 확인합니다.",
        "많은 문제를 한 번 푸는 것보다 오답을 며칠 뒤 다시 풀고 근거를 설명하는 과정이 우선입니다.",
        "고2 학습은 학교 일정과 통학 시간을 제외한 실제 복습 시간 안에서 내신과 모의 학습을 배치합니다.",
    ])
    return f'''<section class="article-section high1-transition-panel"><p class="article-eyebrow">SECOND-YEAR MATH FRAME</p><h2>{esc(local)} 고2 수학의 내신·누적 개념·모의평가 설계</h2><p>{esc(intro)} {esc(profile['common_focus'])}</p><div class="article-target-list">{card_html}</div></section>'''


def build_learning_article(row: dict[str, str], profile: dict[str, str], page_index: int) -> str:
    return adapt_high2(_build_article_high1(row, profile, page_index))


def build_faqs(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    local = row_value(row, "근처 수업가능 동네")
    faqs = list(adapt_high2(high1._middle3_faqs(row, profile)))
    dedicated = (
        f"{local} 고2 수학에서 내신과 모의평가는 어떻게 나눠 준비하나요?",
        f"내신은 학생이 가져온 학교 범위와 과정형 답안의 완료 기록을 중심으로, 모의평가는 낯선 조건에서 개념을 선택한 과정과 시간 배분을 중심으로 봅니다. {profile['mock_focus']} {profile['time_focus']}",
    )
    if len(faqs) < 7:
        faqs.append(dedicated)
    else:
        faqs[-1] = dedicated
    if len(faqs) != 7:
        raise ValueError(f"{local} 고2 수학 FAQ가 7개가 아닙니다: {len(faqs)}")
    return faqs


def build_checklist(row: dict[str, str], profile: dict[str, str], page_index: int) -> list[tuple[str, str]]:
    checklist = list(adapt_high2(high1._middle3_checklist(row, profile, page_index)))
    checklist.append(("내신·모의평가 시간", profile["time_focus"]))
    return checklist


def build_parent_views(row: dict[str, str], profile: dict[str, str]) -> list[str]:
    local = row_value(row, "근처 수업가능 동네")
    notes = list(adapt_high2(high1._middle3_parent_views(row, profile)))
    note = f"{local} 상담에서는 내신과 모의평가를 한 점수로 합치지 말고 누적 개념, 풀이 과정, 서술형, 오답 재학습과 시간 중 차이가 시작된 지점을 확인할 수 있습니다."
    return (notes[:2] + [note]) if len(notes) >= 2 else (notes + [note])


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
    adjusted = list(related)
    adjusted.append((f"{local} {PREVIOUS_TOKEN}", canonical(PARENT, "고1수학학원", local)))
    schema = adapt_high2(high1._middle3_json_ld(row, exact_description, page_url, rep_image, body_image, map_image, faqs, adjusted))
    schema_text = json.dumps(schema, ensure_ascii=False).replace(PREVIOUS_TOKEN, "고1 수학학원")
    schema = json.loads(schema_text)
    grades = original_grades(row)
    for node in schema.get("@graph", []):
        if not isinstance(node, dict):
            continue
        if _has_type(node, "EducationalOrganization") or _has_type(node, "LocalBusiness"):
            node["educationalLevel"] = grades
            node["knowsAbout"] = ["고2 수학", "내신 심화", "누적 개념", "과정형 풀이", "서술형", "오답 재학습", "모의평가", "시간 관리"]
        if _has_type(node, "WebPage") or _has_type(node, "Article"):
            node["description"] = exact_description
        if _has_type(node, "WebPage"):
            node["about"] = [{"@type": "Place", "name": f"{row_value(row, '지역')} {row_value(row, '시or구')} {local}"}, {"@type": "Thing", "name": "고2 수학학원"}, {"@type": "Thing", "name": "고2 내신과 모의평가"}]
        if _has_type(node, "Service"):
            node["serviceType"] = "고등학교 2학년 수학 학습관리"
            node["audience"] = {"@type": "EducationalAudience", "educationalRole": "고등학교 2학년 학생 및 학부모"}
            node["about"] = ["고2 수학", "내신 심화", "누적 개념", "과정형 풀이", "서술형", "오답 재학습", "모의평가", "시간 관리"]
        if _has_type(node, "Article"):
            node["articleSection"] = [row_value(row, "지역"), row_value(row, "시or구"), local, "고2 수학", "내신 심화", "누적 개념", "과정형 풀이", "서술형", "모의평가", "시간 관리"]
            node["datePublished"] = PUBLISH_DATE
            node["dateModified"] = PUBLISH_DATE
    return schema


def append_previous_link(markup: str, local: str) -> str:
    anchor = (
        f'<a class="child-page-button" href="../../고1수학학원/{quote(local, safe="")}/index.html">'
        f'{esc(local)} 고1 수학학원</a>'
    )
    pattern = re.compile(
        r'(<section\b[^>]*class="[^"]*local-page-nav[^"]*".*?<div class="child-button-grid">)(.*?)(</div>\s*</section>)',
        re.I | re.S,
    )
    return pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}{anchor}{match.group(3)}", markup, count=1)


def detail_html(
    row: dict[str, str], manuscript: str, repeated_signatures: set[str],
    image_row: dict[str, str], rep_image: str, map_name: str,
    peer_locals: list[str], page_index: int,
) -> str:
    local = row_value(row, "근처 수업가능 동네")
    proxy = high2_row(row, page_index)
    markup = high1._middle3_detail_html(
        proxy, manuscript, repeated_signatures, image_row, rep_image, map_name,
        peer_locals, page_index,
    )
    markup = adapt_high2(markup)
    markup = high1.restore_grade_facts(markup, proxy, row)
    grades = split_items(row_value(row, "가능학년\n(수학)"))
    if "고2" not in grades:
        markup = re.sub(
            r'(<div class="subject-grade-panel">.*?<div class="subject-school-tags">.*?</div>)',
            lambda match: f'{match.group(1)}<p class="subject-empty-note">고2 수학 개설 여부는 상담 확인 필요</p>',
            markup, count=1, flags=re.S,
        )
    return append_previous_link(markup, local)


def hub_page(rows: list[dict[str, str]]) -> str:
    proxies = [high2_row(row, index) for index, row in enumerate(rows)]
    markup = adapt_high2(high1._middle3_hub_page(proxies))
    old = "371개 지역의 고2 수학학원 선택 기준과 내신·서술형·누적 공백·고2 학습 심화 학습·시간 관리 확인 항목을 정리했습니다."
    new = "371개 지역의 고2 수학학원 선택 기준과 공개 센터 정보, 내신 심화·누적 개념·과정형 풀이·서술형·오답 재학습·모의평가·시간 관리 항목을 정리했습니다."
    return markup.replace(old, new)


def activate() -> None:
    high1.CATEGORY = CATEGORY
    high1.CATEGORY_LABEL = CATEGORY_LABEL
    high1.PUBLISH_DATE = PUBLISH_DATE
    high1.adapt_high1 = adapt_high2
    high1.high1_row = high2_row
    high1.original_grades = original_grades
    high1.meta_description = meta_description
    high1.seed_manuscript = seed_manuscript
    high1.load_manuscripts = load_manuscripts
    high1.page_profile = page_profile
    high1.build_description = build_description
    high1.high1_focus_section = high2_focus_section
    high1.build_learning_article = build_learning_article
    high1.build_faqs = build_faqs
    high1.build_checklist = build_checklist
    high1.build_parent_views = build_parent_views
    high1.page_json_ld = page_json_ld
    high1.detail_html = detail_html
    high1.hub_page = hub_page
    middle3.CATEGORY = CATEGORY
    middle3.CATEGORY_LABEL = CATEGORY_LABEL
    middle3.PUBLISH_DATE = PUBLISH_DATE
    middle3.load_manuscripts = load_manuscripts
    middle3.sanitize_middle3_manuscript = lambda value, row: value
    middle3.contextualize_manuscript = lambda raw, row, repeated: adapt_high2(middle3.diversify_paragraphs(raw, row, int(row.get("__high1_index", "0")), 4000))
    middle3.build_description = build_description
    middle3.page_profile = page_profile
    middle3.build_learning_article = build_learning_article
    middle3.build_faqs = build_faqs
    middle3.build_checklist = build_checklist
    middle3.build_parent_views = build_parent_views
    middle3.page_json_ld = page_json_ld
    middle3.detail_html = detail_html
    middle3.hub_page = hub_page


def main() -> None:
    activate()
    middle3.main()


if __name__ == "__main__":
    main()
