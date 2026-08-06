from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import generate_middle2_math_pages as base


SITE = base.SITE
DOMAIN = base.DOMAIN
SITE_NAME = base.SITE_NAME
PHONE_DISPLAY = base.PHONE_DISPLAY
PHONE_LINK = base.PHONE_LINK
FORM_URL = base.FORM_URL
SMS_URL = base.SMS_URL
PUBLISH_DATE = base.PUBLISH_DATE

PARENT = "과목별학원"
CATEGORY = "중2영어학원"
CATEGORY_LABEL = "중2 영어학원"

esc = base.esc
row_value = base.row_value
split_items = base.split_items
canonical = base.canonical


def choose(local: str, label: str, values: list[str]) -> str:
    return values[base.seed_for(CATEGORY, local, label) % len(values)]


def existing_english_pages(row: dict[str, str]) -> list[Path]:
    parent = base.find_parent_page(row)
    if not parent:
        return []
    candidates = [
        parent.parent / "중1영어학원" / "index.html",
        parent.parent / "초6영어학원" / "index.html",
        parent,
    ]
    return [candidate for candidate in candidates if candidate.exists()]


def source_focus(row: dict[str, str]) -> dict[str, str | int]:
    """기존 전국학원 페이지를 읽고 강조 주제를 고르되 문장은 복사하지 않는다."""
    local = row_value(row, "근처 수업가능 동네")
    pages = existing_english_pages(row)
    source = " ".join(page.read_text(encoding="utf-8") for page in pages)
    themes = {
        "문법 적용": ["문법", "문장 구조", "시제", "품사"],
        "독해 정확도": ["독해", "해석", "지문", "문장"],
        "어휘 누적": ["어휘", "단어", "표현", "암기"],
        "서술형 준비": ["서술형", "영작", "쓰기", "답안"],
        "오답 재학습": ["오답", "재풀이", "틀린 이유", "복습"],
        "내신 일정": ["내신", "시험 범위", "학교 진도", "시험"],
    }
    scored = []
    for theme, terms in themes.items():
        count = sum(source.count(term) for term in terms)
        scored.append((count, base.seed_for(local, theme), theme))
    scored.sort(reverse=True)
    top = [item[2] for item in scored[:4]] or list(themes)
    focus = top[base.seed_for(local, "source-focus") % len(top)]
    return {"focus": focus, "source_pages": len(pages)}


def page_profile(row: dict[str, str]) -> dict[str, str]:
    local = row_value(row, "근처 수업가능 동네")
    reference = source_focus(row)
    students = [
        "단어는 외우지만 교과서 문장 안에서 뜻을 바로 연결하지 못하는 학생",
        "문법 문제는 맞히지만 서술형에서 어순과 형태를 자주 놓치는 학생",
        "문장을 끝까지 해석하기 전에 익숙한 단어만 보고 답을 고르는 학생",
        "교과서 본문 암기는 했지만 변형 문제에서 근거를 찾는 데 시간이 걸리는 학생",
        "시험 범위가 나온 뒤에도 어휘·문법·본문 복습 순서를 정하지 못하는 학생",
        "수업에서는 이해하지만 며칠 뒤 문법 개념을 문장에 적용하지 못하는 학생",
        "긴 문장에서 주어와 동사를 찾지 못해 해석 순서가 흔들리는 학생",
        "듣기와 독해는 괜찮지만 영작과 서술형 답안을 부담스러워하는 학생",
        "숙제는 끝내지만 틀린 문장을 다시 써 보지 않아 같은 실수를 반복하는 학생",
        "어휘 암기량은 충분하지만 유의어·반의어와 문맥 의미 구분이 약한 학생",
        "문제 풀이 속도에 집중해 지문의 연결어와 근거 문장을 놓치는 학생",
        "중1 기초 문법의 공백이 중2 교과서 해석까지 이어지는 학생",
        "시험 직전에 본문과 단어를 몰아서 보느라 누적 복습이 부족한 학생",
        "객관식 선택지는 구분하지만 왜 오답인지 설명하는 연습이 부족한 학생",
        "학습 계획은 세우지만 단어 확인과 본문 재독 날짜를 기록하지 않는 학생",
        "학교 프린트와 교과서의 우선순위를 정하지 못해 자료만 쌓이는 학생",
    ]
    priorities = [
        "최근 시험에서 어휘·문법·독해·서술형 오류를 먼저 분류합니다.",
        "교과서 진도와 누적 단어, 문법 공백을 한 표에 놓고 복습 순서를 정합니다.",
        "정답보다 지문에서 근거 문장을 표시하고 설명하는 과정을 확인합니다.",
        "문장 구조를 끊어 읽은 뒤 같은 문법이 쓰인 새 문장에 적용합니다.",
        "시험일까지 남은 주차를 기준으로 본문·문법·어휘 완료 기준을 나눕니다.",
        "수업 직후, 주중, 시험 전으로 단어와 오답을 다시 볼 시점을 정합니다.",
        "서술형 답안은 내용·어순·문법 형태를 따로 확인해 수정 이유를 남깁니다.",
        "현재 단원을 이해하는 데 필요한 중1 문장 구조부터 짧게 복원합니다.",
        "교과서와 학교 자료에서 반복되는 표현을 묶어 문맥과 함께 익힙니다.",
        "독해 속도보다 문단별 핵심 내용과 정답 근거의 정확도를 먼저 봅니다.",
        "틀린 선택지를 왜 고르면 안 되는지까지 말하게 해 판단 기준을 점검합니다.",
        "학교 시험 범위가 확정되기 전과 후의 학습 계획을 서로 다르게 세웁니다.",
    ]
    checks = [
        "최근 영어 시험에서 가장 많이 틀린 영역이 무엇인지",
        "교과서 본문을 보지 않고 핵심 문장을 설명할 수 있는지",
        "문법 개념을 새 문장에 적용할 때 어느 단계에서 막히는지",
        "누적 단어를 며칠 간격으로 다시 확인하고 있는지",
        "독해 정답의 근거 문장을 지문에서 직접 표시할 수 있는지",
        "서술형 답안의 어순과 동사 형태를 스스로 검토하는지",
        "학교 프린트와 교과서 중 먼저 복습할 자료가 정해져 있는지",
        "주중에 확보할 수 있는 실제 영어 복습 시간이 어느 정도인지",
        "오답 문장을 해설 없이 다시 해석하고 고칠 수 있는지",
        "시험 전 본문·어휘·문법 복습 완료 기준이 적혀 있는지",
        "질문이 생긴 문장에 표시하고 다음 수업에서 확인하는 습관이 있는지",
        "듣기·독해·문법·쓰기 중 점수 변동이 가장 큰 영역이 무엇인지",
    ]
    rhythms = [
        "수업 당일 핵심 문장 확인 → 이틀 뒤 변형 문장 적용 → 주말 누적 점검",
        "단어 의미 확인 → 교과서 문장 해석 → 문법 근거 표시 → 서술형 재작성",
        "짧은 진단 → 부족 영역 보완 → 학교 자료 적용 → 해설 없는 재확인",
        "본문 구조 파악 → 문단 요약 → 선택지 근거 찾기 → 틀린 선택지 교정",
        "주간 어휘 확인 → 문법 적용 문제 → 독해 시간 기록 → 오답 문장 복원",
        "시험 범위 분할 → 단원별 완료 표시 → 변형 문제 → 직전 근거 재확인",
        "중1 공백 복원 → 중2 교과서 연결 → 학교 프린트 적용 → 누적 복습",
        "읽기 전 예측 → 문장 구조 분석 → 핵심 내용 요약 → 답의 근거 설명",
    ]
    return {
        "student": choose(local, "student", students),
        "priority": choose(local, "priority", priorities),
        "check": choose(local, "check", checks),
        "rhythm": choose(local, "rhythm", rhythms),
        "source_focus": str(reference["focus"]),
        "source_pages": str(reference["source_pages"]),
    }


