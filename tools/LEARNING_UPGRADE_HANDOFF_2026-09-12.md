# 전문수업.com 공식 학습 자료 활용 업그레이드

- 완료 기록: 2026-09-12 01:19 KST
- 상태: 로컬 검증 완료 후 2026-09-12 사용자 공개 배포 승인. 기존 main → GitHub → Vercel production으로 배포 진행.
- 작업 폴더: C:\Users\1992k\Desktop\홈페이지 정리\새 홈페이지5
- 정식 도메인: https://전문수업.com/ (https://xn--z92bu9jx8cwzc.com/)
- 기존 브랜드 표기 와와센터, 연락처 010-3957-8283, 문자·상담 양식 연결 유지.
- 기준 Git HEAD: cde2db79073bddb85cc1441d3de2a636a8b4c72d / main
- 기존 GitHub: https://github.com/01039578283-hub/new-academy.git
- 다른 홈페이지의 작업·배포에는 관여하지 않음.

## 개선 범위

총 27페이지: 기존 26개 수정 + 학습코칭 1개 신규.

- 메인: 학습 고민 → 학년·과목 → 4C·AI 요약 → 학습 공간 → 공식 영상 → 지역·상담으로 구성.
- 학습코칭 신규: 4C 진단·처방·지도·상담, 플랜·학습·생활 관리, AI 영어·수학·국어·독서, 결과를 읽는 질문.
- 학습가이드: 시험 준비·플래너·오답·학부모 상담 준비를 구체적인 기록 예시로 재구성. 기존 exam/planner/wrong/parents 앵커 보존.
- 상담문의: 준비 체크리스트와 센터에 확인할 조건 정리. 체크는 저장·전송하지 않으며, 기존 전화·문자·상담 양식 사용. 미확인 공통 운영시간 삭제.
- 전국학원·과목별학원·8개 학년/과목 허브: 기존 2026-09-10 보강 본문·센터 카드·FAQ·검색 목록 유지, 주제별 코칭 요약과 상세 본문 링크 20개 추가.
- 전국학원 13개 지역 허브: 센터 선택 기준·동네 바로가기·FAQ·코칭/상담 링크 26개 추가. 기존 예시 동네 링크 38개도 요약에서 연결.
- 주소 분류에 도로명과 넓은 지역이 함께 존재해 전국학원 및 메인의 '시군구' 표현만 '지역 묶음'으로 정리. 실제 주소·분류 URL은 변경하지 않음. 한국어 조사도 별도 교정.
- 전국센터는 이 사이트에서 기존 메뉴 이름 '전국학원'으로 유지함.

## 공식 자료와 이미지

- https://www.wawacenter.com/brand/wawacenter
- https://www.wawacenter.com/intro/coachingSystem
- https://www.wawacenter.com/intro/AISystem
- 이미지 9개 + 영상 썸네일 3개 = 12개, 합계 1,826,093바이트. assets/official-learning에 원본 그대로 저장.
- 세 공식 페이지의 실제 이미지 경로·영상 ID와 파일 SHA-256을 2026-09-12에 다시 확인. 결과는 tools/reports/learning-upgrade/official-source-check.json.
- 사진은 접거나 자르지 않고 전체 비율 유지. 영상은 무거운 자동 로딩 iframe 대신 썸네일 카드에서 공식 YouTube로 새 창 연결.
- 영상 ID: avpJfW7eIV0 / f_skFu40U04 / UIXUaBZdNXU. 첫 영상의 새 탭·실제 제목·공식 채널·플레이어 표시 확인.
- AI 대상: 영어/수학 초1~고3, 국어 중1~고3, 독서 초1~중2. 본사 프로그램 대상과 개별 센터 개설·비용·시간표를 구분.
- 센터별 시설·성과·교습비·개설 과목·운영시간은 새로 만들지 않음. 학습 기록과 상담 질문은 예시라고 구분.

## 모바일·검색 구조

- 기존 네이비 디자인 유지, 대상 페이지에만 assets/learning-upgrade.css 추가. 기존 assets/site.css 및 assets/site.js 수정 없음.
- 모바일 메뉴 3열×2행, 하단 문의 3열, 상단 수치 카드 2열, 본문·제목·카드·목차 여백 정리.
- 새 본문은 주로 16px, 모바일 첫 설명 17px, 안내 문구/영문 라벨은 보조 크기 사용. 주요 메뉴/버튼 44px 이상.
- H1 1개, title/description/OG 정합성, WebPage/Article/FAQPage/BreadcrumbList와 hasPart/mentions/articleSection/내부 링크 관계 정리.
- FAQ 전체 111개가 화면과 JSON-LD에서 정확히 일치. 구조화 데이터에만 있던 지역 FAQ는 실제 표시하는 답변과 동기화.
- 기존 canonical, og:url, 기존 og:image 존재 여부·값, 소유확인 태그 보존. 기존 허브 23개 title/H1 및 실제 센터 엔터티 이름·주소·등록번호 유지.
- 비대상 기존 HTML 7,125개와 기존 이미지 파일 보존. 기존 동네 원고는 이번 작업에서 수정하지 않음.
- 사이트맵: 기존 7,151 URL/순서를 보존하고 학습코칭 1개 추가 → 7,152개. 수정한 기존 26페이지에만 실제 수정일 반영.
- RSS: 기존 11개 항목/순서를 유지하고 학습코칭 추가 → 12개. 대상 항목 title/description/날짜 동기화.
- llms.txt에 학습 안내 경로와 프로그램 조건 설명 추가. 이것이 검색 순위나 AI 인용을 보장하는 것은 아님.
- .vercelignore에 tools/ 추가. 원고 입력·수집 원본·내부 검사 기록은 공개 배포에서 제외.

