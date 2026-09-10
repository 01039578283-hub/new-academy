# 와와센터 새 홈페이지 작업 현황

- 생성일: 2026-06-26
- 작업 폴더: `C:\Users\얼짱김종범\Desktop\홈페이지 정리\새 홈페이지5`
- 사이트명: `와와센터`
- 현재 메뉴: 홈, 학습가이드, 상담문의
- 전국센터 메뉴/페이지는 추후 생성 예정
- 디자인 방향: 모바일 우선, 신세대 감성, 고급스럽고 깔끔한 학습코칭 사이트
- 생성 이미지: `assets/generated/wawa-center-hero.png`
- 이미지 생성 방식: built-in imagegen
- 메인 이미지 프롬프트 요약: 한국 학습코칭 센터의 젊은 여자 선생님, 고급스럽고 따뜻한 상담 공간, 왼쪽 여백이 있는 랜딩페이지 히어로용 사진
- 포함 JSON-LD:
  - 홈: WebSite, EducationalOrganization, WebPage, BreadcrumbList, FAQPage
  - 학습가이드: WebPage, BreadcrumbList, Article
  - 상담문의: ContactPage, BreadcrumbList, EducationalOrganization
- 상담 링크:
  - 전화: `010-3957-8283`
  - 문자: `https://blogsms.net/01039578283`
  - 상담신청: Google Form 기존 링크 사용

## 다음 작업 후보

- 전국센터 메뉴 추가
- 지역/동네 페이지 생성
- 도메인 확정 후 sitemap.xml 생성
- 네이버 웹마스터도구 인증 코드 적용
- GitHub/Vercel 배포 연결

## 2026-09-10 전문수업.com 허브 보강

- 위 2026-06-26 항목은 초기 기록이며, 현재 사이트는 전문수업.com / 와와센터입니다.
- 실제 폴더: C:\Users\1992k\Desktop\홈페이지 정리\새 홈페이지5
- 기존 GitHub 01039578283-hub/new-academy, main 및 Vercel new-academy 프로젝트를 그대로 사용합니다.
- 보강 대상: 전국학원, 과목별학원, 고1·고2·중2·중3 영어/수학 분류 등 10개 허브.
- 학년·과목별 30절/60문단, 새 FAQ 40개, 학습가이드 링크 20개를 추가했습니다.
- 과목 메인의 제작자용 표현 3개와 각 분류의 FAQ 2문항씩을 고객용 안내로 정리했습니다.
- 전국학원의 기존 구조화 데이터 FAQ 3개도 본문에 표시하여 전체 67문항의 표시 내용과 JSON-LD를 일치시켰습니다.
- 명일·송촌·수완 센터의 기존 확인 가능한 이름/주소/등록번호만 안내 카드에 사용했습니다. 세 센터는 허브 전체에서 같은 EducationalOrganization ID를 사용합니다.
- 학습 공간 사진 2종은 공통 예시임을 명시했습니다. 원본 비율을 유지하며 지연 로딩하고 허브별 alt를 적용했습니다. 특정 지점 시설·운영시간·성과를 새로 주장하지 않았습니다.
- 전국학원을 CollectionPage로 정리하고 13개 실제 지역 링크를 ItemList에 연결했습니다. hasPart/mentions와 본문 WebPageElement 관계도 보강했습니다.
- 기존 title/H1/canonical/og:url/메타 설명, 지역 목록·검색·공유 JS와 비대상 HTML 7,141개, 기존 이미지 383개는 보존했습니다.
- sitemap.xml은 7,151개 URL/순서를 유지하며 대상 10개 lastmod만 갱신했습니다. RSS는 원문 그대로입니다.
- 기존 어두운 디자인을 유지하며 안내 바로가기, 본문 16px, 모바일 1열 및 하단 상담 버튼 3열을 허브에만 적용했습니다.
- 독립 정적 검사: 보호 138 + 추가 내용 340 = 478/478 PASS.
- 브라우저: 실제 CSS 폭 320/390/1280px에서 10허브씩 30회 가로 넘침/새 글자 잘림 없음. 새 FAQ40+전국 기존3 열기/닫기, 8분류 검색/없는 검색/371개 복원/명일동 상세 이동 확인.
- 소스: tools/hub-content-20260910.json, tools/enrich_hubs_20260910.py, assets/hub-guide.css.
- 생성기는 이 배포의 원본 10허브 스냅샷을 입력으로 사용합니다. 이후 별도 편집이 생긴 페이지에 예전 스냅샷을 그대로 재실행하지 마세요. 기존 대량 생성 도구도 이번 작업에서 실행하지 않았습니다.
- 기준선/감사/브라우저/HTTP 결과: C:\Users\1992k\Desktop\CodexData\tmp\pro-class-hubs-2026-09-10
- 배포 절차: 검증한 파일만 main에 커밋/푸시 → 기존 Vercel production → 정식 도메인과 별칭의 실제 응답 비교. 최종 SHA/배포ID/공개 검증 결과는 해당 폴더 release-result.json과 바탕화면 홈페이지 작업 기록.txt에 기록합니다.
- 검색 순위나 노출 증가를 보장하지 않으며, 검색엔진 재수집 후 별도 관찰이 필요합니다.
