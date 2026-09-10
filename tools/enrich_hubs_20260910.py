"""Scoped one-release static hub enhancement. Never run the legacy page generators.

Inputs: the original 10-hub snapshots ZIP and the reviewed, fact-bounded copy.
All original pages are preserved in that ZIP; regenerate only during this release.
"""
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
from html import escape
from html.parser import HTMLParser
import argparse
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://xn--z92bu9jx8cwzc.com'
DATE = '2026-09-10'
DATA = Path(__file__).with_name('hub-content-20260910.json')
LD = re.compile(r'(<script[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)', re.S)
CENTERS = [
    {'key':'myeongil','region':'서울 강동구','name':'와와학습코칭센터 명일점','address':'서울 강동구 양재대로 1606 3층','registration':'서울강동교육지원청 등록 제 7641호','href':'/전국학원/서울/강동구/명일동/'},
    {'key':'songchon','region':'대전 대덕구','name':'와와학습코칭센터 송촌점','address':'대전 대덕구 동춘당로94번길 11-7 4층 402','registration':'대전동부교육지원청등록 제 2동3248호','href':'/전국학원/대전/대덕구/송촌동/'},
    {'key':'suwan','region':'광주 광산구','name':'와와학습코칭센터 수완점','address':'광주 광산구 임방울대로 310 아이비타워 406','registration':'광주서부교육지원청 등록 제6778호','href':'/전국학원/광주/광산구/수완동/'}
]

class Regions(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); href = a.get('href','')
        if tag == 'a':
            route = unquote(urlparse(href).path).removesuffix('index.html').strip('/')
            bits = route.split('/')
            if len(bits) == 1 and bits[0] in ['강원','경기','경상','광주','대구','대전','부산','서울','울산','인천','전라','제주','충청'] and route not in self.links:
                self.links.append(route)