## 검증 결과

- 독립 정적·보존·로컬 HTTP 검사 1,067/1,067 통과.
- 내부 링크/앵커 4,035개 고유 목적지 확인. 로컬 HTTP 49개 모두 200이며 파일 내용 일치.
- 320/390/1280px × 27페이지 + 768px × 4개 주요 화면 = 85회. 최종 문구 교정 후 재검사, 가로 넘침·주요 버튼 크기 오류 없음.
- FAQ 111개 클릭 열기·Enter 닫기 통과.
- 8개 과목 허브에서 명일동 1건 → 없는 검색어 0건 → 키보드로 검색어 삭제 후 371개 복원 확인.
- 새 요약 링크 46개 실제 클릭 및 본문 도착 위치, 메뉴 6개, 과목별 동네 상세 8개, 지역별 동네 상세 13개, 코칭 앵커 8개 확인.
- 이미지 12개 실제 로드 및 원본 비율 확인. 상담 체크박스는 전송 없이 토글됨.
- 재생성 변경 0개, git diff --check 통과. 스테이징 없음, HEAD는 기준 커밋 유지.
- 브라우저 검사 중 외부 영상 탭 종료 후 미리보기 확대율이 바뀌는 도구 동작이 있어 새 탭에서 캡처. 실제 CSS 폭으로 측정했으며, 코드 문제로 판단하여 불필요하게 수정하지 않음.
- 보고서: tools/reports/learning-upgrade/generation.json, static-audit.json, browser-audit.json 및 화면 PNG 6개.

## 이어서 수정하는 방법

- 원고 입력: tools/data/learning-upgrade/{home,coaching,guide,contact}.html, content.json.
- 출처/원본 자산 명세: tools/data/learning-upgrade/sources.json.
- 생성기: tools/upgrade_learning_20260912.py. 기준 커밋과 직전 생성 SHA로 수동 수정 충돌을 검사한다. 기준 커밋을 임의로 바꾸거나 예전 대량 생성기로 덮어쓰지 말 것.
- 독립 감사: tools/audit_learning_upgrade.py --http.
- Python 의존성: C:\Users\1992k\Desktop\CodexData\tmp\wawa4-upgrade-deps의 BeautifulSoup. PowerShell에서 해당 경로를 PYTHONPATH로 지정 후 python -X utf8로 실행.
- 로컬 서버: 프로젝트 폴더에서 python -m http.server 8798 --bind 127.0.0.1.
- 로컬 확인: http://127.0.0.1:8798/ /학습코칭/ /전국학원/ /과목별학원/.
- 2026-09-12 공개 배포 승인 후 이 폴더만 재검증함. tools/verify_learning_release.py --commit <배포 커밋>으로 정식 도메인 응답을 커밋 내용과 비교하며, 배포 ID와 최종 결과는 별도 완료 기록에 남긴다.

## 수정 대상 URL

https://전문수업.com/
https://전문수업.com/학습코칭/
https://전문수업.com/학습가이드/
https://전문수업.com/상담문의/
https://전문수업.com/전국학원/
https://전문수업.com/과목별학원/
https://전문수업.com/과목별학원/고1영어학원/
https://전문수업.com/과목별학원/고1수학학원/
https://전문수업.com/과목별학원/고2영어학원/
https://전문수업.com/과목별학원/고2수학학원/
https://전문수업.com/과목별학원/중2영어학원/
https://전문수업.com/과목별학원/중2수학학원/
https://전문수업.com/과목별학원/중3영어학원/
https://전문수업.com/과목별학원/중3수학학원/
https://전문수업.com/전국학원/강원/
https://전문수업.com/전국학원/경기/
https://전문수업.com/전국학원/경상/
https://전문수업.com/전국학원/광주/
https://전문수업.com/전국학원/대구/
https://전문수업.com/전국학원/대전/
https://전문수업.com/전국학원/부산/
https://전문수업.com/전국학원/서울/
https://전문수업.com/전국학원/울산/
https://전문수업.com/전국학원/인천/
https://전문수업.com/전국학원/전라/
https://전문수업.com/전국학원/제주/
https://전문수업.com/전국학원/충청/
