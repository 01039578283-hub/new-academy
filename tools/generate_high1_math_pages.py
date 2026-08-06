from __future__ import annotations

"""공개 센터 사실과 고1 수학 학습 의도로 371개 지역 페이지를 생성한다.

외부 엑셀 원고는 사용하지 않는다. 검증을 마친 중3 수학 생성기의 사실 확인,
상호 내부링크와 화면/JSON-LD 일치 구조를 재사용하되, 본문은 고교 첫 내신,
공통수학, 과정형 풀이, 모의평가와 학습 시간 관리에 맞게 새로 구성한다.
"""

import json
import re
from urllib.parse import quote

import generate_middle3_math_pages as middle3


base = middle3.base
DOMAIN = base.DOMAIN
SITE_NAME = base.SITE_NAME
PARENT = "과목별학원"
CATEGORY = "고1수학학원"
CATEGORY_LABEL = "고1 수학학원"
PUBLISH_DATE = "2026-08-07"
PREVIOUS_LABEL_TOKEN = "__SAME_TOWN_MIDDLE3_MATH__"

esc = base.esc
row_value = base.row_value
split_items = base.split_items
canonical = middle3.canonical

_middle3_profile = middle3.page_profile
_middle3_article = middle3.build_learning_article
_middle3_faqs = middle3.build_faqs
_middle3_checklist = middle3.build_checklist
_middle3_parent_views = middle3.build_parent_views
_middle3_json_ld = middle3.page_json_ld
_middle3_detail_html = middle3.detail_html
_middle3_hub_page = middle3.hub_page


def choose(local: str, label: str, values: list[str]) -> str:
    return values[base.seed_for(CATEGORY, local, label) % len(values)]


def adapt_high1(value):
    """중3 화면 문맥만 고1 수학으로 전환하고 누적 학년 설명은 보존한다."""
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
        ("중3 수학", "고1 수학"),
        ("중3 학생", "고1 학생"),
        ("중3 과정", "고1 과정"),
        ("중3 내신", "고1 첫 내신"),
        ("중3", "고1"),
        ("고교 진입 전", "고교 첫 학년 적응"),
        ("고교 과정에 들어가기 전", "고교 첫 학년 수업에서"),
        ("고교 선행", "고교 첫 내신"),
        ("중학교 안내", "고등학교 안내"),
        ("개 중학교", "개 고등학교"),
        ("중학교명이", "고등학교명이"),
        ("중학교명", "고등학교명"),
        ("현재 중학교", "현재 고등학교"),
        ("중학교 자료", "고등학교 자료"),
        ("MIDDLE 3 MATH ROADMAP", "HIGH SCHOOL FIRST-YEAR MATH ROADMAP"),
        ("MIDDLE 3 MATH GUIDE", "HIGH SCHOOL FIRST-YEAR MATH GUIDE"),
        ("MIDDLE 3 MATH DIRECTORY", "HIGH SCHOOL FIRST-YEAR MATH DIRECTORY"),
    )
    for before, after in replacements:
        value = value.replace(before, after)
    return value


def high1_row(row: dict[str, str], index: int | None = None) -> dict[str, str]:
    """중3 엔진이 실제 고1 가능 학년과 공개 고등학교 열을 읽도록 대응한다."""
    proxy = dict(row)
    grades = split_items(row_value(row, "가능학년\n(수학)"))
    proxy_grades = [
        "중3" if grade == "고1" else ("중학교 3학년" if grade == "중3" else grade)
        for grade in grades
    ]
    proxy["가능학년\n(수학)"] = ", ".join(proxy_grades)
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
        f"{region} {district} {local} 고1 수학학원 비교를 위해",
        f"{local} 고1 수학의 첫 내신 준비를 시작하기 전에",
        f"{center} 공개 정보와 학생의 최근 수학 답안을 바탕으로",
        f"{region} {local}에서 고등학교 1학년 수학 수업을 살필 때",
        f"{district} {local} 고1 수학 상담을 준비하며",
        f"{local} 학생의 공통수학 적응 순서를 정할 수 있도록",
        f"공개된 {center} 자료 범위에서",
        f"{local} 고1 수학학원 선택 기준으로",
    ]
    focuses = [
        "첫 내신, 공통수학 개념 연결, 풀이 과정, 서술형과 오답 재학습의 확인 순서를 정리했습니다.",
        "중학교 누적 공백과 고교 진도를 구분하고 모의평가와 시간 관리 기준을 함께 안내합니다.",
        "검증된 센터·고등학교·가능 학년 정보와 고1 수학 상담 체크리스트를 구성했습니다.",
        "조건 해석에서 식 전개, 검산, 과정형 답안과 간격 재풀이로 이어지는 학습 흐름을 설명합니다.",
        "학교 자료와 학력평가 오류를 나눠 보고 실제 학습 시간 안에서 우선순위를 정하는 방법을 담았습니다.",
        "점수나 학교별 출제를 단정하지 않고 현재 답안과 공개 정보로 확인할 상담 항목을 제시합니다.",
        "고1 가능 학년, 공개 학교와 교습비를 확인하면서 내신 적응과 주간 계획 기준을 함께 살펴봅니다.",
        "무리한 진도 확장보다 공통수학 개념을 새 조건에 적용하고 풀이 근거를 남기는 과정을 안내합니다.",
    ]
    return f"{openings[page_index % 8]} {focuses[(page_index // 8) % 8]}"


