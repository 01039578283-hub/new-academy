"""Verify a committed 전문수업.com release against the real public domain.

Read-only HTTP requests. Reports contain statuses and hashes, never bodies or
credentials. This verifier is independent of the pre-commit baseline audit.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://xn--z92bu9jx8cwzc.com'
REPORT_DIR = 'tools/reports/learning-upgrade'


def blob(commit, path):
    return subprocess.run(['git', 'show', f'{commit}:{path}'], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True).stdout


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []
        self.canonicals = []
        self.og_urls = []
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('img', 'script') and attrs.get('src'):
            self.assets.append(attrs['src'])
        if tag == 'link':
            rel = attrs.get('rel', '').lower()
            if 'stylesheet' in rel or 'icon' in rel:
                self.assets.append(attrs.get('href', ''))
            if rel == 'canonical':
                self.canonicals.append(attrs.get('href', ''))
        if tag == 'meta':
            if attrs.get('name', '').lower() in ('robots', 'googlebot', 'yeti'):
                self.noindex |= 'noindex' in attrs.get('content', '').lower()
            if attrs.get('property', '').lower() == 'og:url':
                self.og_urls.append(attrs.get('content', ''))


def url_key(value):
    parsed = urlsplit(value)
    return (parsed.scheme, parsed.hostname, unquote(parsed.path), parsed.query)


def digest(content):
    return hashlib.sha256(content).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    commit = subprocess.check_output(['git', 'rev-parse', args.commit], cwd=ROOT).decode().strip()
    generation = json.loads(blob(commit, f'{REPORT_DIR}/generation.json'))
    paths = {row['path']: 'updated-page' for row in generation['targets']}
    for row in generation['targets']:
        page = Page()
        page.feed(blob(commit, row['path']).decode('utf-8-sig'))
        for value in page.assets:
            parsed = urlsplit(urljoin(row['url'], value))
            if parsed.hostname == urlsplit(DOMAIN).hostname:
                path = unquote(parsed.path).lstrip('/')
                if path:
                    paths.setdefault(path, 'page-asset')
    for path in ('sitemap.xml', 'rss.xml', 'llms.txt', 'robots.txt'):
        paths[path] = 'discovery'
    for path in ('과목별학원/고1영어학원/명일동/index.html',
                 '전국학원/서울/강동구/명일동/index.html',
                 '전국학원/서울/강동구/명일동/중1수학학원/index.html',
                 '전국학원/서울/강동구/명일동/초3영어학원/index.html',
                 '전국학원/서울/강동구/명일동/초6수학학원/index.html'):
        assert blob(commit, path) == blob(generation['baseline'], path), path
        paths[path] = 'unchanged-regression'

    jobs = []
    for path, kind in paths.items():
        route = path[:-10] if path.endswith('index.html') else path
        jobs.append((path, kind, DOMAIN + '/' + quote(route, safe='/'), blob(commit, path)))

    def verify(job):
        path, kind, url, expected = job
        result = {'path': path, 'kind': kind, 'url': url}
        try:
            request = Request(url, headers={'User-Agent': 'WawaReleaseVerification/1.0',
                                           'Cache-Control': 'no-cache', 'Accept-Encoding': 'identity'})
            with urlopen(request, timeout=40) as response:
                content = response.read()
                result.update(status=response.status, finalUrl=response.url,
                              bytes=len(content), cache=response.headers.get('x-vercel-cache'),
                              contentType=response.headers.get('content-type'),
                              robotsHeader=response.headers.get('x-robots-tag', ''))
            if Path(path).suffix in ('.html', '.txt', '.xml', '.js', '.css', '.svg'):
                content = content.replace(b'\r\n', b'\n')
                expected = expected.replace(b'\r\n', b'\n')
            result.update(expectedSha256=digest(expected), actualSha256=digest(content),
                          passed=result['status'] == 200 and content == expected
                          and urlsplit(result['finalUrl']).hostname == urlsplit(DOMAIN).hostname)
            if path.endswith('.html'):
                page = Page()
                page.feed(content.decode('utf-8-sig'))
                result.update(canonicals=page.canonicals, ogUrls=page.og_urls,
                              noindex=page.noindex or 'noindex' in result['robotsHeader'].lower())
                result['passed'] &= (not result['noindex'] and len(page.canonicals) == 1
                                     and len(page.og_urls) == 1
                                     and url_key(page.canonicals[0]) == url_key(url)
                                     and url_key(page.og_urls[0]) == url_key(url))
            if path == 'sitemap.xml':
                result['urls'] = len(ET.fromstring(content).findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'))
                result['passed'] &= result['urls'] == 7152
            if path == 'rss.xml':
                result['items'] = len(ET.fromstring(content).findall('./channel/item'))
                result['passed'] &= result['items'] == 12
        except Exception as error:
            result.update(passed=False, error=f'{type(error).__name__}: {error}')
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(verify, jobs))
    private = []
    for path in ('tools/LEARNING_UPGRADE_HANDOFF_2026-09-12.md',
                 'tools/data/learning-upgrade/home.html', '.env.local', '.git/config'):
        try:
            request = Request(DOMAIN + '/' + quote(path, safe='/'), method='HEAD')
            with urlopen(request, timeout=25) as response:
                status = response.status
        except HTTPError as error:
            status = error.code
        except Exception as error:
            status = type(error).__name__
        private.append({'path': path, 'status': status, 'passed': status in (403, 404)})
    failed = [row for row in results + private if not row['passed']]
    report = {'domain': DOMAIN, 'commit': commit, 'verifiedAtUtc': datetime.now(timezone.utc).isoformat(),
              'updatedPages': len(generation['targets']), 'publicResources': len(results),
              'privateChecks': len(private), 'passed': not failed, 'failed': failed,
              'resources': results, 'private': private}
    output = ROOT / REPORT_DIR / 'production-verification.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key not in ('resources', 'private')},
                     ensure_ascii=False, indent=2))
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