def contextual_note(row: dict[str, str], profile: dict[str, str], label: str) -> str:
    local = row_value(row, "근처 수업가능 동네")
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    evidence = schools[base.seed_for(CATEGORY, local, label, "school") % len(schools)] if schools else "현재 학교 자료"
    templates = [
        f"{local} 상담에서는 {evidence}의 실제 시험 범위를 준비해 이 기준이 현재 단원에도 맞는지 확인하는 편이 안전합니다.",
        f"{center}에 문의하기 전에는 {profile['check']}를 적어 두면 이 항목을 학생 상황과 연결해 설명받기 쉽습니다.",
        f"{region} {district} {local} 학생에게 적용할 때는 {profile['rhythm']}의 순서가 주간 일정 안에서 가능한지도 함께 계산해야 합니다.",
        f"{evidence} 자료가 있다면 정답 표시보다 틀린 문장과 수정 흔적을 가져가 수업 반영 방식을 구체적으로 확인할 수 있습니다.",
        f"{local}에서는 {profile['student']}에게 같은 기준을 적용했을 때 어느 단계에서 시간이 오래 걸리는지 따로 기록해 보는 것이 좋습니다.",
        f"이 항목은 {center}의 공개 정보만으로 수업 방식을 단정하기보다 실제 교재와 피드백 예시를 상담에서 확인하는 기준으로 사용합니다.",
        f"{district} 지역 학교라도 교과서와 평가 일정은 다를 수 있으므로 {evidence}의 현재 공지를 기준으로 분량을 다시 나눠야 합니다.",
        f"{local} 학습 계획에는 완료 여부뿐 아니라 며칠 뒤 해설 없이 다시 설명한 결과까지 남겨야 다음 복습량을 조정할 수 있습니다.",
        f"{profile['source_focus']}이 약한 경우에는 이 활동을 한 번에 길게 하기보다 수업 직후와 주중으로 나눠 재현 여부를 확인합니다.",
        f"{center} 상담에서는 이 기준이 평소 수업과 시험 범위 발표 이후에 각각 어떻게 달라지는지 질문해 보는 편이 좋습니다.",
        f"{evidence}를 포함한 학교 자료는 이름만 나열하지 않고 교과서 본문, 프린트, 수행평가 중 어떤 자료인지 구분해 준비합니다.",
        f"{local} 학생의 최근 답안에서 이 기준에 해당하는 문장을 한두 개 골라 두면 추상적인 수준 설명보다 시작점을 명확히 잡을 수 있습니다.",
        f"이 과정의 완료 기준은 문제 수가 아니라 학생이 근거를 말하고 비슷한 새 문장을 혼자 처리할 수 있는지로 정하는 편이 적절합니다.",
        f"{region} {district}의 통학 시간까지 고려해 수업일과 복습일이 겹치지 않도록 배치해야 계획이 시험 전까지 유지됩니다.",
        f"{profile['priority']} 이 원칙을 {evidence}의 현재 진도와 대조하면 먼저 보완할 영역과 미뤄도 되는 영역을 나눌 수 있습니다.",
        f"{local}에서는 학교 범위가 확정되기 전에는 누적 공백을, 확정된 뒤에는 교과서와 프린트 적용을 우선하는지 확인합니다.",
        f"{center}의 시간표와 함께 이 활동에 필요한 수업 외 복습 시간을 물어봐야 학생이 실제로 실행할 수 있는 분량을 정할 수 있습니다.",
        f"{evidence} 시험지를 활용한다면 맞힌 문제 중에서도 근거를 설명하지 못한 항목을 따로 표시해 우연한 정답을 구분합니다.",
        f"이 기준은 {local} 중2 영어 선택을 위한 비교 항목이며 특정 점수 변화나 결과를 예상하게 하는 문구로 사용하지 않습니다.",
        f"학생이 질문을 기다리지 않도록 막힌 문장에 표시하고, {center} 수업에서 확인한 뒤 유사 문장에 적용하는 단계까지 이어지는지 봅니다.",
        f"{district} {local}의 학교 일정과 학생의 다른 과제량을 함께 놓고 보면 같은 학습량이라도 완료 날짜를 다르게 정해야 할 수 있습니다.",
        f"{profile['student']}이라면 이 항목의 난도를 높이기 전에 기본 문장에서 정확하게 재현되는 횟수를 먼저 확인하는 편이 좋습니다.",
        f"공개된 학교명이 없는 경우에도 현재 교과서와 최근 답안을 기준으로 같은 확인 절차를 적용할 수 있으며 학교 정보는 임의로 만들지 않습니다.",
        f"{local} 상담 기록에는 처음 진단한 내용과 다음 확인 날짜를 함께 적어 두어 실제 피드백이 계획에 반영됐는지 비교합니다.",
    ]
    return choose(local, f"context-{label}", templates)