def _context_pair(page_index: int, offset: int = 0) -> str:
    observations = [
        "첫 식을 세우기 전 조건 표시", "다항식 전개에서 부호가 바뀐 지점", "방정식의 해를 원래 조건에 대입한 기록",
        "부등식 변형 뒤 범위를 확인한 과정", "함수의 식과 그래프를 연결한 설명", "도형의 방정식에서 좌표를 정한 근거",
        "경우를 나누는 기준이 겹치지 않는지 본 흔적", "집합 기호를 문장으로 다시 풀어쓴 내용", "행렬 계산 순서를 단계별로 적은 풀이",
        "맞힌 문항에서도 생략된 검산 단계", "서술형 답안의 조건·식·결론 연결", "오답을 며칠 뒤 해설 없이 다시 푼 결과",
        "학교 진도와 누적 복습을 구분한 표시", "모의평가에서 시간이 길어진 문항 유형", "풀이 중 질문이 시작된 정확한 줄",
        "공식을 선택한 이유를 학생 말로 설명한 내용", "유사 문항에서 같은 개념을 찾은 과정", "주중 계획에서 실제 완료한 수학 분량",
        "계산 실수와 개념 오해를 나눈 기록", "새 조건에서도 풀이 순서가 유지된 결과",
    ]
    actions = [
        "최근 시험지와 현재 교재를 나란히 놓고 확인합니다.", "정답을 가린 재풀이와 비교해 독립 해결 범위를 정합니다.",
        "오류 원인별로 나눈 뒤 다음 복습 날짜를 적습니다.", "학생의 말 설명과 종이에 남은 식을 서로 대조합니다.",
        "학교 자료에서 확인되는 범위만 주간 계획에 반영합니다.", "풀이 정확도가 안정된 뒤 소요 시간과 검산 시간을 기록합니다.",
        "현재 단원을 막는 이전 개념만 짧게 복원해 바로 적용합니다.", "수업 직후와 간격을 둔 재현 결과를 구분해 남깁니다.",
        "과정형 문항에서 빠진 근거를 보완한 뒤 새 문제에 적용합니다.", "학교 일정과 통학 시간을 뺀 실제 복습 시간에 배치합니다.",
        "맞힌 문제와 틀린 문제의 첫 단계가 어떻게 다른지 비교합니다.", "완료하지 못한 항목만 다음 계획으로 넘겨 우선순위를 좁힙니다.",
        "내신 자료와 모의평가 기록을 섞지 않고 오류 유형을 나눕니다.", "질문할 부분을 표시한 뒤 필요한 설명 범위만 선택합니다.",
        "기본 문제의 재현이 확인된 뒤 조건이 달라진 문항으로 확장합니다.", "식 전개와 결론 사이의 논리 흐름을 한 문장으로 설명하게 합니다.",
        "정확도·풀이 근거·시간을 각각 기록해 다음 분량을 조정합니다.", "시험 범위 확정 전후에 사용할 복습표를 서로 다르게 구성합니다.",
        "해설을 본 문제는 다른 날 새 종이에서 다시 풀어 완료 여부를 봅니다.", "상담 질문으로 옮겨 실제 관리 기록에 반영되는지 확인합니다.",
    ]
    code = (page_index + offset) % (len(observations) * len(actions))
    return f"{observations[code % len(observations)]}을 {actions[(code // len(observations)) % len(actions)]}"


