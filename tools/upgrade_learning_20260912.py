"""Bounded site5 overview upgrade; never regenerate locality manuscripts.

Regenerates only from the reviewed Git baseline and checked-in editorial inputs.
Refuses to overwrite a manual change to a previously generated output.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from html import escape
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import quote, unquote, urljoin, urlsplit
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'cde2db79073bddb85cc1441d3de2a636a8b4c72d'
DOMAIN = 'https://xn--z92bu9jx8cwzc.com'
DATA = ROOT / 'tools/data/learning-upgrade'
REPORT = ROOT / 'tools/reports/learning-upgrade/generation.json'
CONTENT = json.loads((DATA / 'content.json').read_text('utf-8-sig'))
CORE = {'index.html': 'home', '학습가이드/index.html': 'guide',
        '상담문의/index.html': 'contact', '학습코칭/index.html': 'coaching'}
REGIONS = {f'전국학원/{region}/index.html': region for region in CONTENT['regionNotes']}
TARGETS = list(CORE) + list(CONTENT['hubs']) + list(REGIONS)
NEW_PAGE = '학습코칭/index.html'
META = {
    'home': ('와와센터 | 영어·수학·국어 학습코칭과 지역별 학원 안내', '학생별 진단과 4C 맞춤 코칭, AI 영어·수학·국어·독서 구성을 알아보세요. 중2·중3·고1·고2 과목별 안내와 전국 지역 목록에서 필요한 센터 정보, 공부 방법과 상담 준비를 확인할 수 있습니다.'),
    'coaching': ('와와 학습코칭·AI 학습 | 4C 관리와 과목별 활용 안내', '와와 4C 맞춤 진단·처방·지도·상담, 플랜·학습·생활 관리와 AI 과목별 구성·대상 학년을 안내합니다. 진단 결과를 복습에 활용하는 방법과 센터에 확인할 질문을 살펴보세요.'),
    'guide': ('학습가이드 | 시험 준비·플래너·오답 기록과 학부모 상담', '학교 시험 범위를 정리하고 계획과 실제 공부량을 비교하는 방법, 오답 재풀이 기록과 학부모 상담 자료를 안내합니다. 학생의 학교 일정과 이해 상태에 맞춰 활용할 수 있는 구체적인 공부 예시입니다.'),
    'contact': ('학습 상담문의 | 학년·지역·과목별 준비와 확인 사항', '와와센터 상담 전화·문자·신청 방법을 확인하세요. 학생 학년, 관심 과목, 지역과 최근 공부 자료를 준비하고 개설 여부·방문 일정·교습비·AI 이용 조건을 센터에 문의할 수 있습니다.')
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def baseline(path):
    return subprocess.run(['git', 'show', BASELINE + ':' + path], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def canon(path):
    return DOMAIN + '/' + quote(path.removesuffix('index.html'), safe='/')


def fragment(text):
    return BeautifulSoup(text, 'html.parser')


def inject(parent, text):
    for child in list(fragment(text).contents):
        parent.append(child)


def faq_html(items, heading='먼저 궁금한 점을 확인해 보세요'):
    details = ''.join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q, a in items)
    return f'<section class="shell pl-section pl-faq" id="faq"><div class="pl-section-head"><p class="pl-kicker">질문과 답변</p><h2>{escape(heading)}</h2></div><div class="pl-faq-list">{details}</div></section>'


def grade_links():
    cards = []
    for grade in ['중2', '중3', '고1', '고2']:
        links = ''.join(f'<a href="/과목별학원/{grade}{subject}학원/">{grade} {subject}학원 <span aria-hidden="true">→</span></a>' for subject in ['영어', '수학'])
        cards.append(f'<article class="pl-grade-card"><h3>{grade}</h3>{links}</article>')
    return '<div class="pl-subject-grid">' + ''.join(cards) + '</div>'


def videos_html():
    videos = [('student', 'avpJfW7eIV0', '학생들의 공부 이야기', '공부 경험과 생각을 전하는 학생들의 이야기'),
              ('coaching', 'f_skFu40U04', '코칭 현장의 인터뷰', '원장 인터뷰를 통해 살펴보는 학습 코칭의 관점'),
              ('exam', 'UIXUaBZdNXU', '은평점의 시험기간', '시험을 앞둔 센터의 공부 장면과 학습 이야기')]
    return '<div class="pl-grid pl-three">' + ''.join(
        f'<a class="pl-video-card" href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener noreferrer"><img src="/assets/official-learning/video-{key}.jpg" width="480" height="360" alt="와와센터 {title} 공식 영상 썸네일" loading="lazy"><div class="pl-video-copy"><span class="pl-index">공식 영상</span><h3>{title}</h3><p>{description}</p><span class="pl-link-label">영상 보기 · YouTube 새 창 ↗</span></div></a>' for key, vid, title, description in videos) + '</div>'


def grouping_label(text):
    return (str(text).replace('시군구를', '지역 묶음을').replace('시군구와', '지역 묶음과')
            .replace('시군구가', '지역 묶음이').replace('시군구로', '지역 묶음으로')
            .replace('시군구', '지역 묶음'))


def home_regions():
    s = fragment(baseline('index.html').decode('utf-8-sig'))
    section = s.select_one('.home-region-shortcuts')
    assert section
    section['id'] = 'region-paths'
    for text in list(section.find_all(string=True)):
        if text.parent.name not in ('script', 'style') and '시군구' in text:
            text.replace_with(grouping_label(text))
    for link in section.select('a[href]'):
        u = urlsplit(urljoin(DOMAIN + '/', link['href']))
        if u.netloc == urlsplit(DOMAIN).netloc:
            link['href'] = unquote(u.path).removesuffix('index.html') + (('#' + u.fragment) if u.fragment else '')
    return str(section)


def upgrade_chrome(soup, path, new=False):
    soup.body['class'] = list(dict.fromkeys(soup.body.get('class', []) + ['pro-upgrade']))
    soup.body['data-learning-upgrade'] = '20260912'
    nav = soup.select_one('header .top-nav')
    nav.clear()
    for label, href in [('홈', '/'), ('학습코칭', '/학습코칭/'), ('학습가이드', '/학습가이드/'),
                        ('과목별학원', '/과목별학원/'), ('전국학원', '/전국학원/'), ('상담문의', '/상담문의/')]:
        active = path == 'index.html' if href == '/' else path.startswith(href.lstrip('/'))
        a = soup.new_tag('a', href=href)
        a.string = label
        if active:
            a['class'] = ['active']
            a['aria-current'] = 'page' if path == href.lstrip('/') + 'index.html' or path == 'index.html' else 'location'
        nav.append(a)
    brand = soup.select_one('header .brand')
    if brand:
        brand['href'] = '/'
        small = brand.select_one('small')
        if small:
            small.string = '전문수업.com'
    if new:
        for node in soup.select('head link[href], script[src]'):
            attr = 'href' if node.name == 'link' else 'src'
            if node[attr].startswith('assets/'):
                node[attr] = '/' + node[attr]
    soup.head.append(soup.new_tag('link', rel='stylesheet', href='/assets/learning-upgrade.css?v=20260912'))
    # Static links remain visible without JavaScript and use native fragment navigation.
    footer = soup.select_one('.site-footer')
    if footer:
        inject(footer, '<nav class="pl-footer-links" aria-label="관련 학습 안내"><a href="/학습코칭/">학습코칭</a><a href="/학습가이드/">학습가이드</a><a href="/과목별학원/">과목별학원</a><a href="/전국학원/">전국학원</a></nav>')


def brief_html(item):
    paragraphs = ''.join(f'<p>{escape(text)}</p>' for text in item['paragraphs'])
    checks = '<ul class="pl-list">' + ''.join(f'<li>{escape(text)}</li>' for text in item['checks']) + '</ul>'
    links = ''.join(f'<a href="{escape(href)}">{escape(label)} <span aria-hidden="true">→</span></a>' for href, label in item['links'])
    return f'<section class="shell pl-hub-brief" id="hub-coaching"><p class="pl-kicker">지역 안내와 함께 읽는 학습 기준</p><h2>{escape(item["title"])}</h2>{paragraphs}{checks}<div class="pl-hub-links">{links}</div></section>'


def upgrade_hub(soup, path):
    jump = soup.select_one('.studio-hub-jump')
    assert jump
    a = soup.new_tag('a', href='#hub-coaching')
    a.string = '코칭·AI 활용'
    jump.append(a)
    jump.insert_after(fragment(brief_html(CONTENT['hubs'][path])))
    if path == '과목별학원/index.html':
        groups = []
        for subject, section in [('영어', 'english-options'), ('수학', 'math-options')]:
            links = ''.join(f'<a href="/과목별학원/{grade}{subject}학원/">{grade} {subject}</a>' for grade in ['중2', '중3', '고1', '고2'])
            groups.append(f'<div id="{section}"><h3>학년별 {subject} 안내</h3>{links}</div>')
        inject(soup.select_one('#hub-coaching'), '<nav class="pl-choice-links" aria-label="과목별 빠른 선택">' + ''.join(groups) + '</nav>')


def upgrade_region(soup, path, region):
    directory = soup.select_one('.all-town-directory')
    assert directory
    directory['id'] = 'region-towns'
    list_section = next(x for x in soup.select('main > section.academy-section') if x != directory)
    list_section['id'] = 'region-list'
    # The inherited grouping includes roads and broader areas, not just municipalities.
    for text in list(soup.main.find_all(string=True)):
        if text.parent.name not in ('script', 'style') and '시군구' in text:
            text.replace_with(grouping_label(text))
    old = soup.select_one('.learning-summary-form')
    if old:
        old.decompose()
    town_links = directory.select('a[href]')
    sample_links = []
    for a in town_links[:3]:
        href = urlsplit(urljoin(canon(path), a['href'])).path
        sample_links.append([unquote(href).removesuffix('index.html'), a.get_text(' ', strip=True)])
    item = {'title': f'{region}에서 센터를 찾을 때 확인할 순서',
            'paragraphs': [CONTENT['regionNotes'][region], f'현재 이 목록에는 {len(town_links)}개의 동네 안내가 있습니다. 아래 숫자는 안내 페이지 수이며, 각각이 별도의 센터나 현재 수업 가능한 반을 의미하지는 않습니다.'],
            'checks': ['상세 페이지의 센터 이름·주소를 확인하기', '학생의 학년·과목·방문 시간과 프로그램 조건을 문의하기'],
            'links': [['/학습코칭/#four-c', '센터의 맞춤 관리 과정을 이해하기'], ['/상담문의/#ask-center', '위치 확인 후 물어볼 수업 조건']]}
    hero = soup.select_one('.sub-hero')
    hero.select_one('h1').find_next_sibling('p').string = f'{region} 지역의 학원 안내를 동네별로 모았습니다. 가까운 동네를 고른 뒤 센터의 실제 주소, 대상 학년과 필요한 과목을 함께 확인해 보세요.'
    jump = fragment('<nav class="shell pl-jump" aria-label="지역 안내 목차"><a href="#hub-coaching">센터 선택 기준</a><a href="#region-list">등록 지역 목록</a><a href="#region-towns">동네 바로가기</a><a href="#faq">이용 질문</a></nav>')
    hero.insert_after(jump)
    # insert_after(fragment) reparents children; locate the inserted navigation again.
    soup.select_one('.pl-jump').insert_after(fragment(brief_html(item)))
    link_markup = ''.join(f'<a href="{escape(href)}">{escape(label)} <span aria-hidden="true">→</span></a>' for href, label in sample_links)
    inject(soup.select_one('#hub-coaching'), f'<div class="pl-hub-links" aria-label="{region} 동네 안내 예시">{link_markup}</div>')
    qs = [[f'{region} 목록의 동네 수가 실제 지점 수인가요?', f'아닙니다. 이 페이지의 {len(town_links)}개 동네 링크는 등록된 안내 페이지 수입니다. 같은 센터와 연결되는 동네가 있을 수 있으므로 상세 센터 이름과 주소를 확인해 주세요.'],
          [f'{region}에서 영어·수학 학년별 안내도 찾을 수 있나요?', '전국학원의 동네 상세 안내와 별도로 과목별학원에서 중2·중3·고1·고2 영어·수학 안내를 찾을 수 있습니다. 페이지의 학습 설명과 실제 센터의 개설 여부를 나누어 확인하세요.']]
    inject(soup.main, faq_html(qs, f'{region} 지역 안내 이용 질문'))
    return item


def visible_faq(soup):
    pairs = []
    for detail in soup.select('.pl-faq-list details, .faq-list details, .sh-faq-list details'):
        summary = detail.find('summary', recursive=False)
        if not summary:
            continue
        answer = ' '.join(x.get_text(' ', strip=True) for x in detail.find_all('p', recursive=False))
        if answer:
            pairs.append((summary.get_text(' ', strip=True), answer))
    return pairs


def set_meta(soup, name, value, prop=False):
    key = 'property' if prop else 'name'
    nodes = soup.find_all('meta', attrs={key: name})
    tag = nodes[0] if nodes else soup.new_tag('meta', attrs={key: name})
    tag['content'] = value
    if not nodes:
        soup.head.append(tag)
    for extra in nodes[1:]:
        extra.decompose()


def sync_schema(soup, path, mode, modified, new):
    old_graph = []
    for script in soup.select('script[type="application/ld+json"]'):
        data = json.loads(script.string or script.get_text())
        old_graph.extend(data.get('@graph', [data]))
        script.decompose()
    url = canon(path) if new else soup.select_one('link[rel="canonical"]')['href']
    soup.select_one('link[rel="canonical"]')['href'] = url
    if mode in META:
        title, description = META[mode]
        soup.title.string = title
        set_meta(soup, 'description', description)
    else:
        title = soup.title.get_text()
        description = soup.select_one('meta[name="description"]')['content']
        if path == '전국학원/index.html':
            description = '등록된 지역과 동네의 학습코칭 안내에서 센터 이름·주소와 학습 정보를 확인하세요. 학년·과목별 안내, 4C 코칭 설명과 실제 개설 여부·방문 조건을 확인할 상담 질문을 함께 제공합니다.'
            set_meta(soup, 'description', description)
        elif path == '과목별학원/index.html':
            description = '중2·중3·고1·고2의 영어·수학 학원 안내를 학년과 지역별로 살펴보세요. 학교 진도·오답 복습·상담 준비 기준을 읽고, 관심 지역의 센터 정보와 실제 개설 여부를 확인할 수 있습니다.'
            set_meta(soup, 'description', description)
        elif path in REGIONS:
            description = f'{REGIONS[path]}의 등록된 지역·동네별 학습코칭 안내입니다. 상세 페이지에서 센터 이름과 주소를 살피고, 학생 학년·과목·방문 시간과 프로그램 이용 조건을 확인할 질문을 준비하세요.'
            set_meta(soup, 'description', description)
    for key, value in [('og:title', title), ('og:description', description), ('og:url', url)]:
        set_meta(soup, key, value, True)
    if soup.select_one('meta[name="twitter:title"]'):
        set_meta(soup, 'twitter:title', title)
        set_meta(soup, 'twitter:description', description)
    org = next((n.copy() for n in old_graph if n.get('@id') == DOMAIN + '/#organization'), None)
    if org is None:
        home_graph = json.loads(fragment(baseline('index.html').decode('utf-8-sig')).select_one('script[type="application/ld+json"]').string)['@graph']
        org = next(n.copy() for n in home_graph if n.get('@id') == DOMAIN + '/#organization')
    org.pop('openingHours', None)
    org.pop('openingHoursSpecification', None)
    website = {'@type': 'WebSite', '@id': DOMAIN + '/#website', 'url': DOMAIN + '/', 'name': '와와센터', 'inLanguage': 'ko-KR'}
    if mode in CORE.values():
        label = '홈' if mode == 'home' else {'coaching': '학습코칭', 'guide': '학습가이드', 'contact': '상담문의'}[mode]
        crumbs = [{'@type': 'ListItem', 'position': 1, 'name': '홈', 'item': DOMAIN + '/'}]
        if mode != 'home':
            crumbs.append({'@type': 'ListItem', 'position': 2, 'name': label, 'item': url})
        webpage = {'@type': 'ContactPage' if mode == 'contact' else 'WebPage', '@id': url + '#webpage', 'url': url}
        graph = [website, org, webpage, {'@type': 'BreadcrumbList', '@id': url + '#breadcrumb', 'itemListElement': crumbs}]
        if mode in ('coaching', 'guide'):
            graph.append({'@type': 'Article', '@id': url + '#article', 'headline': title,
                          'description': description, 'mainEntityOfPage': {'@id': url + '#webpage'},
                          'author': {'@id': org['@id']}, 'publisher': {'@id': org['@id']}, 'inLanguage': 'ko-KR',
                          'dateModified': modified, 'about': [{'@type': 'Thing', 'name': '학습코칭'}, {'@type': 'Thing', 'name': '복습 기록'}]})
            webpage['mainEntity'] = {'@id': url + '#article'}
        elif mode == 'home':
            webpage['mainEntity'] = {'@id': org['@id']}
        else:
            webpage['mainEntity'] = {'@id': org['@id']}
    else:
        graph = [n for n in old_graph if n.get('@type') != 'FAQPage']
        if not any(n.get('@id') == website['@id'] for n in graph):
            graph.insert(0, website)
        if not any(n.get('@id') == org['@id'] for n in graph):
            graph.insert(1, org)
        else:
            graph = [org if n.get('@id') == org['@id'] else n for n in graph]
        webpage = next(n for n in graph if n.get('@id') == url + '#webpage')
    webpage.update(name=title, description=description, inLanguage='ko-KR', dateModified=modified,
                   isPartOf={'@id': website['@id']}, publisher={'@id': org['@id']}, breadcrumb={'@id': url + '#breadcrumb'})
    parts = []
    headings = []
    for section in soup.main.select('section[id], article[id]'):
        heading = section.find(['h2', 'h3'])
        if heading:
            name = heading.get_text(' ', strip=True)
            headings.append(name)
            parts.append({'@type': 'WebPageElement', '@id': url + '#' + section['id'], 'url': url + '#' + section['id'], 'name': name})
    webpage['hasPart'] = parts
    links = []
    for a in soup.main.select('a[href]'):
        u = urlsplit(urljoin(url, a['href']))
        if u.netloc == urlsplit(DOMAIN).netloc and (a.find_parent(class_='pl-hub-brief') or unquote(u.path).startswith(('/학습코칭/', '/학습가이드/', '/상담문의/'))):
            full = DOMAIN + quote(unquote(u.path), safe='/') + (('#' + u.fragment) if u.fragment else '')
            if full not in links:
                links.append(full)
    webpage['significantLink'] = links
    mentions = webpage.get('mentions', [])
    if isinstance(mentions, dict):
        mentions = [mentions]
    if not any(x.get('@id') == canon(NEW_PAGE) + '#webpage' for x in mentions):
        mentions.append({'@id': canon(NEW_PAGE) + '#webpage'})
    webpage['mentions'] = mentions
    for node in graph:
        if node.get('@type') == 'Article':
            node.update(headline=title, description=description, dateModified=modified, articleSection=headings)
        elif node.get('@type') == 'Service':
            node['description'] = description
    pairs = visible_faq(soup)
    if pairs:
        graph.append({'@type': 'FAQPage', '@id': url + '#faq', 'isPartOf': {'@id': url + '#webpage'},
                      'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in pairs]})
    script = soup.new_tag('script', type='application/ld+json')
    script.string = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', r'<\/')
    soup.head.append(script)
    return {'url': url, 'title': title, 'description': description, 'faqs': len(pairs), 'contextLinks': links}


def main():
    assert len(TARGETS) == 27 and len(set(TARGETS)) == 27
    previous = json.loads(REPORT.read_text('utf-8')) if REPORT.exists() else {}
    modified = previous.get('modified') or datetime.now(timezone(timedelta(hours=9))).isoformat(timespec='seconds')
    writes = {}
    rows = []
    for path in TARGETS:
        new = path == NEW_PAGE
        original = baseline('index.html' if new else path)
        current = (ROOT / path).read_bytes() if (ROOT / path).exists() else None
        known = previous.get('hashes', {}).get(path)
        safe = current is None if new else current.replace(b'\r\n', b'\n') == original.replace(b'\r\n', b'\n')
        assert safe or (known and sha(current) == known), 'Unreviewed edit: ' + path
        soup = fragment(original.decode('utf-8-sig'))
        mode = CORE.get(path, 'region' if path in REGIONS else 'hub')
        if mode in CORE.values():
            raw = (DATA / f'{mode}.html').read_text('utf-8')
            raw = raw.replace('<!-- page-faq -->', faq_html(CONTENT['faq'][mode]))
            raw = raw.replace('<!-- subject-links -->', grade_links())
            raw = raw.replace('<!-- video-cards -->', videos_html())
            if '<!-- home-regions -->' in raw:
                raw = raw.replace('<!-- home-regions -->', home_regions())
            soup.main.replace_with(fragment(raw).main)
        elif mode == 'hub':
            upgrade_hub(soup, path)
            if path == '전국학원/index.html':
                for text in list(soup.main.find_all(string=True)):
                    if text.parent.name not in ('script', 'style') and '시군구' in text:
                        text.replace_with(grouping_label(text))
        else:
            upgrade_region(soup, path, REGIONS[path])
        upgrade_chrome(soup, path, new)
        metadata = sync_schema(soup, path, mode, modified, new)
        output = str(soup).replace('\r\n', '\n').encode('utf-8')
        writes[path] = output
        rows.append({'path': path, 'mode': mode, **metadata, 'changed': output != current})
    # Discovery files retain all previous URL identities and order; append just the new pillar.
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    xml = ET.fromstring(baseline('sitemap.xml'))
    index = {unquote(row['url']): row for row in rows}
    found = set()
    for entry in xml.findall(f'{{{ns}}}url'):
        location = unquote(entry.findtext(f'{{{ns}}}loc'))
        if location in index:
            found.add(location)
            lastmod = entry.find(f'{{{ns}}}lastmod')
            if lastmod is None:
                lastmod = ET.SubElement(entry, f'{{{ns}}}lastmod')
            lastmod.text = modified
    assert len(found) == 26, len(found)
    entry = ET.SubElement(xml, f'{{{ns}}}url')
    ET.SubElement(entry, f'{{{ns}}}loc').text = canon(NEW_PAGE)
    ET.SubElement(entry, f'{{{ns}}}lastmod').text = modified
    ET.indent(xml, space='  ')
    writes['sitemap.xml'] = ET.tostring(xml, encoding='utf-8', xml_declaration=True) + b'\n'
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
    rss = ET.fromstring(baseline('rss.xml'))
    channel = rss.find('channel')
    date = format_datetime(datetime.fromisoformat(modified))
    channel.find('lastBuildDate').text = date
    rss_found = set()
    for item in channel.findall('item'):
        location = unquote(item.findtext('link'))
        if location in index:
            row = index[location]
            for tag, value in [('title', row['title']), ('description', row['description']), ('pubDate', date)]:
                child = item.find(tag)
                if child is None:
                    child = ET.SubElement(item, tag)
                child.text = value
            rss_found.add(location)
    row = next(row for row in rows if row['path'] == NEW_PAGE)
    item = ET.SubElement(channel, 'item')
    for tag, value in [('title', row['title']), ('link', row['url']), ('guid', row['url']), ('pubDate', date), ('description', row['description'])]:
        child = ET.SubElement(item, tag)
        if tag == 'guid':
            child.set('isPermaLink', 'true')
        child.text = value
    ET.indent(rss, space='  ')
    writes['rss.xml'] = ET.tostring(rss, encoding='utf-8', xml_declaration=True) + b'\n'
    llms = baseline('llms.txt').decode('utf-8-sig').rstrip()
    llms += '\n\n## 학습코칭과 상담 준비\n\n- [와와 4C 학습코칭과 AI 과목별 안내](' + canon(NEW_PAGE) + ')\n- [공부 계획과 오답 기록](' + canon('학습가이드/index.html') + ')\n- [센터 이용 조건과 상담 준비](' + canon('상담문의/index.html') + ')\n\nAI 영어·수학은 본사 안내상 초1~고3, AI 국어는 중1~고3, AI 독서는 초1~중2 대상입니다. 개별 센터의 개설·이용 조건은 별도 확인해야 합니다. 지역·동네 링크 수는 안내 페이지 수이며 지점 수가 아닙니다.\n'
    writes['llms.txt'] = llms.replace('\r\n', '\n').encode('utf-8')
    # Preflight all outputs before any write, including discovery files.
    for path, output in writes.items():
        current = (ROOT / path).read_bytes() if (ROOT / path).exists() else None
        if path not in TARGETS:
            assert current.replace(b'\r\n', b'\n') == baseline(path).replace(b'\r\n', b'\n') or sha(current) == previous.get('hashes', {}).get(path), 'Unreviewed discovery edit: ' + path
    for path, output in writes.items():
        dest = ROOT / path
        if not dest.exists() or dest.read_bytes() != output:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(output)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {'baseline': BASELINE, 'modified': modified, 'deployment': 'Not requested; local only',
              'targets': rows, 'hashes': {path: sha(output) for path, output in writes.items()},
              'sitemapUrls': len(xml.findall(f'{{{ns}}}url')), 'rssItems': len(channel.findall('item')), 'rssUpdated': len(rss_found)}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'pages': len(rows), 'changed': sum(row['changed'] for row in rows), 'faqs': sum(row['faqs'] for row in rows), 'sitemapUrls': report['sitemapUrls'], 'rssItems': report['rssItems']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
