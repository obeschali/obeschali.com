import json,re,sys
CATS={'politika','ekonomika','mir','tekhnika','infra','obshchestvo','sport'};KINDS={'promise','forecast','denial','irony'}
D=json.load(open('stories.json',encoding='utf-8'));ids=set();bad=0
def err(i,m):
    global bad;bad+=1;print(f'[{i}] {m}')
dt=re.compile(r'^\d{4}-\d{2}(-\d{2})?$')
for s in D:
    i=s.get('id','?')
    if i in ids:err(i,'дубль id')
    ids.add(i)
    if s.get('cat') not in CATS:err(i,'cat')
    if s.get('kind') not in KINDS:err(i,'kind')
    if not 1<=s.get('w',0)<=5:err(i,'w 1..5')
    for k in('who','role','quote','head','body'):
        if not s.get(k):err(i,'нет '+k)
    for k in('date','odate'):
        if not dt.match(s.get(k,'')):err(i,'формат '+k)
    for k in('qsrc','osrc'):
        if not s.get(k) or not all(str(x.get('u','')).startswith('https://') and x.get('t') for x in s[k]):err(i,'источники '+k)
print(len(D),'историй,',bad,'ошибок');sys.exit(bad>0)