def seed_manuscript(row: dict[str, str], page_index: int) -> str:
    local = row_value(row, "근처 수업가능 동네")
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    schools = split_items(row_value(row, "타깃학교\n(고)"))
    evidence = schools[base.seed_for(CATEGORY, local, "seed-school") % len(schools)] if schools else "학생이 가져온 현재 고등학교 자료"
    first = _context_pair(page_index, 0)
    second = _context_pair(page_index, 97)
    third = _context_pair(page_index, 211)
    fourth = _context_pair(page_index, 307)
    order = page_index % 4
    titles = [
        "고교 첫 수학 진단에서 답보다 먼저 볼 것",
        "공통수학 개념을 현재 풀이와 연결하는 순서",
        "내신과 모의평가 기록을 분리하는 이유",
        "서술형과 오답 재학습의 완료 기준",
    ]
    titles = titles[order:] + titles[:order]
    return f'''<section class="shell academy-section article-main manuscript-panel">
      <section class="article-hero"><p class="article-eyebrow">FIRST-YEAR MATH NOTE</p><h2>{esc(region)} {esc(district)} {esc(local)} 고1 수학 점검 기록</h2><p class="article-intro">{esc(local)} 고1 수학은 진도표만 비교하기보다 첫 내신과 공통수학 답안에서 조건 해석, 풀이 과정, 서술형 근거와 오답 재학습이 어떻게 이어지는지 확인해야 합니다.</p></section>
      <section class="article-section article-local-feature-section"><h2>{esc(titles[0])}</h2><p>{esc(evidence)}의 최근 풀이에서 {esc(first)} 고등학교 1학년의 첫 시험은 중학교 누적 개념을 새 기호와 조건에 적용하는 과정까지 함께 봅니다.</p></section>
      <section class="article-section article-local-feature-section"><h2>{esc(titles[1])}</h2><p>다항식·방정식·부등식·함수처럼 공통수학에서 다시 연결되는 개념은 단원 이름을 외우는 데서 끝내지 않습니다. {esc(second)}</p></section>
      <section class="article-section article-local-feature-section"><h2>{esc(titles[2])}</h2><p>학교 내신은 학생이 가져온 실제 범위와 과정형 문항을, 모의평가와 학력평가는 낯선 조건에서의 판단 순서와 시간 배분을 중심으로 기록합니다. {esc(third)}</p></section>
      <section class="article-section article-local-feature-section"><h2>{esc(titles[3])}</h2><p>오답 관리는 답을 고치는 것으로 끝내지 않고 오류 원인, 수정한 풀이 근거, 다시 풀 날짜와 결과를 남겨야 합니다. {esc(fourth)}</p></section>
    </section>'''


def load_manuscripts() -> list[str]:
    rows = base.read_csv(base.CENTER_CSV)
    return [seed_manuscript(row, index) for index, row in enumerate(rows)]


def sanitize_manuscript(value: str, row: dict[str, str]) -> str:
    return value


def contextualize_manuscript(raw: str, row: dict[str, str], repeated: set[str]) -> str:
    page_index = int(row.get("__high1_index", "0"))
    return adapt_high1(middle3.diversify_paragraphs(raw, row, page_index, 4000))


