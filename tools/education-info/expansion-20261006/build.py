from pathlib import Path
from html import escape
from concurrent.futures import ThreadPoolExecutor
import json,re,sys,importlib.util,hashlib,shutil,os,time,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
RELEASE=Path(r'C:/Users/1992k/Desktop/CodexData/worktrees/publish21-new-academy-20260925')
OUT=Path(r'C:/Users/1992k/Desktop/CodexData/outputs/professional-education-expansion-20261006')
TOOL=Path(__file__).parent;DATE='2026-10-06'
sys.path.insert(0,str(ROOT/'tools/education-info'))
spec=importlib.util.spec_from_file_location('original_education_builder',ROOT/'tools/education-info/build.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
old=base.ARTICLES
old_manifest=json.loads((ROOT/'tools/education-info/manifest.json').read_text(encoding='utf-8'))
for a,m in zip(old,old_manifest['articles']):a['path']=m['path'];a['images']=m['images']
space={}
for name in ['catalog.py','catalog2.py','catalog3.py']:exec(compile((TOOL/name).read_text(encoding='utf-8'),str(TOOL/name),'exec'),space)
articles=space['ARTICLES'];assert len(articles)==30
selection=json.loads((OUT/'selection.json').read_text(encoding='utf-8'))
old_folders={r['folder'] for r in json.loads((ROOT/'tools/education-info/selection.json').read_text(encoding='utf-8'))['selected']}
assert not old_folders.intersection(r['folder'] for r in selection['records'])
captions='노트에 학습 내용을 적는 손|교재와 태블릿을 함께 보는 모습|교재와 지구본을 살펴보는 학생|펼친 책에 필기하는 모습|수식이 있는 칠판 앞에서 설명하는 모습|어른과 어린이가 교재를 두고 대화하는 모습|펼친 책과 연필|교실에서 교재를 읽는 학생들|교사와 함께 교재를 살펴보는 학생들|책을 들고 모여 있는 학생들|책상에서 필기하는 학생|책상 앞에서 교재를 보는 학생|헤드폰과 노트북으로 공부하는 학생|영어 문장을 형광펜으로 표시하는 모습|책상 앞에서 생각하는 학생|교실에서 종이에 쓰는 학생|교재와 학습 도구를 정리한 책상|책상에서 교재를 보며 생각하는 학생|태블릿과 교재를 함께 보는 학생|교재를 펼치고 대화하는 두 사람|노트북 앞에서 함께 학습하는 모습|책과 가방을 들고 서 있는 학생들|교재를 두고 이야기하는 학생들|교복을 입고 함께 서 있는 학생들|태블릿 화면을 보며 필기하는 모습|책 위에 놓인 알파벳 학습 도구|교실에서 함께 자료를 살펴보는 학생들|펼친 책에 글을 쓰는 학생|교재와 지구본을 보는 학생|교재와 태블릿을 정리해 둔 책상|교재와 노트북으로 함께 공부하는 모습|학생의 교재를 함께 살펴보는 교사|온라인 설명 화면과 필기 도구|어른과 어린이가 함께 앉아 있는 모습|학습 자료를 들고 있는 두 사람|교사와 학생이 대화하는 모습|교실에서 노트에 쓰는 학생들|책과 가방을 들고 서 있는 학생들|교실에서 교재를 보는 학생|수학 시험 종이와 연필|식탁에서 식사하는 어린이|책과 시계가 놓인 책상|학습 자료를 들고 있는 학생과 교사|모여 앉아 학습 내용을 적는 손|교재에 필기하는 학생|종이에 연필로 쓰는 학생|태블릿의 설명을 보는 학생|책상에서 교재를 보는 학생|교실에서 교재와 노트를 보는 학생|학습 내용을 종이에 적는 손|메모와 교재를 확인하는 학생|교재와 태블릿을 보는 모습|책상에 앉아 생각하는 학생|펼친 책 앞에서 생각하는 학생|교실에서 노트에 쓰는 학생|노트북과 시계가 놓인 책상|교실 책상에서 공부하는 학생|교실에서 교재를 읽는 학생들|교복을 입고 서 있는 학생들|교재를 함께 보는 어린이들|책상에서 대화하는 교사와 학생|답안지에 연필로 표시하는 모습|국어 시험 자료와 답안지|책장에서 책을 고르는 어린이|화면 앞에서 설명 자료를 보여 주는 모습|엄지를 들어 보이는 학생들|연필 지우개로 종이를 지우는 모습|책상에서 교재를 보는 학생|교재에 필기하는 손|수학 풀이 종이와 자|책상에서 생각하는 학생들|교재와 노트에 학습 내용을 쓰는 손|책과 필기구가 놓인 책상|책을 들고 함께 모여 있는 학생들|교재에 필기하는 학생|어른과 어린이가 손을 잡는 모습|교재를 펼치고 생각하는 학생|교재를 함께 보는 두 사람|책 더미 앞에서 쉬는 학생|환경 주제의 종이 학습 도구|태블릿과 교재를 함께 놓은 책상|책 더미 옆에서 쉬는 학생|책상에서 연필을 들고 있는 학생|책과 가방을 들고 서 있는 학생들|책상에서 교재와 노트북으로 공부하는 모습|도형 도구를 들고 칠판 앞에 있는 학생들|교실에서 학습 내용을 쓰는 손|교재 앞에서 설명하는 학생|학교에서 대화하는 학생들|교재와 노트북으로 함께 학습하는 모습'.split('|')
assert len(captions)==90
for a,r in zip(articles,selection['records']):
    assert a['sourceId']==r['id'];a['path']='/교육정보/'+a['slug']+'/'
    a['sourceFolder']=r['folder'];a['guide']='숙제량조절' if a['sourceId']==23 else a['guide']
    assert a['guide'] in base.GUIDE_BY_SLUG
    assert len(a['description'])<=80 and a['description'].endswith('.')
    a['images']=[]
    for i,im in enumerate(r['images']):
        assert hashlib.sha256(Path(im['path']).read_bytes()).hexdigest()==im['sha256']
        src='/assets/education-info/'+a['slug']+'-'+str(i+1)+Path(im['path']).suffix.lower()
        a['images'].append({**im,'src':src,'alt':captions[(r['id']-1)*3+i]})
    assert len({im['sha256'] for im in a['images']})==3
base.SOURCES.update({
 'movement':['NHS · 편안한 범위의 유연성 운동','https://www.nhs.uk/live-well/exercise/flexibility-exercises/','일반적인 움직임 참고 자료이며 치료·진단 안내가 아님'],
 'tasks':['Google Tasks · 기능과 이용 조건','https://support.google.com/tasks/answer/7675772?hl=ko','할 일·하위 할 일·마감과 학교 계정 조건'],
 'wellbeing':['Android · 디지털 웰빙','https://support.google.com/android/answer/9346420?hl=ko','앱 사용 시간·제한과 기기·계정 조건'],
 'listening':['British Council · 수준별 듣기 연습','https://learnenglish.britishcouncil.org/free-resources/listening','수준에 맞는 음성과 이해 확인 활동'],
 'exam':['한국교육과정평가원 · 대학수학능력시험','https://www.suneung.re.kr/','응시 학년도 공식 안내와 공개 자료 확인']})
base.DATE=DATE;base.ARTICLES=articles
home=(RELEASE/'index.html').read_text(encoding='utf-8-sig')
base.HEADER=re.search(r'<header\b[\s\S]*?</header>',home).group();base.FOOTER=re.search(r'<footer\b[\s\S]*?</footer>',home).group()
base.ROOT=ROOT
for a in articles:
    for im in a['images']:
        dest=ROOT/im['src'].lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(im['path'],dest)
base.article_pages()
# 실제 지점 사진으로 오인하지 않도록 참고 사진의 용도를 표시한다.
for a in articles:
    p=ROOT/a['path'].lstrip('/')/'index.html';s=p.read_text(encoding='utf-8')
    s=s.replace('<figcaption>','<figcaption>학습 상황 참고 이미지 · ')
    s=re.sub(r'(<a\b[^>]*data-education-menu[^>]*)(>)',lambda m:m[1]+' class="active" aria-current="page"'+m[2],s)
    p.write_text(s,encoding='utf-8')
base.ARTICLES=old
combined=[{**a,'format':'교육정보'} for a in articles]+base.all_cards()
new_cards=''.join(base.card(a) for a in combined)
hub=ROOT/'교육정보/index.html';s=hub.read_bytes().decode('utf-8-sig')
s,n=re.subn(r'(<div class="ei-grid">)[\s\S]*?(</div><nav class="ei-pagination")',lambda m:m[1]+new_cards+m[2],s);assert n==1
s=s.replace('30<span>교육정보','60<span>교육정보').replace('교육정보 30개','교육정보 60개')
desc='시험·학습 습관·과목별 공부·학부모 상담의 교육정보 60개와 실천 가이드 42개를 찾아보고 동네·지점 안내로 연결합니다.'
for pattern in [r'(<meta name="description" content=")[^"]*(")',r'(<meta property="og:description" content=")[^"]*(")',r'(<meta name="twitter:description" content=")[^"]*(")']:
    s,n=re.subn(pattern,lambda m:m[1]+escape(desc,quote=True)+m[2],s);assert n==1
def graph_update(m):
    d=json.loads(m[1])
    for v in d['@graph']:
        if v['@type']=='CollectionPage':v['description']=desc;v['dateModified']=DATE
        if v['@type']=='ItemList':v['numberOfItems']=len(combined);v['itemListElement']=[{'@type':'ListItem','position':i+1,'name':a['title'],'url':base.absolute(a['path'])} for i,a in enumerate(combined)]
    return '<script type="application/ld+json">'+base.js(d)+'</script>'
s,n=re.subn(r'<script type="application/ld\+json">([\s\S]*?)</script>',graph_update,s);assert n==1
featured=''.join(f'<a class="ei-feature" data-ei-context-link href="{a["path"]}"><span>{a["category"]}</span><strong>{escape(a["title"])}</strong><span>읽어보기 →</span></a>' for a in [articles[24],articles[14],articles[9]])
s,n=re.subn(r'(<div class="ei-featured">)[\s\S]*?(</div></section>)',lambda m:m[1]+featured+m[2],s);assert n==1
hub.write_bytes(s.encode('utf-8'))
base.DESCRIPTION['/교육정보']=desc
# 기존 표시된 추천 영역 안에서 링크만 갱신한다. 주변 본문과 줄바꿈은 보존한다.
pattern=re.compile(rb'<!-- education-entry:start -->[\s\S]*?<!-- education-entry:end -->')
def recommended(rel):
    if '수학' in rel:return [6,10]
    if '영어' in rel:return [9,28]
    if '국어' in rel:return [17,20]
    if '초등' in rel:return [22,19]
    if '고등' in rel or any(v in rel for v in ['고1','고2','고3']):return [21,7]
    if rel=='index.html':return [25,15]
    pool=[1,2,3,4,5,8,11,12,13,14,16,18,24,26,27,29,30]
    i=int(hashlib.sha256(rel.encode()).hexdigest()[:8],16)%len(pool)
    return [pool[i],pool[(i+5)%len(pool)]]
def overlay(root,rel):
    p=root/rel;raw=p.read_bytes();m=pattern.search(raw)
    if not m:return None
    fragment=m[0].decode('utf-8');query=re.search(r'class="education-all" href="/교육정보/([^"]*)"',fragment)[1]
    ids=recommended(rel);existing=re.findall(r'<a href="([^"]*)">([\s\S]*?)</a>',re.search(r'<div class="education-entry-links">([\s\S]*?)</div>',fragment)[1])
    old_link=existing[-1]
    links=''.join(f'<a href="{articles[i-1]["path"]}{query}">{escape(articles[i-1]["title"])} <span aria-hidden="true">→</span></a>' for i in ids)+f'<a href="{old_link[0]}">{old_link[1]}</a>'
    new,n=re.subn(r'(<div class="education-entry-links">)[\s\S]*?(</div>)',lambda v:v[1]+links+v[2],fragment);assert n==1
    changed=raw[:m.start()]+new.encode()+raw[m.end():]
    assert pattern.sub(b'',changed)==pattern.sub(b'',raw)
    # 일부 Windows 읽기 프로세스의 일시적인 파일 공유 충돌을 피하는 원자적 저장.
    saved=True
    if changed!=raw:
        temp=p.with_name('index.education-expansion.tmp')
        temp.write_bytes(changed)
        for attempt in range(5):
            try:os.replace(temp,p);break
            except OSError:
                if attempt==4:
                    # 원본 파일을 점유한 프로세스가 있는 경우 변경 계획을 별도 보관.
                    planned=OUT/'source-pending'/rel;planned.parent.mkdir(parents=True,exist_ok=True);planned.write_bytes(changed)
                    saved=False
                    temp.unlink()
                    break
                time.sleep(.2)
    return {'path':rel,'newSourceIds':ids,'beforeSha256':baseline['source']['html'][rel],'afterSha256':hashlib.sha256(changed).hexdigest(),'outsideFragmentPreserved':True,'saved':saved}
baseline=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'))
rels=[r for r in baseline['source']['html'] if r=='index.html' or r.startswith(('지점안내/','전국학원/','과목별학원/'))]
with ThreadPoolExecutor(max_workers=12) as pool:links=[v for v in pool.map(lambda r:overlay(ROOT,r),rels) if v]
(OUT/'source-overlays.json').write_text(json.dumps(links,ensure_ascii=False,indent=2),encoding='utf-8')
registry=json.loads((ROOT/'seo-descriptions.json').read_text(encoding='utf-8-sig'))
for key,d in base.DESCRIPTION.items():registry['pages'][key]={'description':d,'sources':[d]}
(ROOT/'seo-descriptions.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns)
site=ET.parse(ROOT/'sitemap.xml');site_root=site.getroot()
known={v.find('{'+ns+'}loc').text for v in site_root}
for a in articles:
    if base.absolute(a['path']) in known:continue
    entry=ET.SubElement(site_root,'{'+ns+'}url');ET.SubElement(entry,'{'+ns+'}loc').text=base.absolute(a['path']);ET.SubElement(entry,'{'+ns+'}lastmod').text=DATE
for entry in site_root:
    if entry.find('{'+ns+'}loc').text==base.absolute('/교육정보/'):entry.find('{'+ns+'}lastmod').text=DATE
assert len(site_root)==9988
ET.indent(site,space='  ');site.write(ROOT/'sitemap.xml',encoding='utf-8',xml_declaration=True)
rss=ET.parse(ROOT/'rss.xml');channel=rss.getroot().find('channel');stamp='Tue, 06 Oct 2026 00:00:00 +0900';channel.find('lastBuildDate').text=stamp
known_rss={v.findtext('link') for v in channel.findall('item')}
for a in articles:
    if base.absolute(a['path']) in known_rss:continue
    item=ET.Element('item')
    for key,value in [('title',a['title']),('link',base.absolute(a['path'])),('guid',base.absolute(a['path'])),('description',a['description']),('pubDate',stamp),('category',a['category'])]:
        tag=ET.SubElement(item,key);tag.text=value
        if key=='guid':tag.set('isPermaLink','true')
    channel.insert(0,item)
ET.indent(rss,space='  ');rss.write(ROOT/'rss.xml',encoding='utf-8',xml_declaration=True)
manifest={'date':DATE,'selectionSeed':selection['seed'],'newPages':[a['path'] for a in articles],'hub':'/교육정보/','articles':articles,'linkedPages':len(links),'totalEducationArticles':60,'totalDirectoryCards':102,'sources':base.SOURCES,'privateSourcesIncluded':False}
(TOOL/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'newArticles':30,'photos':90,'directoryCards':102,'linkedPages':len(links),'sitemapPages':9988},ensure_ascii=False))
