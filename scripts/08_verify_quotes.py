"""Hallucination / verbatim check: every quote in outputs/quotes.txt (topic|||doc_id|||quote) must (1) exist verbatim (whitespace-normalised, case-sensitive)
in the RAW source record (data/raw/*.jsonl, re-read here, not the cleaned CSV), (2) belong to the cited doc, (3) contain no handles/emails/phones/URLs.  Writes outputs/quote_verification.csv."""
import json, glob, re, pandas as pd, sys
def norm(s): return re.sub(r"\s+"," ",s or "").strip()
corpus=pd.read_csv("data/processed/corpus_all.csv",low_memory=False,usecols=["doc_id","source","raw_id","url","context","product","date","rating"]).set_index("doc_id")
raw={}
def add(src,i,t): raw[(src,str(i))]=raw.get((src,str(i)),"")+" "+norm(t)
for f in glob.glob("data/raw/*.jsonl"):
    for l in open(f):
        try: r=json.loads(l)
        except: continue
        s=r.get("source")
        if s in("playstore",): add("playstore",r["id"],r.get("text"))
        elif s=="appstore": add("appstore",r["id"],(r.get("title") or "")+" "+(r.get("text") or "")+" "+(r.get("title") or "")+". "+(r.get("text") or ""))
        else: add(s,r["id"],(r.get("title") or "")+" "+(r.get("topic_title") or "")+" "+(r.get("text") or ""))
rows=[]
for l in open("outputs/quotes.txt"):
    if not l.strip() or l.startswith("#"): continue
    t,i,q=l.rstrip("\n").split("|||"); q=norm(q).strip(".… ")
    ok_doc=i in corpus.index; src=corpus.loc[i,"source"] if ok_doc else None; rid=str(corpus.loc[i,"raw_id"]) if ok_doc else None
    rec=raw.get((src,rid),"") if ok_doc else ""
    found=bool(q) and q in rec
    pii=bool(re.search(r"@\w|\b\d{10}\b|https?://|www\.|\w+@\w+\.\w+",q))
    rows.append(dict(topic=t,doc_id=i,source=src,quote=q,doc_found=ok_doc,verbatim_in_raw=found,pii_flag=pii,url=corpus.loc[i,"url"] if ok_doc else None,context=corpus.loc[i,"context"] if ok_doc else None,product=corpus.loc[i,"product"] if ok_doc else None,date=corpus.loc[i,"date"] if ok_doc else None,rating=corpus.loc[i,"rating"] if ok_doc else None))
V=pd.DataFrame(rows); V.to_csv("outputs/quote_verification.csv",index=False)
print(f"quotes={len(V)} verbatim_in_raw={int(V.verbatim_in_raw.sum())} doc_found={int(V.doc_found.sum())} pii_flagged={int(V.pii_flag.sum())}")
bad=V[~V.verbatim_in_raw|V.pii_flag]
if len(bad): print(bad[["topic","doc_id","quote","verbatim_in_raw","pii_flag"]].to_string()); sys.exit(1)