def page_profile(row: dict[str, str]) -> dict[str, str]:
    local = row_value(row, "근처 수업가능 동네")
    profile = adapt_high1(_middle3_profile(row))
    profile["common_focus"] = choose(local, "common-focus", [
        "다항식의 구조와 식 변형을 조건에 맞게 선택하고 전개 뒤 부호를 검산합니다.",
        "방정식과 부등식은 해를 구한 뒤 원래 조건과 범위에 맞는지 다시 확인합니다.",
        "함수는 식·표·그래프가 나타내는 같은 관계를 바꾸어 설명할 수 있는지 봅니다.",
        "도형의 방정식은 좌표와 조건을 표시한 뒤 사용할 식의 근거를 순서대로 적습니다.",
        "집합과 명제는 기호를 문장으로 풀고 참·거짓 판단의 조건을 빠뜨리지 않게 합니다.",
        "경우의 수는 나누는 기준이 겹치거나 빠지지 않았는지 작은 사례와 함께 확인합니다.",
        "행렬은 계산 규칙만 외우지 않고 연산 순서와 결과가 나타내는 정보를 설명합니다.",
        "중학교 함수·방정식 지식을 공통수학의 새 표현에 연결해 개념 전환 지점을 확인합니다.",
    ])
    profile["mock_focus"] = choose(local, "mock-focus", [
        "모의평가는 정답 수보다 조건 해석·개념 선택·식 전개·시간 중 어디에서 막혔는지 기록합니다.",
        "전국연합 학력평가는 학교 내신과 오류 유형을 섞지 않고 낯선 문항의 첫 접근을 따로 봅니다.",
        "시간 제한 없이 정확히 푼 결과와 제한 시간 안 결과를 비교해 문항 순서를 조정합니다.",
        "학력평가 오답은 해설을 본 뒤 끝내지 않고 같은 개념의 새 문항에서 풀이 순서를 재현합니다.",
        "모의고사에서 오래 걸린 문항은 계산량과 조건 판단 시간을 나눠 다음 연습 기준을 정합니다.",
        "내신 자료와 모의평가의 공통 오류가 확인될 때만 같은 복습 항목으로 묶어 관리합니다.",
        "답안 제출 전 남길 검산 시간을 정하고 쉬운 문항의 실수와 어려운 문항의 판단 오류를 구분합니다.",
        "첫 모의평가 한 번으로 수준을 단정하지 않고 간격을 둔 풀이 기록과 함께 변화 여부를 봅니다.",
    ])
    profile["time_focus"] = choose(local, "time-focus", [
        "학교 과제와 통학 시간을 제외한 실제 주중 여유 시간으로 현행·오답·모의 복습을 나눕니다.",
        "수업 당일 풀이 정리, 주중 재풀이, 주말 누적 확인의 날짜를 각각 적습니다.",
        "시험 범위 발표 전에는 누적 공백을, 발표 뒤에는 학교 자료와 서술형 완료를 우선합니다.",
        "계획한 문제 수보다 해설 없이 완료한 문항과 다시 확인할 날짜로 다음 분량을 정합니다.",
        "내신 준비일과 모의평가 복습일을 분리해 한날에 수학 과제가 과도하게 몰리지 않게 합니다.",
        "정확한 풀이 과정이 안정되기 전에는 시간 제한을 늦추고 이후 단계적으로 적용합니다.",
        "학교 일정이 바뀌면 미완료 항목과 옮긴 날짜를 함께 기록해 계획이 사라지지 않게 합니다.",
        "질문 해결일과 해설 없이 다시 푸는 날을 다르게 두어 설명 의존도를 확인합니다.",
    ])
    profile["writing_focus"] = choose(local, "writing-focus", [
        "서술형은 조건·사용 개념·식 전개·결론이 한 흐름으로 읽히는지 확인합니다.",
        "과정형 문항은 답이 맞아도 생략한 근거를 찾아 학생 말과 수식으로 보완합니다.",
        "풀이 과정의 첫 식이 문제 조건에서 어떻게 나왔는지 한 문장으로 설명하게 합니다.",
        "부호와 계산을 고친 뒤에도 사용한 개념의 근거가 답안에 남는지 다시 봅니다.",
        "같은 답에 이르는 다른 풀이를 비교해 더 안정적으로 재현할 수 있는 순서를 고릅니다.",
        "답안 작성 뒤 조건 누락, 식의 연결, 결론 표현을 일정한 검토 순서로 확인합니다.",
        "해설 문장을 그대로 옮기지 않고 학생이 실제로 사용한 풀이 근거만 다시 작성합니다.",
        "조건이 달라진 문항에서도 서술 순서를 유지할 수 있어야 완료한 풀이로 봅니다.",
    ])
    return profile


def build_description(row: dict[str, str], profile: dict[str, str], page_index: int) -> str:
    return meta_description(row, page_index)


