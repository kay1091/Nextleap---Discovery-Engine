"""Precision audit of the FULL-corpus coder output: random sample (seed 7) of 20 coded positives per opportunity area. The analyst (me, LLM) judges each
(1 = the text genuinely raises this area's issue; 0 = false positive).  Labels in labels/audit_labels.txt  (AREA|doc_id|0/1).  
Usage: sample -> python 07c_audit_sample.py sample ; score -> python 07c_audit_sample.py score"""
import sys; sys.path.insert(0,"scripts")
import pandas as pd, numpy as np, glob
from areas import AREAS
mode=sys.argv[1]
d=pd.read_csv("data/processed/corpus_final.csv",low_memory=False); d["codes"]=d.codes.fillna("")
if mode=="sample":
    rows=[]
    for a,v in AREAS.items():
        if a=="A5":   # A5 uses the regex-only IA_ALERTS rule (the AND-variant ML+regex coder kept only ~10 docs; revised after first audit)
            m=d.codes_regex_only.fillna("").str.contains("IA_ALERTS"); s=d[m].sample(20,random_state=3)
        else:
            m=d.codes.apply(lambda c:any(x in c.split(",") for x in v["codes"])); s=d[m].sample(min(20,int(m.sum())),random_state=7)
        for _,r in s.iterrows(): rows.append(dict(area=a,doc_id=r.doc_id,source=r.source,codes=r.codes,text=r.text))
    pd.DataFrame(rows).to_csv("data/processed/audit_sample.csv",index=False); print(len(rows))
else:
    L=[l.strip().split("|") for f in glob.glob("labels/audit_labels*.txt") for l in open(f) if l.strip()]
    A=pd.DataFrame(L,columns=["area","doc_id","ok"]); A["ok"]=A.ok.astype(int)
    S=pd.read_csv("data/processed/audit_sample.csv"); assert set(S.doc_id)==set(A.doc_id),(len(S),len(A))
    P=A.groupby("area").ok.agg(audit_n="size",audit_tp="sum"); P["audit_precision"]=P.audit_tp/P.audit_n
    # Wilson 95% CI
    z=1.96; p=P.audit_precision; n=P.audit_n; den=1+z*z/n
    P["ci_lo"]=((p+z*z/(2*n))-z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)))/den; P["ci_hi"]=((p+z*z/(2*n))+z*np.sqrt(p*(1-p)/n+z*z/(4*n*n)))/den
    P=P.reset_index(); P.to_csv("outputs/audit_precision_by_area.csv",index=False); print(P.round(2))