def build_manuscript(row: dict[str, str], profile: dict[str, str]) -> str:
    local = row_value(row, "근처 수업가능 동네")
    region = row_value(row, "지역")
    district = row_value(row, "시or구")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    grades = split_items(row_value(row, "가능학년\n(영어)"))
    available = "중2" in grades
    school_text = ", ".join(schools[:4]) if schools else "현재 재학 중학교"
    focus = profile["source_focus"]

    introductions = [
        f"{region} {district} {local}에서 중2 영어학원을 고를 때는 문제집의 난이도보다 학교 진도와 학생의 오류가 어떻게 연결되는지 먼저 확인해야 합니다. {profile['student']}이라면 {focus}부터 점검한 뒤 교과서와 학교 자료에 적용하는 흐름이 필요합니다.",
        f"중학교 2학년 영어는 단어, 문법, 독해와 서술형이 따로 움직이지 않습니다. {local} 학생에게 필요한 시작점은 최근 시험에서 막힌 영역을 나누고, {profile['rhythm']}의 순서로 혼자 다시 확인할 수 있게 만드는 것입니다.",
        f"{local} 중2 영어 상담에서는 선행 범위보다 최근 영어 답안에 남은 흔적을 보는 편이 정확합니다. {profile['check']}를 먼저 확인하면 {focus}와 다른 영역 사이의 연결 문제를 구체적으로 찾을 수 있습니다.",
        f"{district} 지역에서 중2 영어 내신을 준비한다면 교과서 본문 암기만으로 충분한지부터 다시 살펴야 합니다. 문장 구조, 단어의 문맥 의미, 지문 근거와 서술형 수정 과정을 함께 기록해야 변형 문제에도 대응할 수 있습니다.",
        f"영어 공부 시간이 길어도 복습 시점과 완료 기준이 없으면 시험 직전에 다시 처음부터 보게 됩니다. {local}에서는 {profile['priority']} 그 결과를 학교 진도와 연결해 주간 계획을 조정하는 방식이 실용적입니다.",
        f"{center}의 공개 정보와 기존 {local} 영어 안내를 함께 볼 때 핵심은 학생이 설명을 들은 뒤 스스로 문장을 읽고 고칠 수 있는지입니다. 중2 과정에서는 {focus}을 중심으로 어휘·독해·서술형까지 이어지는지 확인해야 합니다.",
        f"중2 영어는 중1에서 배운 기본 구조가 교과서의 긴 문장과 학교별 평가 문항으로 확장되는 시기입니다. {local} 학생의 현재 답안을 기준으로 공백을 찾고, 무리한 진도보다 재현 가능한 학습 순서를 세우는 것이 먼저입니다.",
        f"{school_text} 등 학교 자료를 준비할 때는 범위 자체보다 학생이 어디에서 해석을 멈추고 어떤 형태를 반복해 틀리는지 기록해야 합니다. {local} 중2 영어학원 비교도 이 기록을 수업에 반영하는지를 중심으로 진행하는 편이 좋습니다.",
    ]
    intro = choose(local, "intro", introductions)

    domain_variants = {
        "문법을 답이 아닌 문장 구조로 확인": [
            "교과서 범위의 문법 이름을 외우는 데서 끝내지 않고 주어·동사와 수식 관계를 표시한 뒤, 같은 구조가 쓰인 새 문장에서 형태를 선택하게 합니다.",
            "문법 문제의 정답 번호보다 문장 안에서 어떤 말이 무엇을 꾸미고 동사의 형태가 왜 달라지는지 표시한 뒤 변형 문장에 적용합니다.",
            "개념 설명을 들은 다음 교과서 문장에서 해당 구조를 찾고, 조건이 바뀐 문장을 스스로 고쳐 쓰는 단계까지 확인합니다.",
            "용어 암기에 머물지 않도록 문장 성분과 시제 단서를 먼저 찾게 하고 정답 형태를 선택한 근거를 짧게 적습니다.",
            "틀린 문법 문항은 규칙을 다시 읽는 데서 끝내지 않고 원래 문장과 수정 문장을 나란히 두어 달라진 부분을 설명하게 합니다.",
            "중1에서 배운 기본 구조가 흔들리는지와 현재 교과서의 새 문법을 적용하지 못하는지를 구분해 보완 순서를 정합니다.",
        ],
        "독해는 근거 문장과 연결어까지 표시": [
            "문장을 번역하는 것만으로 끝내지 않고 문단의 핵심 내용, 연결어, 대명사가 가리키는 대상과 선택지의 근거를 지문에서 직접 찾게 합니다.",
            "첫 문장부터 끝까지 같은 속도로 해석하기보다 문단 역할을 나누고 답을 판단한 근거가 어느 문장에 있는지 표시합니다.",
            "긴 문장에서 주어와 동사를 먼저 찾고 연결어 앞뒤의 관계를 정리한 뒤 선택지와 지문의 표현을 대조합니다.",
            "해석한 한국어만 확인하지 않고 대명사의 대상, 문단 전환과 핵심 표현을 찾아 한 문장으로 내용을 요약하게 합니다.",
            "독해 오답은 단어 부족, 문장 구조, 내용 연결과 선택지 해석 중 어디에서 시작됐는지 나눠 다음 지문에 적용합니다.",
            "시간을 줄이기 전에 문단마다 핵심 정보를 표시하고, 정답뿐 아니라 다른 선택지가 지문과 맞지 않는 이유까지 설명합니다.",
        ],
        "어휘는 교과서 문맥과 함께 누적": [
            "단어 뜻 하나만 외우기보다 교과서 속 쓰임, 품사 변화, 함께 쓰이는 표현과 유의어를 묶고 일정 간격으로 다시 확인합니다.",
            "단어장을 가리고 뜻을 말하는 단계에 더해 교과서 문장에서 어떤 품사와 의미로 쓰였는지 구분하게 합니다.",
            "새 단어와 이미 배운 표현을 따로 두지 않고 본문, 대화문과 학교 프린트에서 다시 만난 횟수를 기록합니다.",
            "철자와 대표 뜻만 확인하지 않고 파생어, 반대 표현과 자주 함께 쓰이는 말을 문장 단위로 묶어 복습합니다.",
            "시험 범위 단어는 당일 암기 결과보다 이틀 뒤와 주말에 문장 속 의미를 다시 떠올릴 수 있는지 확인합니다.",
            "알고 있는 단어인데 해석이 막힌 경우 품사와 문맥 의미를 잘못 판단했는지 살펴보고 해당 문장까지 함께 저장합니다.",
        ],
        "서술형은 수정 이유를 남기는 방식으로": [
            "답안을 다시 쓰게 할 때 철자만 고치지 않고 내용 누락, 어순, 동사 형태, 문법 조건을 나눠 어떤 이유로 수정했는지 기록합니다.",
            "정답 문장을 그대로 베끼기보다 문제의 조건을 표시하고 학생 답안에서 빠진 내용과 잘못된 형태를 구분해 고칩니다.",
            "서술형 오답은 내용 전달, 단어 선택, 어순과 문법 형태를 따로 채점해 다음 답안에서 먼저 볼 항목을 정합니다.",
            "한국어 뜻을 영어로 옮길 때 핵심 표현과 동사의 시제를 먼저 정한 뒤 문장 완성 후 조건 충족 여부를 검토합니다.",
            "고친 답안은 같은 날 한 번 쓰는 데서 끝내지 않고 며칠 뒤 비슷한 의미의 새 문장을 해설 없이 다시 작성합니다.",
            "부분 점수를 기대하기보다 요구된 표현, 문장 수와 문법 조건을 체크 목록으로 바꾸어 제출 전 스스로 확인하게 합니다.",
        ],
    }
    domains = [
        (title, choose(local, "domain-copy-" + title, variants))
        for title, variants in domain_variants.items()
    ]
    domains.sort(key=lambda item: base.seed_for(CATEGORY, local, item[0]))
    domain_cards = "".join(
        f"<article class=\"article-card\"><h3>{esc(title)}</h3><p>{esc(body)} {esc(choose(local, title, [profile['priority'], profile['rhythm']]))} {esc(contextual_note(row, profile, 'domain-' + title))}</p></article>"
        for title, body in domains
    )

    if schools:
        school_heading = f"{schools[0]} 등 학교 자료를 확인할 때의 기준"
        school_intro = (
            f"공개 센터 자료에는 {', '.join(schools)} 등이 수업 가능 학교로 기재되어 있습니다. "
            "학교별 실제 교과서, 시험 범위와 일정은 달라질 수 있으므로 특정 출제 경향을 임의로 단정하지 않고 현재 자료를 기준으로 확인합니다."
        )
    else:
        school_heading = "중학교명이 공개되지 않은 지역의 확인 기준"
        school_intro = (
            "공개 센터 자료에는 중학교명이 별도로 기재되어 있지 않습니다. 학교를 임의로 만들지 않고 상담 시 현재 교과서, 시험 범위, 프린트와 수행평가 일정을 확인해야 합니다."
        )
    school_cards_bank = [
        ("교과서와 부교재", "시험 범위에 포함된 본문, 대화문, 추가 읽기 자료와 학교 프린트의 우선순위를 구분합니다."),
        ("어휘 확인 범위", "본문 단어뿐 아니라 변형 형태, 숙어, 유의어와 수업 중 추가된 표현까지 포함되는지 확인합니다."),
        ("문법 적용 방식", "개념 설명 뒤 교과서 문장과 변형 문장에서 같은 구조를 찾아 적용하는지 살펴봅니다."),
        ("서술형 조건", "문장 수, 핵심 표현, 어순과 문법 조건을 나누고 답안을 고친 이유까지 확인합니다."),
        ("수행평가 일정", "말하기·쓰기 과제의 일정과 평가 조건은 학교 공지를 기준으로 별도 계획에 반영합니다."),
        ("시험 직전 재확인", "새 문제를 늘리기보다 틀린 문장과 근거를 해설 없이 다시 설명할 수 있는지 확인합니다."),
    ]
    offset = base.seed_for(CATEGORY, local, "school-cards") % len(school_cards_bank)
    school_cards = (school_cards_bank[offset:] + school_cards_bank[:offset])[:3]
    school_card_html = "".join(
        f"<article class=\"article-target-card\"><h3>{esc(title)}</h3><p>{esc(body)} {esc(contextual_note(row, profile, 'school-' + title))}</p></article>"
        for title, body in school_cards
    )

    process_sets = [
        [
            ("01. 최근 답안 진단", "시험지와 과제에서 어휘·문법·독해·쓰기 오류를 분리하고 가장 먼저 바꿀 한 가지를 정합니다."),
            ("02. 문장 단위 보완", "부족한 개념을 짧게 정리한 뒤 교과서 문장과 새 문장에 같은 기준을 적용합니다."),
            ("03. 학교 자료 연결", "현재 학교 진도와 프린트에 적용하면서 정답 근거와 수정 이유를 말하게 합니다."),
            ("04. 간격을 둔 재확인", "해설 없이 다시 해석하고 쓸 날짜를 정해 일시적인 암기인지 확인합니다."),
        ],
        [
            ("01. 범위와 일정 나누기", "시험일까지 남은 주차와 교과서·프린트·단어 범위를 작은 완료 단위로 나눕니다."),
            ("02. 핵심 구조 표시", "본문의 주어·동사·수식 관계와 시험 문법이 적용된 부분을 직접 표시합니다."),
            ("03. 변형 문제 설명", "답을 고른 이유와 다른 선택지가 틀린 이유를 지문 근거로 설명합니다."),
            ("04. 서술형 복원", "틀린 답안을 조건별로 고친 뒤 며칠 후 같은 의미의 새 문장을 다시 작성합니다."),
        ],
        [
            ("01. 어휘 재현 확인", "뜻을 가리고 말하는 것뿐 아니라 문장 속 품사와 쓰임을 구분할 수 있는지 봅니다."),
            ("02. 독해 흐름 정리", "문단마다 한 문장으로 요약하고 연결어와 대명사의 관계를 표시합니다."),
            ("03. 문법 근거 쓰기", "정답 형태를 선택한 근거를 짧게 적어 우연히 맞힌 문제를 구분합니다."),
            ("04. 누적 오답 갱신", "다시 맞힌 문제와 여전히 막히는 문제를 나눠 다음 주 복습량을 조정합니다."),
        ],
        [
            ("01. 중1 공백 찾기", "중2 문장을 읽는 데 필요한 기본 시제, 품사와 문장 성분의 공백을 먼저 확인합니다."),
            ("02. 현재 단원 연결", "복원한 개념을 현재 교과서 문장과 학교 자료에 바로 적용합니다."),
            ("03. 시간 제한 연습", "정확도가 확보된 뒤 독해와 문법 문제의 풀이 시간을 단계적으로 기록합니다."),
            ("04. 시험 전 압축", "단어·본문·문법·서술형의 남은 항목을 한 장의 확인표로 압축합니다."),
        ],
    ]
    process = choose(local, "process", process_sets)
    process_html = "".join(
        f"<article class=\"article-target-card\"><h3>{esc(title)}</h3><p>{esc(body)} {esc(contextual_note(row, profile, 'process-' + title))}</p></article>"
        for title, body in process
    )

    consultation_points = [
        ("학생 설명 비율", "선생님의 설명 뒤 학생이 문장 구조와 정답 근거를 자신의 말로 다시 설명하는 시간이 있는지 확인합니다."),
        ("과제의 완료 기준", "문제 수만 정하는지, 단어 재확인·본문 재독·오답 수정까지 완료 기준이 나뉘는지 살펴봅니다."),
        ("피드백 기록", "수업에서 발견한 오류가 다음 과제와 복습 날짜에 어떻게 반영되는지 확인합니다."),
        ("시험 기간 조정", "평소 루틴이 시험 범위 발표 후 교과서·프린트·서술형 중심으로 어떻게 바뀌는지 질문합니다."),
        ("수업 외 복습", "주중 실제 가능한 시간에 맞춰 단어와 본문을 다시 볼 분량이 조정되는지 확인합니다."),
        ("질문 처리 방식", "막힌 문장을 표시하고 질문한 뒤 비슷한 문장을 혼자 해결하는 단계까지 이어지는지 봅니다."),
    ]
    consultation_points.sort(key=lambda item: base.seed_for(CATEGORY, local, "consult", item[0]))
    consult_html = "".join(
        f"<article class=\"article-subject-card\"><h3>{esc(title)}</h3><p>{esc(body)} {esc(contextual_note(row, profile, 'consult-' + title))}</p></article>"
        for title, body in consultation_points[:4]
    )

    availability = (
        f"공개된 {center} 영어 가능 학년에 중2가 포함되어 있습니다. 다만 실제 반 편성과 시작일은 상담 시 다시 확인해야 합니다."
        if available
        else f"공개된 {center} 자료에는 영어 가능 학년이 비어 있습니다. 중2 영어 개설 여부를 임의로 단정하지 않고 상담에서 확인해야 합니다."
    )
    closing = choose(
        local,
        "closing",
        [
            f"{local} 중2 영어학원을 비교할 때는 한 번의 점수보다 학생이 틀린 문장을 스스로 고치고 며칠 뒤 다시 설명할 수 있는지를 확인하세요. {availability}",
            f"중2 영어 학습 계획은 교과서 진도와 학생의 실제 복습 시간을 함께 놓고 조정해야 합니다. {profile['check']}를 상담 질문으로 준비하면 수업 방식을 더 구체적으로 비교할 수 있습니다. {availability}",
            f"{region} {district} {local}에서 영어 수업을 살필 때는 문법·독해·어휘·서술형이 하나의 기록으로 이어지는지 확인하는 것이 중요합니다. {availability}",
            f"문제량보다 중요한 것은 학습 기록이 다음 수업과 시험 전 복습에 반영되는 과정입니다. {profile['rhythm']}의 흐름이 학생 일정에 맞는지 상담에서 확인해 보세요. {availability}",
        ],
    )

    return f'''<section class="shell academy-section article-main manuscript-panel">
      <section class="article-hero">
        <p class="article-eyebrow">LOCAL ENGLISH STUDY GUIDE</p>
        <h2>{esc(region)} {esc(district)} {esc(local)} 중2 영어 학습 설계</h2>
        <p class="article-intro">{esc(intro)} {esc(contextual_note(row, profile, 'opening'))}</p>
      </section>
      <section class="article-section article-local-feature-section">
        <h2>{esc(local)} 중2 영어에서 함께 관리할 네 영역</h2>
        <div class="article-card-grid">{domain_cards}</div>
      </section>
      <section class="article-section article-local-feature-section">
        <h2>{esc(school_heading)}</h2>
        <p>{esc(school_intro)}</p>
        <div class="article-target-list">{school_card_html}</div>
      </section>
      <section class="article-section article-local-feature-section">
        <h2>{esc(profile['source_focus'])}을 중심으로 구성한 주간 수업 흐름</h2>
        <div class="article-target-list">{process_html}</div>
      </section>
      <section class="article-section article-local-feature-section">
        <h2>{esc(local)} 영어 상담에서 확인할 운영 기준</h2>
        <div class="article-subject-grid">{consult_html}</div>
      </section>
      <section class="article-closing"><p>{esc(closing)}</p></section>
    </section>'''