def high1_focus_section(row: dict[str, str], profile: dict[str, str]) -> str:
    local = row_value(row, "근처 수업가능 동네")
    cards = [
        ("첫 내신 적응", "학생이 가져온 학교 자료의 범위와 완료 날짜를 확인하고 공통수학 풀이 기록과 연결합니다."),
        ("공통수학 개념", profile["common_focus"]),
        ("풀이 과정", "조건 해석, 개념 선택, 첫 식, 식 전개와 검산을 나눠 막힌 단계를 표시합니다."),
        ("서술형 답안", profile["writing_focus"]),
        ("오답 재학습", "오류 원인을 고친 뒤 간격을 두고 다시 풀어 같은 개념이 새 문항에서도 적용되는지 봅니다."),
        ("모의평가", profile["mock_focus"]),
        ("학습 시간 관리", profile["time_focus"]),
        ("중학교 개념 연결", "방정식·함수·도형의 누적 지식이 고교의 기호와 조건에서도 이어지는지 확인합니다."),
    ]
    cards.sort(key=lambda item: base.seed_for(CATEGORY, local, "high1-card", item[0]))
    card_html = "".join(
        f'<article class="article-target-card"><h3>{esc(title)}</h3><p>{esc(body)}</p></article>'
        for title, body in cards
    )
    intro = choose(local, "high1-intro", [
        f"{local} 고1 수학은 첫 내신 진도와 모의평가를 한 기록으로 뭉치지 않고 자료별로 막힌 단계를 구분해야 합니다.",
        f"{local} 학생의 공통수학 시작점은 선행 분량보다 최근 답안의 조건 해석과 풀이 근거에서 찾습니다.",
        f"고등학교 1학년의 수학 계획은 학교 자료, 오답 재학습과 실제 주간 학습 시간을 함께 놓고 정해야 합니다.",
        f"첫 내신과 학력평가의 결과가 다르면 문제 유형보다 개념 선택·식 전개·검산·시간의 차이를 먼저 봅니다.",
        f"공통수학에서 막힌 문제는 중학교 누적 공백과 고교의 새 표현 중 어느 쪽이 원인인지 분리합니다.",
        f"서술형 답안은 정답 여부와 별도로 조건, 사용 개념, 풀이 과정과 결론의 연결을 확인합니다.",
        f"많은 문제를 한 번 푸는 것보다 오답을 며칠 뒤 다시 풀고 근거를 설명하는 과정이 우선입니다.",
        f"고1 첫 학기에는 학교 일정과 통학 시간을 제외한 실제 복습 시간 안에서 내신과 모의 학습을 배치합니다.",
    ])
    return f'''<section class="article-section high1-transition-panel"><p class="article-eyebrow">FIRST-YEAR MATH FRAME</p><h2>{esc(local)} 고1 수학의 첫 내신·공통수학·모의평가 설계</h2><p>{esc(intro)} {esc(profile['common_focus'])}</p><div class="article-target-list">{card_html}</div></section>'''


def build_learning_article(row: dict[str, str], profile: dict[str, str], page_index: int) -> str:
    markup = adapt_high1(_middle3_article(row, profile, page_index))
    section = high1_focus_section(row, profile)
    head, separator, tail = markup.rpartition("</section>")
    combined = f"{head}{section}</section>{tail}" if separator else f"{markup}{section}"
    return adapt_high1(middle3.diversify_paragraphs(combined, row, page_index, 9000))


