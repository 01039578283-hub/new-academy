from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[3];TOOL=ROOT/'tools/home-content'
OUT=Path(r'C:/Users/1992k/Desktop/CodexData/outputs/professional-education-expansion-20261006')
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'));data=json.loads((TOOL/'content.json').read_text(encoding='utf-8'))
for pos,id in [(1,25),(2,15),(3,10)]:
    a=manifest['articles'][id-1];data['reading'][pos]={'name':a['title'],'description':a['description'],'audience':a['audience']+' · 새 교육정보','path':a['path'],'link':a['title'].split(',')[0]+' 읽기'}
data['date']='2026-10-06';(TOOL/'content.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
space={'__file__':str(TOOL/'build.py')};definition=(TOOL/'build.py').read_text(encoding='utf-8').split("with (ROOT / 'index.html').open")[0];exec(compile(definition,str(TOOL/'build.py'),'exec'),space)
p=ROOT/'index.html';raw=p.read_bytes();text=raw.decode('utf-8-sig');newline='\r\n' if '\r\n' in text else '\n'
marker=r'<!-- home-reading:start -->[\s\S]*?<!-- home-reading:end -->'
text,n=re.subn(marker,lambda m:space['reading']().replace('\n',newline),text);assert n==1
def update(m):
    d=json.loads(m[2])
    for v in d['@graph']:
        if v.get('@id')==space['DOMAIN']+'/#reading-directory':v.update(space['item_list']('reading-directory','시험·공부 습관·학원 선택이 고민이라면',data['reading']))
        if v.get('@type')=='WebPage' and v.get('url')==space['DOMAIN']+'/':
            v['dateModified']='2026-10-06';v['significantLink']=list(dict.fromkeys(v.get('significantLink',[])+[space['absolute'](a['path']) for a in data['reading']]))
    return m[1]+json.dumps(d,ensure_ascii=False,separators=(',',':'))+m[3]
text,n=re.subn(r'(<script\b[^>]*type="application/ld\+json"[^>]*>)([\s\S]*?)(</script>)',update,text,count=1);assert n==1
def strip(s):return re.sub(r'<script\b[^>]*type="application/ld\+json"[^>]*>[\s\S]*?</script>','',re.sub(marker,'',s))
assert strip(text)==strip(raw.decode('utf-8-sig'))
p.write_bytes(text.encode('utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'))
(OUT/'homepage-preservation.json').write_text(json.dumps({'onlyReadingFragmentAndSchemaChanged':True,'originalSectionsPreserved':True,'newRecommendedIds':[25,15,10],'beforeSha256':hashlib.sha256(raw).hexdigest(),'afterSha256':hashlib.sha256(p.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
print('Homepage reading cards and schema updated; surrounding sections preserved.')