def representative_for(row: dict[str, str], fallbacks: list[str]) -> str:
    parent = base.find_parent_page(row)
    candidates: list[Path] = []
    if parent:
        candidates.extend(
            [
                parent.parent / "중1영어학원" / "index.html",
                parent.parent / "초6영어학원" / "index.html",
                parent,
            ]
        )
    for candidate in candidates:
        if not candidate.exists():
            continue
        source = candidate.read_text(encoding="utf-8")
        match = re.search(r'data-role="representative-image"[^>]*src="([^"]+)"', source, re.I)
        if match:
            return html.unescape(match.group(1))
    local = row_value(row, "근처 수업가능 동네")
    return fallbacks[base.seed_for(CATEGORY, local, "representative") % len(fallbacks)]


def body_image_for(row: dict[str, str]) -> str:
    for candidate in existing_english_pages(row):
        source = candidate.read_text(encoding="utf-8")
        match = re.search(r"assets/centers/common/([^\"?#]+)", source, re.I)
        if match and (SITE / "assets" / "centers" / "common" / match.group(1)).exists():
            return match.group(1)
    return "seoul.jpg" if row_value(row, "지역") == "서울" else "local.jpg"


def build_faqs(row: dict[str, str], profile: dict[str, str]) -> list[tuple[str, str]]:
    local = row_value(row, "근처 수업가능 동네")
    title = f"{local} 중2 영어학원"
    center = row_value(row, "센터명") or f"{local} 학습센터"
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    grades = split_items(row_value(row, "가능학년\n(영어)"))
    school_answer = (
        f"공개 센터 자료에는 {', '.join(schools)} 등이 수업 가능 학교로 기재되어 있습니다. 실제 교과서, 시험 범위와 일정은 상담할 때 현재 학교 자료로 다시 확인해야 합니다."
        if schools
        else "공개 센터 자료에는 중학교명이 별도로 기재되어 있지 않습니다. 학교명을 임의로 만들지 않고 상담 시 현재 교과서, 시험 범위와 학교 자료를 확인합니다."
    )
    availability_answer = (
        f"공개된 {center} 가능 학년 정보에 중2 영어가 포함되어 있습니다. 실제 시간표, 반 편성과 시작 가능일은 변동될 수 있어 상담 시 다시 확인해야 합니다."
        if "중2" in grades
        else f"공개된 {center} 자료에는 영어 가능 학년이 기재되어 있지 않습니다. 중2 영어 개설 여부와 수업 일정은 상담을 통해 확인해야 합니다."
    )
    bank = [
        (f"{title} 상담 전에 어떤 자료를 준비하면 좋나요?", f"최근 영어 시험지, 교과서와 학교 프린트, 현재 단어장과 틀린 서술형 답안을 준비하면 좋습니다. 특히 {profile['check']}를 메모하면 상담 기준이 구체적해집니다."),
        (f"{local} 중2 영어학원은 어떤 학생에게 맞는지 어떻게 판단하나요?", f"{profile['student']}이라면 설명 뒤 스스로 해석하고 고치는 과정이 있는지 확인하세요. {profile['priority']}"),
        ("중2 영어 내신은 무엇부터 준비해야 하나요?", f"어휘·문법·독해·서술형 중 최근 답안에서 가장 흔들린 영역을 먼저 구분해야 합니다. 이후 {profile['rhythm']}의 흐름으로 학교 자료에 연결합니다."),
        ("교과서 본문을 외우는 것만으로 충분한가요?", "본문을 익히는 것은 필요하지만 문장 구조, 핵심 표현, 문단 흐름과 변형 질문의 근거까지 설명할 수 있어야 합니다. 암기한 문장을 새로운 조건에 맞게 바꾸는 연습도 확인하세요."),
        ("문법과 독해는 따로 공부해야 하나요?", "개념을 처음 정리할 때는 나눌 수 있지만 실제 내신에서는 문법이 교과서 문장과 독해 선택지에 함께 적용됩니다. 배운 구조를 지문에서 찾고 해석에 반영하는 과정이 필요합니다."),
        ("학교별 영어 내신 자료도 확인할 수 있나요?", school_answer),
        ("중2 영어 수강 가능 여부는 어디에서 확인하나요?", availability_answer),
        ("서술형 오답은 어떻게 관리해야 하나요?", "철자만 다시 쓰기보다 내용 누락, 어순, 동사 형태와 문법 조건을 나눠 수정 이유를 남겨야 합니다. 며칠 뒤 해설 없이 같은 의미의 문장을 다시 작성하는지도 확인하세요."),
        ("영어 단어는 얼마나 자주 복습해야 하나요?", "한 번에 많은 양을 외우는 기준보다 수업 당일, 주중과 시험 전처럼 간격을 두고 다시 재현할 날짜를 정하는 것이 중요합니다. 문장 속 품사와 쓰임까지 함께 확인하세요."),
        ("중1 문법이 부족해도 중2 진도를 따라갈 수 있나요?", "현재 중2 문장을 이해하는 데 필요한 중1 개념을 찾아 짧게 복원한 뒤 바로 교과서 문장에 적용하는 방식으로 계획할 수 있습니다. 실제 보완 범위는 진단 결과로 정합니다."),
        ("상담할 때 시간표와 교습비도 확인해야 하나요?", "네. 공개 교습비 자료와 함께 주당 횟수, 시작·종료 시각, 결석·보강 기준, 시험 기간 일정 변동을 같은 표에 적어 비교하는 것이 좋습니다."),
    ]
    order = sorted(bank, key=lambda item: base.seed_for(CATEGORY, local, "faq", item[0]))
    selected = order[:5]
    for required in (bank[0], bank[1]):
        if required not in selected:
            selected[-1] = required
    return selected