def build_faqs(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    local = row_value(row, "근처 수업가능 동네")
    faqs = list(adapt_high1(_middle3_faqs(row, profile)))
    faqs = [
        (
            "공통수학 진도와 고1 첫 내신 중 무엇을 먼저 확인해야 하나요?",
            f"진도 범위를 일률적으로 넓히기보다 학생이 가져온 현재 학교 자료와 최근 답안에서 누적 개념의 연결 상태를 먼저 봅니다. {profile['common_focus']}",
        )
        if "고교 첫 내신과 고1 첫 내신" in question
        else (question, answer)
        for question, answer in faqs
    ]
    dedicated = (
        f"{local} 고1 수학에서 첫 내신과 모의평가는 어떻게 나눠 준비하나요?",
        f"첫 내신은 학생이 가져온 학교 범위와 과정형 답안의 완료 기록을 중심으로, 모의평가는 낯선 조건의 개념 선택과 시간 배분을 중심으로 봅니다. {profile['mock_focus']} {profile['time_focus']}",
    )
    if len(faqs) < 7:
        faqs.append(dedicated)
    else:
        faqs[-1] = dedicated
    if len(faqs) != 7:
        raise ValueError(f"{local} 고1 수학 FAQ가 7개가 아닙니다: {len(faqs)}")
    return faqs


def build_checklist(row: dict[str, str], profile: dict[str, str], page_index: int) -> list[tuple[str, str]]:
    checklist = list(adapt_high1(_middle3_checklist(row, profile, page_index)))
    checklist.append(("첫 내신·모의 시간", profile["time_focus"]))
    return checklist


def build_parent_views(row: dict[str, str], profile: dict[str, str]) -> list[str]:
    local = row_value(row, "근처 수업가능 동네")
    notes = list(adapt_high1(_middle3_parent_views(row, profile)))
    note = f"{local} 상담에서는 첫 내신과 모의평가를 한 점수로 합치지 말고 공통수학 개념, 풀이 과정, 서술형, 오답 재학습과 시간 관리 중 어디서 차이가 시작됐는지 질문할 수 있습니다."
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
    adjusted.append((PREVIOUS_LABEL_TOKEN, canonical(PARENT, "중3수학학원", local)))
    schema = adapt_high1(
        _middle3_json_ld(row, exact_description, page_url, rep_image, body_image, map_image, faqs, adjusted)
    )
    grades = original_grades(row)
    for node in schema.get("@graph", []):
        if not isinstance(node, dict):
            continue
        if _has_type(node, "EducationalOrganization") or _has_type(node, "LocalBusiness"):
            node["educationalLevel"] = grades
            node["knowsAbout"] = ["고1 수학", "고교 첫 내신", "공통수학", "풀이 과정", "서술형", "오답 재학습", "모의평가", "시간 관리"]
        if _has_type(node, "WebPage"):
            node["description"] = exact_description
            node["about"] = [{"@type": "Place", "name": f"{row_value(row, '지역')} {row_value(row, '시or구')} {local}"}, {"@type": "Thing", "name": "고1 수학학원"}, {"@type": "Thing", "name": "고교 첫 내신과 공통수학"}]
        if _has_type(node, "Service"):
            node["serviceType"] = "고등학교 1학년 수학 학습관리"
            node["audience"] = {"@type": "EducationalAudience", "educationalRole": "고등학교 1학년 학생 및 학부모"}
            node["about"] = ["고1 수학", "첫 내신", "공통수학", "과정형 풀이", "서술형", "오답 재학습", "모의평가", "시간 관리"]
        if _has_type(node, "Article"):
            node["description"] = exact_description
            node["articleSection"] = [row_value(row, "지역"), row_value(row, "시or구"), local, "고1 수학", "첫 내신", "공통수학", "풀이 과정", "서술형", "모의평가", "시간 관리"]
            node["datePublished"] = PUBLISH_DATE
            node["dateModified"] = PUBLISH_DATE
    return schema


def restore_grade_facts(markup: str, proxy: dict[str, str], original: dict[str, str]) -> str:
    proxy_grades = split_items(row_value(proxy, "가능학년\n(수학)"))
    processed = [adapt_high1(grade) for grade in proxy_grades]
    actual = split_items(row_value(original, "가능학년\n(수학)"))
    markup = markup.replace(", ".join(processed), ", ".join(actual))
    markup = markup.replace(
        "".join(f"<span>{esc(grade)}</span>" for grade in processed),
        "".join(f"<span>{esc(grade)}</span>" for grade in actual),
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
        f'<a class="child-page-button" href="../../중3수학학원/{quote(local, safe="")}/index.html">'
        f'{esc(local)} 중3 수학학원</a>'
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
    proxy = high1_row(row, page_index)
    markup = _middle3_detail_html(
        proxy, manuscript, repeated_signatures, image_row, rep_image, map_name,
        peer_locals, page_index,
    )
    markup = adapt_high1(markup)
    markup = markup.replace(PREVIOUS_LABEL_TOKEN, f"{local} 중3 수학학원")
    markup = restore_grade_facts(markup, proxy, row)
    grades = split_items(row_value(row, "가능학년\n(수학)"))
    if "고1" not in grades:
        markup = re.sub(
            r'(<div class="subject-grade-panel">.*?<div class="subject-school-tags">.*?</div>)',
            lambda match: f'{match.group(1)}<p class="subject-empty-note">고1 수학 개설 여부는 상담 확인 필요</p>',
            markup,
            count=1,
            flags=re.S,
        )
    return append_previous_link(markup, local)


def hub_page(rows: list[dict[str, str]]) -> str:
    proxies = [high1_row(row, index) for index, row in enumerate(rows)]
    markup = adapt_high1(_middle3_hub_page(proxies))
    old = "371개 지역의 고1 수학학원 선택 기준과 내신·서술형·누적 공백·고교 첫 학년 적응 학습·시간 관리 확인 항목을 정리했습니다."
    new = "371개 지역의 고1 수학학원 선택 기준과 공개 센터 정보, 첫 내신·공통수학·풀이 과정·서술형·오답 재학습·모의평가·시간 관리 항목을 정리했습니다."
    return markup.replace(old, new)


def activate() -> None:
    middle3.CATEGORY = CATEGORY
    middle3.CATEGORY_LABEL = CATEGORY_LABEL
    middle3.PUBLISH_DATE = PUBLISH_DATE
    middle3.load_manuscripts = load_manuscripts
    middle3.sanitize_middle3_manuscript = sanitize_manuscript
    middle3.contextualize_manuscript = contextualize_manuscript
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
