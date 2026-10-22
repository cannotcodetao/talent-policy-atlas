import json, re
d = json.load(open("talent-data.json", encoding="utf-8"))
_AMT_WAN=re.compile(r'(\d+(?:\.\d+)?)\s*万'); _AMT_YUAN=re.compile(r'(\d+(?:\.\d+)?)\s*元')
_MONTHLY=re.compile(r'(\d+(?:\.\d+)?)\s*元\s*/\s*月'); _AMT_YUAN_YEAR=re.compile(r'(\d+(?:\.\d+)?)\s*元\s*/\s*年')
_CLAUSE_SEP=re.compile(r'[，,；;：:\n、/]')
def _clauses(t): return [c for c in _CLAUSE_SEP.split(str(t)) if c.strip()]
GRAD_NEG=['购房','房票','公积金','住房贷款','高层次','住房补贴','共有产权','按揭','还款']
WEL_POS=['租房','租赁','房租','居住','安家','租金']; WEL_NEG=['贷款','公积金','公积','购房','房票','共有产权','产权']
ST_NEG=['贷款','借款','贴息','信贷','大赛','项目资助','基金','创投','团队','孵化器','孵化','众创','科技','风投']; ST_POS=['补贴','资助','奖励','场租','房租','安家','生活','扶持','金']
def scan_wan(cs,neg=(),pos=None):
    best=0.0;hit=None
    for cl in cs:
        if neg and any(k in cl for k in neg):continue
        if pos and not any(k in cl for k in pos):continue
        for m in _AMT_WAN.finditer(cl):
            v=float(m.group(1))
            if v>best:best=v;hit=cl
    return best,hit
def scan_yuan(cs,neg=(),pos=None):
    best=0.0;hit=None
    for cl in cs:
        if neg and any(k in cl for k in neg):continue
        if pos and not any(k in cl for k in pos):continue
        for m in _AMT_YUAN.finditer(cl):
            v=float(m.group(1))/10000.0
            if v>best:best=v;hit=cl
    return best,hit
def wel(text):
    cs=_clauses(text);best=0.0
    for cl in cs:
        if any(k in cl for k in WEL_NEG):continue
        if not (any(k in cl for k in WEL_POS) or '租' in cl or '居住' in cl):continue
        for m in _MONTHLY.finditer(cl): best=max(best,float(m.group(1))*12/10000.0)
        for m in _AMT_YUAN_YEAR.finditer(cl): best=max(best,float(m.group(1))/10000.0)
        has_month='月' in cl
        for m in _AMT_YUAN.finditer(cl):
            best=max(best, float(m.group(1))*12/10000.0 if has_month else float(m.group(1))/10000.0)
        for m in _AMT_WAN.finditer(cl): best=max(best,float(m.group(1)))
    return round(best,3)
def its(c,dim):
    for p in ['zhejiang','guangdong']:
        if c in d[p]: return d[p][c]['dimensions'].get(dim,{}).get('items',[])
    return []
def sc(c,dim):
    best=0.0;src=''
    if dim=='grad_subsidy':
        for it in its(c,dim):
            for f in ('cash','house_voucher'):
                b,h=scan_wan(_clauses(it.get(f,'')),neg=GRAD_NEG)
                if b>best:best=b;src=h
    elif dim=='anju_subsidy':
        for it in its(c,dim):
            b,h=scan_wan(_clauses(it.get('discount','')))
            if b>best:best=b;src=h
    elif dim=='welfare':
        for it in its(c,dim):
            b=wel(it.get('detail',''))
            if b>best:best=b;src=it.get('detail','')[:60]
    elif dim=='startup':
        for it in its(c,dim):
            cs=_clauses(it.get('detail','') or it.get('type',''))
            b,h=scan_wan(cs,neg=ST_NEG,pos=ST_POS);b2,h2=scan_yuan(cs,neg=ST_NEG,pos=ST_POS)
            if b2>b:b=b2;h=h2
            if b>best:best=b;src=h
    return round(best,3),src
cities=[c for p in ['zhejiang','guangdong'] for c in d[p]]
for dim in ['grad_subsidy','anju_subsidy','welfare','startup']:
    res=sorted(((sc(c,dim)[0],c) for c in cities),reverse=True)
    print(f"\n##### {dim} TOP8 #####")
    for v,c in res[:8]:
        s,src=sc(c,dim); print(f"  {c:>3} {v:>8}  <- {str(src)[:66]}")
print("\n##### anju_subsidy discount contamination scan #####")
flagged=0
for c in cities:
    for it in its(c,'anju_subsidy'):
        disc=it.get('discount','')
        if re.search(r'贷款|公积金|贴息',disc) and not re.search(r'购房|房票|补贴',disc):
            print(f"  [!] {c}: {disc[:80]}"); flagged+=1
print("  flagged =",flagged)