def build_parent_notes(row: dict[str, str], profile: dict[str, str]) -> list[str]:
    local = row_value(row, "근처 수업가능 동네")
    center = row_value(row, "센터명") or f"{local} 학습센터"
    notes = [
        f"{local} 영어 상담에서는 단어 수나 문제량보다 아이가 지문에서 답의 근거를 찾고 설명할 수 있는지를 물어보는 편이 비교에 도움이 됩니다.",
        f"{profile['student']}에게는 진도를 서두르기보다 {profile['rhythm']}의 복습 흐름이 실제 일정에 맞는지 확인하는 것이 중요합니다.",
        f"{center} 공개 정보를 볼 때 학교 자료, 영어 가능 학년과 교습비 링크를 함께 확인하면 상담 질문을 빠뜨리지 않고 정리할 수 있습니다.",
        f"{local} 중2 영어학원을 비교할 때 교과서 본문뿐 아니라 서술형 답안을 고친 이유까지 기록하는지 질문해 볼 필요가 있습니다.",
        f"최근 시험지를 어휘·문법·독해·쓰기 영역으로 나눠 보니 같은 점수라도 필요한 학습 순서가 다를 수 있다는 점을 확인할 수 있습니다.",
        f"시험 범위가 나오기 전에는 누적 어휘와 문장 구조를, 범위가 나온 뒤에는 학교 자료와 변형 문제를 중심으로 계획이 바뀌는지 살펴보는 것이 좋습니다.",
        f"수업에서 맞힌 문장도 며칠 뒤 해설 없이 다시 해석하고 쓸 수 있는지 확인하는 기준이 {local} 영어 수업 비교에 유용합니다.",
        f"통학 거리뿐 아니라 종료 시각, 보강 기준과 시험 기간 시간표를 함께 확인해야 실제 주간 복습 시간을 계산할 수 있습니다.",
        f"{profile['check']}를 아이와 먼저 이야기한 뒤 상담하면 추상적인 설명보다 현재 필요한 도움을 구체적으로 확인하기 쉽습니다.",
        f"학교 프린트와 교과서의 우선순위를 정하고 완료 여부를 기록하는 방식인지 살펴보면 시험 직전의 학습 부담을 예상할 수 있습니다.",
    ]
    notes.sort(key=lambda value: base.seed_for(CATEGORY, local, "parent", value))
    return notes[:3]


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
    title = f"{local} 중2 영어학원"
    center = row_value(row, "센터명") or f"{local} 학습센터"
    address = row_value(row, "센터 주소")
    registration = row_value(row, "교육지원청 등록번호")
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    grades = split_items(row_value(row, "가능학년\n(영어)"))
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
        "knowsAbout": ["중2 영어", "중학교 영어 내신", "교과서 독해", "문법 적용", "어휘 누적", "서술형"],
        "contactPoint": {"@type": "ContactPoint", "telephone": f"+82-{PHONE_DISPLAY[1:]}", "contactType": "교육 상담", "availableLanguage": "Korean", "url": FORM_URL},
        "makesOffer": [{"@type": "Offer", "name": f"{title} 학습 상담", "category": "중2 영어 학습 진단", "url": tuition_url or page_url, "itemOffered": {"@id": f"{page_url}#service"}}],
        "mentions": [{"@type": "School", "name": school} for school in schools],
    }
    if registration:
        organization["identifier"] = registration
    graph = [
        {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "url": f"{DOMAIN}/", "name": SITE_NAME, "inLanguage": "ko-KR"},
        organization,
        {
            "@type": "WebPage", "@id": f"{page_url}#webpage", "url": page_url, "name": title, "description": description, "inLanguage": "ko-KR",
            "isPartOf": {"@id": f"{DOMAIN}/#website"}, "breadcrumb": {"@id": f"{page_url}#breadcrumb"}, "mainEntity": {"@id": f"{page_url}#service"},
            "primaryImageOfPage": {"@id": f"{page_url}#primaryimage"},
            "about": [{"@type": "Place", "name": f"{region} {district} {local}"}, {"@type": "Thing", "name": CATEGORY_LABEL}, {"@type": "Thing", "name": "중학교 2학년 영어 내신"}],
            "mentions": [{"@type": "EducationalOrganization", "name": center}, *[{"@type": "School", "name": school} for school in schools]],
            "hasPart": [{"@type": "WebPageElement", "name": name} for name in ["핵심 답변", "중2 영어 학습 설계", "센터 정보", "상담 전 체크리스트", "FAQ", "학부모 상담 관점", "내부링크"]],
        },
        {"@type": "ImageObject", "@id": f"{page_url}#primaryimage", "url": rep_image, "caption": f"{title} {SITE_NAME} 대표"},
        {
            "@type": "BreadcrumbList", "@id": f"{page_url}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{DOMAIN}/"},
                {"@type": "ListItem", "position": 2, "name": PARENT, "item": canonical(PARENT)},
                {"@type": "ListItem", "position": 3, "name": CATEGORY_LABEL, "item": canonical(PARENT, CATEGORY)},
                {"@type": "ListItem", "position": 4, "name": title, "item": page_url},
            ],
        },
        {"@type": "Service", "@id": f"{page_url}#service", "name": f"{title} 학습 상담 및 안내", "serviceType": "중학교 2학년 영어 학습관리", "provider": {"@id": f"{page_url}#organization"}, "areaServed": {"@type": "Place", "name": f"{region} {district} {local}"}, "audience": {"@type": "EducationalAudience", "educationalRole": "중학교 2학년 학생 및 학부모"}, "about": ["중2 영어", "내신 대비", "교과서 독해", "문법", "어휘", "서술형"]},
        {
            "@type": "Article", "@id": f"{page_url}#article", "url": page_url, "headline": title, "description": description,
            "datePublished": PUBLISH_DATE, "dateModified": PUBLISH_DATE, "inLanguage": "ko-KR", "mainEntityOfPage": {"@id": f"{page_url}#webpage"},
            "author": {"@id": f"{page_url}#organization"}, "publisher": {"@id": f"{page_url}#organization"}, "image": [rep_image, body_image, map_image],
            "articleSection": [region, district, local, "중2 영어", "교과서", "문법", "독해", "어휘", "서술형"],
            "about": [{"@type": "Thing", "name": title}], "mentions": [{"@type": "EducationalOrganization", "name": center}],
        },
        {"@type": "FAQPage", "@id": f"{page_url}#faq", "mainEntity": [{"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}} for question, answer in faqs]},
        {"@type": "ItemList", "@id": f"{page_url}#related-pages", "name": f"{local} 관련 학습 페이지", "itemListElement": [{"@type": "ListItem", "position": index, "name": name, "url": url} for index, (name, url) in enumerate(related, 1)]},
    ]
    return {"@context": "https://schema.org", "@graph": graph}


def detail_html(
    row: dict[str, str],
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
    grades = split_items(row_value(row, "가능학년\n(영어)"))
    schools = split_items(row_value(row, "타깃학교\n(중)"))
    available = "중2" in grades
    title = f"{local} 중2 영어학원"
    profile = page_profile(row)
    description = f"{region} {district} {local} 중2 영어학원 선택을 위해 {center} 공개 정보와 교과서·문법·독해·어휘·서술형 학습 및 상담 기준을 정리했습니다."
    page_url = canonical(PARENT, CATEGORY, local)
    body_name = body_image_for(row)
    body_url = f"{DOMAIN}/assets/centers/common/{body_name}"
    map_url = f"{DOMAIN}/assets/maps/{quote(map_name)}"
    parent_link = base.parent_relative_url(row)
    middle1_link = base.parent_relative_url(row, "중1영어학원")
    elementary6_link = base.parent_relative_url(row, "초6영어학원")
    district_rows = [candidate for candidate in rows if row_value(candidate, "지역") == region and row_value(candidate, "시or구") == district]
    if len(district_rows) > 1:
        sibling_index = next(position for position, candidate in enumerate(district_rows) if row_value(candidate, "근처 수업가능 동네") == local)
        previous_local = row_value(district_rows[sibling_index - 1], "근처 수업가능 동네")
        next_local = row_value(district_rows[(sibling_index + 1) % len(district_rows)], "근처 수업가능 동네")
    else:
        previous_local = row_value(rows[index - 1], "근처 수업가능 동네") if index else row_value(rows[-1], "근처 수업가능 동네")
        next_local = row_value(rows[(index + 1) % len(rows)], "근처 수업가능 동네")
    neighbor_locals = list(dict.fromkeys([previous_local, next_local]))
    related = [
        (CATEGORY_LABEL, canonical(PARENT, CATEGORY)),
        (f"{local} 중2 수학학원", canonical(PARENT, "중2수학학원", local)),
        (f"{local}학원", base.parent_canonical_url(row)),
        (f"{local} 중1 영어학원", base.parent_canonical_url(row, "중1영어학원")),
        (f"{local} 초6 영어학원", base.parent_canonical_url(row, "초6영어학원")),
    ]
    related.extend((f"{neighbor} 중2 영어학원", canonical(PARENT, CATEGORY, neighbor)) for neighbor in neighbor_locals)
    faqs = build_faqs(row, profile)
    notes = build_parent_notes(row, profile)
    schema = page_json_ld(row, description, page_url, rep_image, body_url, map_url, faqs, related)
    school_html = "".join(f"<span>{esc(school)}</span>" for school in schools) if schools else '<p class="subject-empty-note">공개 자료에 중학교명이 별도로 기재되어 있지 않아 상담 시 현재 학교와 시험 범위를 확인합니다.</p>'
    grade_html = "".join(f"<span>{esc(grade)}</span>" for grade in grades) if grades else "<span>상담 확인</span>"
    availability_text = (
        f"공개 센터 자료의 영어 가능 학년에 중2가 포함되어 있습니다. 실제 반 편성과 일정은 {center} 상담에서 확인해야 합니다."
        if available
        else f"공개된 {center} 자료에는 영어 가능 학년이 비어 있어 중2 영어 개설 여부를 상담에서 확인해야 합니다."
    )
    faq_html = "".join(f"<details><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>" for question, answer in faqs)
    notes_html = "".join(f'<article class="subject-parent-note"><p>{esc(note)}</p></article>' for note in notes)
    neighbor_links_html = "".join(
        f'<a class="child-page-button" href="../{quote(neighbor, safe="")}/index.html">{esc(neighbor)} 중2 영어학원</a>'
        for neighbor in neighbor_locals
    )
    tuition_html = f'<a class="btn ghost" href="{esc(tuition)}" target="_blank" rel="noopener noreferrer">센터 교습비 자료 확인</a>' if tuition else '<span class="subject-empty-note">교습비 자료는 상담 시 확인해 주세요.</span>'
    manuscript = build_manuscript(row, profile)

    return f'''{base.head_html(title, description, page_url, rep_image, schema, "../../../")}
<body>
{base.nav_html("../../../", "subject")}
  <main id="main">
    <nav class="breadcrumb-box" aria-label="현재 위치"><a href="../../../index.html">홈</a><span>›</span><a href="../../index.html">과목별학원</a><span>›</span><a href="../index.html">중2 영어학원</a><span>›</span>{esc(title)}</nav>
    <section class="sub-hero shell directory-hero subject-detail-hero">
      <div class="reveal"><p class="eyebrow">MIDDLE SCHOOL ENGLISH GUIDE</p><h1>{esc(title)}</h1><p>{esc(description)}</p><div class="hero-actions"><a class="btn primary" href="{FORM_URL}" target="_blank" rel="noopener noreferrer">상담 준비하기</a><a class="btn ghost" href="../index.html">다른 지역 찾기</a></div></div>
      <div class="stat-console reveal"><div class="stat-pill"><strong>{esc(local)}</strong><span>{esc(region)} {esc(district)}</span></div><div class="stat-pill"><strong>{'확인' if not available else '중2'}</strong><span>{'개설 여부 상담 필요' if not available else '영어 가능 학년 기재'}</span></div></div>
    </section>
    <section class="shell csv-body-stack csv-top-media local-media-section subject-media" aria-label="{esc(title)} 이미지 안내">
      <img data-role="representative-image" style="display:none;" src="{esc(rep_image)}" alt="{esc(title)} {SITE_NAME} 대표">
      <figure class="csv-media-card"><img src="../../../assets/centers/common/{body_name}" alt="{esc(title)} 본문 {SITE_NAME}" loading="eager" decoding="async"></figure>
      <figure class="csv-media-card"><img src="../../../assets/maps/{quote(map_name)}" alt="{esc(title)} 지도 {SITE_NAME}" loading="lazy" decoding="async"></figure>
    </section>
    <section class="shell geo-summary-panel subject-answer-panel reveal" aria-labelledby="answer-title">
      <p class="eyebrow">핵심 답변</p><h2 id="answer-title">{esc(title)}, 무엇부터 확인해야 할까요?</h2>
      <p>{esc(local)}에서 중2 영어학원을 비교할 때는 교과서 진도만 보지 말고 어휘 재현, 문법 적용, 독해 근거, 서술형 수정과 시험 전 복습 기록을 함께 살펴야 합니다. {esc(profile['student'])}이라면 특히 {esc(profile['source_focus'])}이 다른 영역으로 어떻게 연결되는지 확인하는 것이 좋습니다.</p>
      <div class="geo-fact-grid"><article class="geo-fact-card"><span>현재 학생 상황</span><strong>{esc(profile['student'])}</strong></article><article class="geo-fact-card"><span>우선 확인</span><strong>{esc(profile['priority'])}</strong></article><article class="geo-fact-card"><span>상담 질문</span><strong>{esc(profile['check'])}</strong></article></div>
    </section>
    {manuscript}
    <section class="shell academy-section subject-local-facts reveal" aria-labelledby="local-facts-title">
      <div class="section-heading"><p class="eyebrow">VERIFIED LOCAL FACTS</p><h2 id="local-facts-title">{esc(local)} 센터 정보와 수업 확인 항목</h2><p>기존 전국학원 페이지와 공개 센터 자료에 있는 사실만 사용했으며, 기재되지 않은 학교나 운영 조건은 임의로 만들지 않았습니다.</p></div>
      <div class="subject-fact-grid"><article><span>센터</span><strong>{esc(center)}</strong><p>{esc(address) if address else '주소는 상담 시 확인해 주세요.'}</p></article><article><span>중2 영어 가능 학년</span><strong>{'자료에 기재됨' if available else '상담 확인 필요'}</strong><p>{esc(availability_text)}</p></article><article><span>교육지원청 등록 정보</span><strong>{esc(registration_name) if registration_name else '상담 확인'}</strong><p>{esc(registration_number) if registration_number else '공개 자료에 등록번호가 별도로 기재되어 있지 않습니다.'}</p></article></div>
      <div class="subject-school-panel"><h3>공개 자료의 중학교 안내</h3><div class="subject-school-tags">{school_html}</div></div>
      <div class="subject-grade-panel"><h3>공개 자료의 영어 가능 학년</h3><div class="subject-school-tags">{grade_html}</div>{tuition_html}</div>
    </section>
    <section class="shell geo-checklist-panel reveal" aria-labelledby="checklist-title">
      <p class="eyebrow">상담 전 체크리스트</p><h2 id="checklist-title">{esc(title)} 비교 전에 적어둘 내용</h2>
      <div class="geo-checklist-grid"><article class="geo-check-card"><b>01</b><strong>학교 자료</strong><p>최근 시험지, 교과서, 학교 프린트와 수행평가 일정을 준비합니다.</p></article><article class="geo-check-card"><b>02</b><strong>영역별 오류</strong><p>{esc(profile['check'])}를 확인합니다.</p></article><article class="geo-check-card"><b>03</b><strong>복습 간격</strong><p>{esc(profile['rhythm'])}이 실제 주간 일정에 가능한지 계산합니다.</p></article><article class="geo-check-card"><b>04</b><strong>운영 조건</strong><p>반 편성, 시간표, 결석·보강 기준과 교습비를 확인합니다.</p></article></div>
    </section>
    <section class="shell academy-section local-proof-section" aria-labelledby="faq-title">
      <div class="section-heading"><p class="eyebrow">FAQ & PARENT VIEW</p><h2 id="faq-title">{esc(title)} 자주 묻는 질문과 학부모 상담 관점</h2><p>화면 질문과 답변은 JSON-LD에도 동일하게 반영했습니다. 상담 관점은 특정 성과를 보장하는 후기가 아니라 비교에 참고할 수 있도록 재구성한 예시입니다.</p></div>
      <div class="local-proof-layout"><section class="local-faq-card" aria-label="{esc(title)} 자주 묻는 질문"><div class="faq-list">{faq_html}</div></section><aside class="local-review-card" aria-label="{esc(title)} 학부모 상담 관점"><div class="review-list">{notes_html}</div></aside></div>
    </section>
    <section class="shell local-page-nav reveal" aria-labelledby="related-title">
      <div class="section-heading"><p class="eyebrow">RELATED GUIDES</p><h2 id="related-title">{esc(local)} 및 인접 학습 페이지</h2><p>중2 과목 안내와 기존 전국학원 영어 페이지를 함께 비교할 수 있습니다.</p></div>
      <div class="child-button-grid"><a class="child-page-button" href="../index.html">중2 영어학원 지역 목록</a><a class="child-page-button" href="../../중2수학학원/{quote(local, safe='')}/index.html">{esc(local)} 중2 수학학원</a><a class="child-page-button" href="{parent_link}">{esc(local)}학원</a><a class="child-page-button" href="{middle1_link}">{esc(local)} 중1 영어학원</a><a class="child-page-button" href="{elementary6_link}">{esc(local)} 초6 영어학원</a>{neighbor_links_html}</div>
    </section>
  </main>
{base.footer_html("../../../")}
</body>
</html>
'''


def hub_page(rows: list[dict[str, str]]) -> str:
    title = "중2 영어학원 지역별 안내"
    description = "371개 지역의 중2 영어학원 선택 기준과 공개 센터 정보, 교과서·문법·독해·어휘·서술형 상담 항목을 지역별로 정리했습니다."
    url = canonical(PARENT, CATEGORY)
    items = [(f"{row_value(row, '근처 수업가능 동네')} 중2 영어학원", canonical(PARENT, CATEGORY, row_value(row, "근처 수업가능 동네"))) for row in rows]
    faqs = [
        ("지역별 중2 영어학원 페이지는 어떤 자료를 참고했나요?", "전문수업.com 전국학원 아래의 각 동네·중1 영어·초6 영어 페이지 구성과 센터정보 정리 자료의 실제 기재 내용을 참고했습니다. 기존 문장은 복사하지 않고 중2 학습 기준으로 새로 작성했습니다."),
        ("영어 가능 학년이 비어 있는 지역도 있나요?", "네. 공개 자료에 영어 가능 학년이 없는 지역은 개설을 임의로 단정하지 않고 상담 확인 필요로 표시했습니다."),
        ("동네나 센터 이름으로 바로 찾을 수 있나요?", "검색창에 동네명, 시군구, 센터명 또는 공개된 중학교명을 입력하면 해당 지역 카드만 확인할 수 있습니다."),
    ]
    schema = base.collection_schema(title, description, url, [("홈", f"{DOMAIN}/"), (PARENT, canonical(PARENT)), (CATEGORY_LABEL, url)], items, faqs)
    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row_value(row, "지역")][row_value(row, "시or구")].append(row)
    region_sections = []
    for region_index, (region, districts) in enumerate(grouped.items()):
        count = sum(len(values) for values in districts.values())
        district_sections = []
        for district, district_rows in districts.items():
            cards = []
            for row in district_rows:
                local = row_value(row, "근처 수업가능 동네")
                center = row_value(row, "센터명")
                schools = row_value(row, "타깃학교\n(중)")
                search = " ".join([region, district, local, center, schools])
                cards.append(f'<a class="subject-town-card" data-subject-town data-search="{esc(search)}" href="{quote(local, safe="")}/index.html"><strong>{esc(local)}</strong><span>{esc(district)} · 중2 영어</span></a>')
            district_sections.append(f'<section class="subject-district-group" data-subject-district><h3>{esc(district)} <small>{len(district_rows)}개 지역</small></h3><div class="subject-town-grid">{"".join(cards)}</div></section>')
        region_sections.append(f'<details class="subject-region-group" data-subject-region{" open" if region_index == 0 else ""}><summary><span>{esc(region)}</span><b>{count}개 지역</b></summary><div class="subject-region-body">{"".join(district_sections)}</div></details>')
    faq_html = "".join(f"<details><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>" for question, answer in faqs)
    schema_text = base.head_html(title, description, url, f"{DOMAIN}/assets/generated/academy-hero-v2.webp", schema, "../../", "website")
    return f'''{schema_text}
<body>
{base.nav_html("../../", "subject")}
  <main id="main">
    <nav class="breadcrumb-box" aria-label="현재 위치"><a href="../../index.html">홈</a><span>›</span><a href="../index.html">과목별학원</a><span>›</span>중2 영어학원</nav>
    <section class="sub-hero shell directory-hero"><div class="reveal"><p class="eyebrow">MIDDLE SCHOOL ENGLISH DIRECTORY</p><h1>중2 영어학원</h1><p>{esc(description)}</p></div><div class="stat-console reveal"><div class="stat-pill"><strong>371</strong><span>동네별 학습 안내</span></div><div class="stat-pill"><strong>13</strong><span>광역 지역 구분</span></div></div></section>
    <section class="shell academy-section subject-directory" data-subject-directory>
      <div class="section-heading"><p class="eyebrow">LOCAL SEARCH</p><h2>동네 이름으로 중2 영어학원 찾기</h2><p>광역·시군구별로 접어 정리했습니다. 동네명, 센터명이나 공개 학교명을 검색하면 해당 결과만 남습니다.</p></div>
      <div class="subject-search-box"><label for="subject-town-search">동네·시군구·센터·학교 검색</label><input id="subject-town-search" type="search" placeholder="예: 명일동, 강동구, 명일점" autocomplete="off" data-subject-search><p aria-live="polite" data-subject-search-status>전체 371개 지역</p></div>
      <div class="subject-region-list">{"".join(region_sections)}</div>
    </section>
    <section class="shell academy-section subject-hub-faq"><div class="section-heading"><p class="eyebrow">DIRECTORY FAQ</p><h2>지역 페이지 이용 전에 확인하세요</h2></div><div class="faq-list">{faq_html}</div></section>
  </main>
{base.footer_html("../../")}
</body>
</html>
'''


def main() -> None:
    rows = base.read_csv(base.CENTER_CSV)
    image_rows = base.load_image_rows()
    fallbacks = base.representative_urls()
    if len(rows) != 371:
        raise ValueError(f"센터 자료는 371행이어야 합니다: {len(rows)}")
    if any(len(existing_english_pages(row)) < 2 for row in rows):
        raise ValueError("기존 전국학원 영어 참고 페이지가 누락된 지역이 있습니다.")
    output = SITE / PARENT / CATEGORY
    output.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(rows):
        local = row_value(row, "근처 수업가능 동네")
        image_row = image_rows.get(local, {})
        representative = representative_for(row, fallbacks)
        map_name = base.map_filename(row, image_row)
        target = output / local
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(detail_html(row, image_row, representative, map_name, index, rows), encoding="utf-8")
    (output / "index.html").write_text(hub_page(rows), encoding="utf-8")
    (SITE / PARENT / "index.html").write_text(base.category_page(), encoding="utf-8")
    sitemap_urls = [(canonical(PARENT, CATEGORY), "weekly", "0.9")]
    sitemap_urls.extend((canonical(PARENT, CATEGORY, row_value(row, "근처 수업가능 동네")), "monthly", "0.8") for row in rows)
    base.update_sitemap(sitemap_urls)
    print(f"reference_mode=existing_nationwide_english_pages")
    print(f"source_pages_read={len(rows) * 2}")
    print(f"generated_details={len(rows)}")
    print(f"generated_total={len(rows) + 1}")
    print(f"target={output}")


if __name__ == "__main__":
    main()