def question(q, a):
    return {'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}}

def details(q, a):
    return f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>'

def node_list(graph, kind):
    return next((n for n in graph if n.get('@type') == kind), None)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--snapshots', type=Path, required=True); ap.add_argument('--copy-dir', type=Path, required=True)
    args = ap.parse_args()
    content = {}
    for filename in ['high-copy.json','middle-copy.json']:
        part = json.loads((args.copy_dir / filename).read_text('utf-8-sig'))
        assert not (content.keys() & part.keys()); content.update(part)
    assert len(content) == 10
    DATA.write_text(json.dumps(content, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    policies = {}
    with zipfile.ZipFile(args.snapshots) as archive:
        for route, item in content.items():
            rel = route.strip('/') + '/index.html'
            source = archive.read(rel).decode('utf-8-sig').replace('\r\n','\n')
            assert 'studio-hub-content' not in source
            current = (ROOT / rel).read_text('utf-8-sig')
            assert current == source or 'studio-hub-content' in current, 'Unreviewed change: '+rel
            ld = LD.search(source); assert ld
            doc = json.loads(ld.group(2)); graph = doc['@graph']
            webpage = next(n for n in graph if n.get('@type') in ['WebPage','CollectionPage'])
            url = webpage['url']
            faq = node_list(graph,'FAQPage')
            existing = list(faq['mainEntity']) if faq else []
            replacements = []
            if route == '/과목별학원/':
                replacements = [
                    {'old':'학년과 과목을 먼저 선택한 뒤 지역별 학습 안내를 찾을 수 있도록 정리한 전문수업.com 과목별 학원 허브입니다.','new':'자녀의 학년과 필요한 과목을 선택해 보세요. 지역별 안내에서 학교 공부, 오답 복습과 상담 준비에 필요한 내용을 확인할 수 있습니다.'},
                    {'old':'검색 의도에 맞춘 안내','new':'학생 상태에 맞는 선택'},
                    {'old':'실제로 생성된 허브만 표시하며, 존재하지 않는 카테고리는 노출하지 않습니다.','new':'중2·중3·고1·고2의 수학·영어 안내를 확인할 수 있습니다. 현재 배우는 범위와 어려움을 기준으로 살펴보세요.'}]
            elif route.startswith('/과목별학원/'):
                label = item['label']
                learning = {
                    '고1 수학학원':'학교 자료에 맞춘 풀이 기록과 답안 마무리', '고1 영어학원':'학교 영어 자료의 이해와 질문에 맞는 답 쓰기',
                    '고2 수학학원':'실제 수강 범위의 개념 연결과 조건 판단', '고2 영어학원':'현재 과목 자료의 의미 이해와 근거에 맞는 표현',
                    '중2 수학학원':'학교에서 배운 개념의 설명과 문제 적용', '중2 영어학원':'학교 문장의 이해와 배운 표현의 활용',
                    '중3 수학학원':'누적 오답의 원인과 독립적인 풀이 검토', '중3 영어학원':'배운 어휘·표현의 활용과 읽기 근거 확인'}[label]
                new_pairs = [
                    (f'지역별 {label} 안내에서 무엇을 확인할 수 있나요?', f'센터 위치와 기재된 학교·가능 학년, 교육비 확인 링크를 살펴볼 수 있습니다. {learning}에 필요한 점검 기준도 함께 확인해 보세요.'),
                    (f'{label.replace("학원", "")} 수업의 현재 수강 가능 여부는 어떻게 확인하나요?', '지역 안내의 대상 학년을 먼저 확인하고, 현재 학년과 배우는 범위를 정리해 상담 시 수강 가능 여부를 확인해 주세요. 학년 정보가 없는 경우에도 개설되어 있다고 가정하지 않고 문의하는 것이 좋습니다.')]
                for old, (q,a) in zip(existing[:2], new_pairs):
                    replacements += [{'old':old['name'],'new':q},{'old':old['acceptedAnswer']['text'],'new':a}]
                    old['name'] = q; old['acceptedAnswer']['text'] = a
            head, body = source.split('<body>',1)
            for pair in replacements:
                assert pair['old'] in body, (rel,pair['old'])
                body = body.replace(pair['old'],pair['new'])
            policies[rel] = replacements
            if route == '/전국학원/':
                parser = Regions(); parser.feed(body); assert len(parser.links) == 13, parser.links
                listing = node_list(graph,'ItemList')
                listing['itemListElement'] = [{'@type':'ListItem','position':i+1,'name':name,'url':BASE+quote('/전국학원/'+name+'/')} for i,name in enumerate(parser.links)]
                webpage['@type'] = 'CollectionPage'; webpage['mainEntity'] = {'@id':listing['@id']}
            new_questions = [question(x['question'],x['answer']) for x in item['faqs']]
            if not faq:
                faq = {'@type':'FAQPage','@id':url+'#faq','mainEntity':[]}; graph.append(faq)
            faq['mainEntity'] = existing + new_questions
            visible_questions = (existing if route == '/전국학원/' else []) + new_questions
            parts = []
            section_html = []
            for i,section in enumerate(item['sections']):
                sid = section['id']; parts.append({'@id':url+'#'+sid})
                graph.append({'@type':'WebPageElement','@id':url+'#'+sid,'url':url+'#'+sid,'name':section['title'],'text':'\n\n'.join(section['paragraphs']),'isPartOf':{'@id':webpage['@id']}})
                section_html.append(f'<section class="sh-lesson" id="{sid}"><span class="sh-number" aria-hidden="true">{i+1:02}</span><div class="sh-lesson-copy"><h3>{escape(section["title"])}</h3>'+''.join('<p>'+escape(p)+'</p>' for p in section['paragraphs'])+'</div></section>')
            centers_html = []
            mentions = []
            for c in CENTERS:
                cid = BASE+'/#center-'+c['key']; mentions.append({'@id':cid})
                graph.append({'@type':'EducationalOrganization','@id':cid,'name':c['name'],'url':BASE+quote(c['href']),'address':{'@type':'PostalAddress','streetAddress':c['address'],'addressCountry':'KR'},'identifier':{'@type':'PropertyValue','name':'교육지원청 등록번호','value':c['registration']}})
                centers_html.append('<article class="sh-center"><p class="sh-center-region">'+escape(c['region'])+'</p><h3>'+escape(c['name'])+'</h3><p>'+escape(c['address'])+'</p><p class="sh-registration">'+escape(c['registration'])+'</p><a href="'+quote(c['href'])+'">'+escape(c['name'].split()[-1])+' 지역 안내 <span aria-hidden="true">→</span></a></article>')
            webpage['hasPart'] = webpage.get('hasPart',[]) + parts + [{'@id':faq['@id']}]
            webpage['mentions'] = webpage.get('mentions',[]) + mentions
            webpage['dateModified'] = DATE
            questions_html = ''.join(details(q['name'],q['acceptedAnswer']['text']) for q in visible_questions)
            pictures = ''.join(f'<figure><img src="/assets/hub-classroom-{i}.webp" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{escape(item["label"])} 학습 공간 예시 {i}"><figcaption>{caption}</figcaption></figure>' for i,w,h,caption in [(1,500,300,'개별 책상이 배치된 학습 공간 예시'),(2,800,600,'학습 좌석과 교실 구성을 살펴보는 공간 예시')])
            links = ''.join('<a href="'+quote(x['href'],safe='/#')+'">'+escape(x['label'])+' <span aria-hidden="true">→</span></a>' for x in item['readLinks'])
            addition = f'''\n<!-- studio-hub-content:start 2026-09-10 -->
<div class="shell studio-hub-content">
 <div class="sh-intro" id="hub-learning"><p class="sh-kicker">LEARNING NOTES</p><h2>{escape(item['label'])}, 선택 전에 살펴볼 내용</h2><p>학생의 현재 자료를 기준으로 읽고, 필요한 질문을 골라 보세요.</p></div>
 <div class="sh-lessons">{''.join(section_html)}</div>
 <section class="sh-centers" id="hub-centers"><div class="sh-intro"><p class="sh-kicker">CENTER INFORMATION</p><h2>지역 안내에서 확인하는 센터 정보</h2><p>지역별 안내에 연결된 센터 예시입니다. 원하는 지역의 위치와 대상 학년을 확인하고, 현재 수강 가능한 과목과 방문 일정은 상담 시 문의해 주세요.</p></div><div class="sh-center-grid">{''.join(centers_html)}</div><div class="sh-photos">{pictures}</div><p class="sh-photo-note">위 사진은 공통 학습 공간 예시이며, 특정 지점의 현재 시설을 뜻하지 않습니다.</p></section>
 <section class="sh-faq" id="faq"><div class="sh-intro"><p class="sh-kicker">QUESTIONS &amp; ANSWERS</p><h2>학습과 상담 Q&amp;A</h2></div><div class="sh-faq-list">{questions_html}</div></section>
 <nav class="sh-reading" id="related-pages" aria-label="함께 읽을 학습 안내"><h2>필요한 내용을 조금 더 살펴보세요</h2><div class="sh-reading-links">{links}</div></nav>
</div>
<!-- studio-hub-content:end -->\n'''
            assert 'id="faq"' not in body and 'id="related-pages"' not in body
            body = body.replace('</main>', addition+'</main>',1)
            jump = '<nav class="shell studio-hub-jump" aria-label="허브 내용 바로가기"><a href="#hub-learning">학습 선택 기준</a><a href="#hub-centers">센터 정보</a><a href="#faq">학습 Q&amp;A</a></nav>'
            body = body.replace('</section>', '</section>'+jump,1)
            head = LD.sub(lambda m:m.group(1)+json.dumps(doc,ensure_ascii=False,separators=(',',':'))+m.group(3),head,count=1)
            head = head.replace('</head>','<link rel="stylesheet" href="/assets/hub-guide.css?v=20260910"></head>')
            output = head+'<body class="studio-hub-page">'+body
            output = re.sub(r'^[ \t]+$', '', output, flags=re.M)
            (ROOT/rel).write_text(output,encoding='utf-8')
    (args.copy_dir/'exact-text-replacements.json').write_text(json.dumps(policies,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    s = (ROOT/'sitemap.xml').read_text('utf-8')
    count = 0
    def update(m):
        nonlocal count
        block = m.group(0); loc = re.search(r'<loc>(.*?)</loc>',block).group(1)
        if unquote(urlparse(loc).path) in content:
            count += 1
            block = re.sub(r'<lastmod>.*?</lastmod>',f'<lastmod>{DATE}</lastmod>',block)
        return block
    s = re.sub(r'<url>.*?</url>',update,s,flags=re.S); assert count == 10
    (ROOT/'sitemap.xml').write_text(s,encoding='utf-8')
    print(json.dumps({'hubs':len(content),'sections':30,'new_faqs':40,'existing_faqs_exposed':3,'sitemap_dates':count},ensure_ascii=False))

if __name__ == '__main__':
    main()
