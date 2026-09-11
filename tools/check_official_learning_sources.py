"""Verify the requested official source pages and unedited source image bytes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'tools/data/learning-upgrade/sources.json').read_text('utf-8-sig'))
output = ROOT / 'tools/reports/learning-upgrade'
output.mkdir(parents=True, exist_ok=True)


def get(url):
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0 WawaSiteSourceReview'}), timeout=40) as response:
        assert response.status == 200
        return response.read()


pages = []
for i, url in enumerate(manifest['pages']):
    content = get(url)
    (output / f'official-source-{i + 1}.html').write_bytes(content)
    pages.append({'url': url, 'status': 200, 'sha256': hashlib.sha256(content).hexdigest(), 'text': content.decode('utf-8')})
all_source = '\n'.join(page['text'] for page in pages)


def verify(row):
    local = (ROOT / 'assets/official-learning' / row['file']).read_bytes()
    result = {'file': row['file'], 'source': row['source'], 'localHashMatches': hashlib.sha256(local).hexdigest() == row['sha256']}
    if row['file'].startswith('video-'):
        vid = parse_qs(urlsplit(row['source']).query)['v'][0]
        result.update(linkedFromOfficialPage=vid in all_source, thumbnailBytes=len(local))
        result['passed'] = result['localHashMatches'] and result['linkedFromOfficialPage']
    else:
        remote = get(row['source'])
        result.update(linkedFromOfficialPage=urlsplit(row['source']).path in all_source, remoteSha256=hashlib.sha256(remote).hexdigest(), originalBytesMatch=remote == local)
        result['passed'] = result['localHashMatches'] and result['linkedFromOfficialPage'] and result['originalBytesMatch']
    return result


with ThreadPoolExecutor(max_workers=3) as pool:
    assets = list(pool.map(verify, manifest['assets']))
for page in pages:
    del page['text']
report = {'verifiedAtUtc': datetime.now(timezone.utc).isoformat(), 'pages': pages, 'assets': assets, 'passed': all(row['passed'] for row in assets)}
(output / 'official-source-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'pages': len(pages), 'assets': len(assets), 'passed': report['passed'], 'failures': [row for row in assets if not row['passed']]}, ensure_ascii=False))
raise SystemExit(0 if report['passed'] else 1)
