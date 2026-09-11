"""Independent DOM, preservation, discovery and local HTTP checks for site5."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.parse import unquote, urljoin, urlsplit, quote
from urllib.request import urlopen
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'tools/data/learning-upgrade'
REPORT = ROOT / 'tools/reports/learning-upgrade'
DOMAIN = 'https://xn--z92bu9jx8cwzc.com'
BASE = 'cde2db79073bddb85cc1441d3de2a636a8b4c72d'
GEN = json.loads((REPORT / 'generation.json').read_text('utf-8'))
checks, errors, pages = [], [], []
cache = {}


def check(name, passed, detail=None):
    row = {'check': name, 'passed': bool(passed)}
    if not passed:
        row['detail'] = detail
        errors.append(row)
    checks.append(row)


def git(*args):
    return subprocess.check_output(['git', '-c', 'core.safecrlf=false', *args], cwd=ROOT)


def base(path):
    return git('show', BASE + ':' + path)


def soup(path):
    if path not in cache:
        cache[path] = BeautifulSoup((ROOT / path).read_bytes(), 'html.parser', from_encoding='utf-8')
    return cache[path]


def faq(doc):
    pairs = []
    for d in doc.select('.pl-faq-list details, .faq-list details, .sh-faq-list details'):
        summary = d.find('summary', recursive=False)
        ps = d.find_all('p', recursive=False)
        if summary and ps:
            pairs.append((summary.get_text(' ', strip=True), ' '.join(p.get_text(' ', strip=True) for p in ps)))
    return pairs


def resolve(url):
    parsed = urlsplit(url)
    path = unquote(parsed.path).lstrip('/')
    if not path or path.endswith('/'):
        path += 'index.html'
    return path, unquote(parsed.fragment)


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--http', action='store_true')
    run_http = args.parse_args().http
    targets = {row['path'] for row in GEN['targets']}
    old_targets = targets - {'학습코칭/index.html'}
    tracked_changed = set(x for x in git('diff', '--name-only', '-z').decode().split('\0') if x)
    allowed = old_targets | {'sitemap.xml', 'rss.xml', 'llms.txt', '.vercelignore', 'PROJECT_HANDOFF.md'}
    check('HEAD unchanged and correct repository', git('rev-parse', 'HEAD').decode().strip() == BASE)
    check('No changes staged for deployment', not git('diff', '--cached', '--name-only').strip())
    check('Tracked changes are strictly in scope', not tracked_changed - allowed, sorted(tracked_changed - allowed))
    originals = [x for x in git('ls-files', '-z', '*.html').decode().split('\0') if x]
    check('Original HTML inventory', len(originals) == 7151, len(originals))
    check('All 7125 non-target HTML unchanged', len(set(originals) - old_targets) == 7125 and not ((set(originals) - old_targets) & tracked_changed))
    check('Shared CSS and JS untouched', (ROOT / 'assets/site.css').read_bytes().replace(b'\r\n', b'\n') == base('assets/site.css').replace(b'\r\n', b'\n') and (ROOT / 'assets/site.js').read_bytes().replace(b'\r\n', b'\n') == base('assets/site.js').replace(b'\r\n', b'\n'))
    check('Private editorial tools excluded from deployment', 'tools/' in (ROOT / '.vercelignore').read_text())
    check('Legacy image files unchanged', not any(x.startswith('assets/') for x in tracked_changed))
    all_links, asset_paths = set(), set()
    titles, descriptions = [], []
    total_faq = 0
    for row in GEN['targets']:
        path, mode = row['path'], row['mode']
        doc = soup(path)
        label = path + ': '
        check(label + 'one H1 and title', len(doc.select('h1')) == 1 and len(doc.select('title')) == 1)
        check(label + 'renamed grouping has correct Korean particles', not any(x in doc.main.get_text() for x in ('지역 묶음와', '지역 묶음로', '지역 묶음를', '지역 묶음가')))
        check(label + 'one canonical and description', len(doc.select('link[rel="canonical"]')) == 1 and len(doc.select('meta[name="description"]')) == 1)
        canonical = doc.select_one('link[rel="canonical"]')['href']
        title = doc.title.get_text(' ', strip=True)
        description = doc.select_one('meta[name="description"]')['content']
        titles.append(title)
        descriptions.append(description)
        check(label + 'canonical and OG URL agree', canonical == doc.select_one('meta[property="og:url"]')['content'] == row['url'])
        check(label + 'title and social title agree', title == doc.select_one('meta[property="og:title"]')['content'] == row['title'])
        check(label + 'description and social description agree', description == doc.select_one('meta[property="og:description"]')['content'] == row['description'])
        check(label + 'indexable', 'noindex' not in str(doc.select_one('meta[name="robots"]')).lower())
        ids = [tag['id'] for tag in doc.select('[id]')]
        check(label + 'unique HTML IDs', len(ids) == len(set(ids)), [x for x, n in Counter(ids).items() if n > 1])
        check(label + 'no nested anchors or headings', not doc.select('a a, h1 h2, h2 h3, p p, p div'))
        check(label + 'six static menu destinations', [a['href'] for a in doc.select('.top-nav a')] == ['/', '/학습코칭/', '/학습가이드/', '/과목별학원/', '/전국학원/', '/상담문의/'])
        check(label + 'scoped mobile stylesheet once', len([x for x in doc.select('link[rel="stylesheet"]') if '/assets/learning-upgrade.css' in x['href']]) == 1 and 'pro-upgrade' in doc.body.get('class', []))
        check(label + 'no heavy video embed', not doc.select('iframe, video') and not any('youtube' in x.get('src', '') for x in doc.select('script[src]')))
        ld_nodes = []
        for tag in doc.select('script[type="application/ld+json"]'):
            try:
                graph = json.loads(tag.string)['@graph']
                ld_nodes += graph
            except Exception as error:
                check(label + 'valid JSON-LD', False, str(error))
        graph_ids = [n.get('@id') for n in ld_nodes if n.get('@id')]
        check(label + 'unique top-level schema entities', len(graph_ids) == len(set(graph_ids)))
        web = next((n for n in ld_nodes if n.get('@id') == canonical + '#webpage'), {})
        check(label + 'WebPage metadata matches body', web.get('name') == title and web.get('description') == description)
        for part in web.get('hasPart', []):
            _, anchor = resolve(part.get('url', ''))
            element = doc.find(id=anchor)
            check(label + 'hasPart ' + anchor, bool(element) and part.get('name') == element.find(['h2', 'h3']).get_text(' ', strip=True))
        displayed = faq(doc)
        declared = [(q['name'], q['acceptedAnswer']['text']) for n in ld_nodes if n.get('@type') == 'FAQPage' for q in n['mainEntity']]
        check(label + 'FAQ display/schema exact match', displayed == declared, {'display': len(displayed), 'schema': len(declared)})
        check(label + 'nonempty FAQ', len(displayed) > 0)
        total_faq += len(displayed)
        check(label + 'no unsupported base opening hours', not any(('openingHours' in n or 'openingHoursSpecification' in n) for n in ld_nodes if n.get('@id') == DOMAIN + '/#organization'))
        link_failures = []
        for a in doc.select('a[href]'):
            full = urljoin(canonical, a['href'])
            parsed = urlsplit(full)
            if parsed.netloc == urlsplit(DOMAIN).netloc:
                dest, anchor = resolve(full)
                all_links.add(full)
                if not (ROOT / dest).is_file():
                    link_failures.append({'href': a['href'], 'reason': 'missing file'})
                elif anchor and dest.endswith('.html') and not soup(dest).find(id=anchor):
                    link_failures.append({'href': a['href'], 'reason': 'missing anchor'})
        check(label + 'all internal links and fragments resolve', not link_failures, link_failures[:12])
        for tag in doc.select('img[src], script[src], link[rel="stylesheet"][href]'):
            full = urljoin(canonical, tag.get('src') or tag.get('href'))
            if urlsplit(full).netloc == urlsplit(DOMAIN).netloc:
                dest, _ = resolve(full)
                asset_paths.add(dest)
                check(label + 'local asset ' + dest, (ROOT / dest).is_file())
            if tag.name == 'img' and '/official-learning/' in tag['src']:
                check(label + 'official image dimensions and ALT', bool(tag.get('alt', '').strip()) and int(tag.get('width', 0)) > 0 and int(tag.get('height', 0)) > 0)
                check(label + 'image not hidden', not tag.has_attr('hidden') and 'display:none' not in tag.get('style', '').replace(' ', ''))
        if path != '학습코칭/index.html':
            original = BeautifulSoup(base(path), 'html.parser', from_encoding='utf-8')
            check(label + 'canonical preserved', canonical == original.select_one('link[rel="canonical"]')['href'])
            current_og = doc.select_one('meta[property="og:image"]')
            original_og = original.select_one('meta[property="og:image"]')
            check(label + 'OG image preserved', (current_og.get('content') if current_og else None) == (original_og.get('content') if original_og else None))
            check(label + 'verification tags preserved', [(x['name'], x['content']) for x in doc.select('meta[name$="site-verification"]')] == [(x['name'], x['content']) for x in original.select('meta[name$="site-verification"]')])
            check(label + 'contact button destinations preserved', [x['href'] for x in doc.select('.floating-actions a')] == [x['href'] for x in original.select('.floating-actions a')])
            if mode in ('hub', 'region'):
                check(label + 'H1 and title preserved', original.h1.get_text(' ', strip=True) == doc.h1.get_text(' ', strip=True) and original.title.get_text(' ', strip=True) == title)
                old_faq = faq(original)
                check(label + 'original visible FAQ retained', all(q in displayed for q in old_faq))
                for selector in ('.subject-directory', '.subject-category-section', '.all-town-directory', '.studio-hub-content'):
                    old = original.select_one(selector)
                    now = doc.select_one(selector)
                    if old:
                        expected = old.decode_contents()
                        if mode == 'region' or path == '전국학원/index.html':
                            expected = (expected.replace('시군구를', '지역 묶음을').replace('시군구와', '지역 묶음과')
                                        .replace('시군구가', '지역 묶음이').replace('시군구로', '지역 묶음으로')
                                        .replace('시군구', '지역 묶음'))
                        check(label + 'preserve ' + selector, bool(now) and expected == now.decode_contents())
            if mode == 'hub':
                original_centers = [(n.get('@id'), n.get('name'), n.get('address'), n.get('identifier')) for tag in original.select('script[type="application/ld+json"]') for n in json.loads(tag.string)['@graph'] if '#center-' in n.get('@id', '')]
                current_centers = [(n.get('@id'), n.get('name'), n.get('address'), n.get('identifier')) for n in ld_nodes if '#center-' in n.get('@id', '')]
                check(label + 'real center entities preserved', original_centers == current_centers)
        pages.append({'path': path, 'mode': mode, 'title': title, 'h1': doc.h1.get_text(' ', strip=True), 'characters': len(doc.main.get_text(' ', strip=True)), 'faqs': len(displayed), 'internalLinks': sum(urlsplit(urljoin(canonical, a['href'])).netloc == urlsplit(DOMAIN).netloc for a in doc.main.select('a[href]'))})
    check('All overview titles distinct', len(titles) == len(set(titles)))
    check('All descriptions distinct', len(descriptions) == len(set(descriptions)))
    check('111 visible FAQ answers verified', total_faq == 111, total_faq)
    for anchor in ('exam', 'planner', 'wrong', 'parents'):
        check('Preserve old learning guide anchor: ' + anchor, bool(soup('학습가이드/index.html').find(id=anchor)))
    manifest = json.loads((DATA / 'sources.json').read_text('utf-8-sig'))
    for row in manifest['assets']:
        path = 'assets/official-learning/' + row['file']
        check('Original image hash: ' + row['file'], hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == row['sha256'])
        check('Image used: ' + row['file'], path in asset_paths)
    check('Official source recheck passed', json.loads((REPORT / 'official-source-check.json').read_text('utf-8'))['passed'])
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    oldmap, newmap = ET.fromstring(base('sitemap.xml')), ET.parse(ROOT / 'sitemap.xml').getroot()
    oldurls = [x.findtext(ns + 'loc') for x in oldmap]
    newurls = [x.findtext(ns + 'loc') for x in newmap]
    check('Sitemap old URLs/order preserved; new pillar only appended', newurls[:-1] == oldurls and unquote(newurls[-1]) == DOMAIN + '/학습코칭/' and len(newurls) == 7152 and len(set(newurls)) == 7152)
    oldrss, newrss = ET.fromstring(base('rss.xml')), ET.parse(ROOT / 'rss.xml').getroot()
    oldlinks = [x.findtext('link') for x in oldrss.findall('./channel/item')]
    newlinks = [x.findtext('link') for x in newrss.findall('./channel/item')]
    check('RSS old items/order preserved; new pillar appended', newlinks[:-1] == oldlinks and len(newlinks) == 12 and unquote(newlinks[-1]) == DOMAIN + '/학습코칭/')
    metadata = {unquote(x['url']): x for x in GEN['targets']}
    for item in newrss.findall('./channel/item'):
        row = metadata.get(unquote(item.findtext('link')))
        if row:
            check('RSS title/description ' + row['path'], item.findtext('title') == row['title'] and item.findtext('description') == row['description'])
    http_rows = []
    if run_http:
        files = sorted(targets | asset_paths | {'sitemap.xml', 'rss.xml', 'llms.txt', 'robots.txt'})
        def request(path):
            url = 'http://127.0.0.1:8798/' + quote(path.removesuffix('index.html'), safe='/')
            try:
                with urlopen(url, timeout=20) as response:
                    content, status = response.read(), response.status
                return {'path': path, 'status': status, 'matchesLocal': content == (ROOT / path).read_bytes(), 'passed': status == 200 and content == (ROOT / path).read_bytes()}
            except Exception as error:
                return {'path': path, 'passed': False, 'error': str(error)}
        with ThreadPoolExecutor(max_workers=4) as pool:
            http_rows = list(pool.map(request, files))
        for row in http_rows:
            check('Local HTTP ' + row['path'], row['passed'], row)
    result = {'baseline': BASE, 'pages': pages, 'totalPages': len(pages), 'preservedHtml': 7125, 'visibleFaq': total_faq, 'uniqueInternalDestinations': len(all_links), 'checks': len(checks), 'passed': len(checks) - len(errors), 'failures': errors, 'details': checks, 'http': http_rows}
    (REPORT / 'static-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('pages', 'details', 'http')}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == '__main__':
    main()
