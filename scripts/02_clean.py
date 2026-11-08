"""Stage 2: unify raw sources -> dedupe -> language detect -> spam flag -> relevance / first-time / product tags.
Outputs data/processed/corpus_all.csv (every unique doc, with flags) and corpus_relevant.csv (SIP/MF-relevant, non-spam)."""
import warnings; warnings.filterwarnings("ignore")
import json, glob, re, hashlib, pandas as pd, sys
sys.path.insert(0,"scripts")
from common import *
def jl(p): 
    rows=[]
    for f in glob.glob(p):
        for line in open(f):
            try: rows.append(json.loads(line))
            except: pass
    return rows
docs=[]
for r in jl("data/raw/playstore*_raw.jsonl"):
    docs.append(dict(source="playstore",product=r["product"],kind="review",date=r["date"],rating=r["rating"],text=r["text"] or "",url=r["url"],raw_id=r["id"],context="",likes=r.get("thumbs_up")))
for r in jl("data/raw/appstore_raw.jsonl"):
    docs.append(dict(source="appstore",product=r["product"],kind="review",date=r["date"],rating=r["rating"],text=((r.get("title") or "")+". "+(r["text"] or "")).strip(),url=r["url"],raw_id=r["id"],context="",likes=None))
for r in jl("data/raw/reddit_posts_raw.jsonl"):
    t=(r.get("text") or "")
    if t in ("[removed]","[deleted]"): t=""
    docs.append(dict(source="reddit",product=None,kind="post",date=r["date"],rating=None,text=((r.get("title") or "")+". "+t).strip(),url=r["url"],raw_id=r["id"],context="r/"+str(r["subreddit"]),likes=r.get("score")))
for r in jl("data/raw/reddit_comments_raw.jsonl"):
    t=r.get("text") or ""
    if t in ("[removed]","[deleted]"): continue
    docs.append(dict(source="reddit",product=None,kind="comment",date=r["date"],rating=None,text=t,url=r.get("url"),raw_id=r["id"],context="r/"+str(r["subreddit"]),likes=r.get("score")))
for r in jl("data/raw/youtube_raw.jsonl"):
    docs.append(dict(source="youtube",product=None,kind="reply" if r["is_reply"] else "comment",date=(pd.to_datetime(r["date_ts"],unit="s").isoformat() if r.get("date_ts") else None),rating=None,text=r["text"],url=r["url"],raw_id=r["id"],context=f'{r["channel"]} | {r["video_title"]}',likes=r.get("votes")))
for r in jl("data/raw/forums_raw.jsonl"):
    if r.get("staff"): continue    # exclude staff/mod answers: we want user voices
    docs.append(dict(source=r["source"],product=None,kind=r["kind"],date=r["date"],rating=None,text=r["text"] if r["kind"]=="reply" else (r["topic_title"]+". "+r["text"]),url=r["url"],raw_id=r["id"],context=r["topic_title"],likes=r.get("likes")))
for r in jl("data/raw/x_raw.jsonl"):
    docs.append(dict(source="x",product=None,kind="post",date=r["date"],rating=None,text=r["text"],url=r["url"],raw_id=r["id"],context="",likes=r.get("likes")))
df=pd.DataFrame(docs); n_raw=len(df)
df["text"]=df["text"].fillna("").str.replace(r"\s+"," ",regex=True).str.strip()
stats=[("raw records loaded",n_raw)]
# dedupe 1: same source + raw id
df=df.drop_duplicates(["source","raw_id"]); stats.append(("after dedupe by (source,id)",len(df)))
df["norm"]=df["text"].str.lower().str.replace(r"[^a-z0-9\u0900-\u0dff]+"," ",regex=True).str.strip()
df=df[df["norm"].str.len()>0]
# dedupe 2: same source + product + normalized text (copy-paste duplicates), count them
df["dup_n"]=df.groupby(["source","product","norm"],dropna=False)["norm"].transform("size")
df=df.drop_duplicates(["source","product","norm"]); stats.append(("after dedupe by normalised text within source/product",len(df)))
df["date"]=pd.to_datetime(df["date"],errors="coerce",utc=True).dt.tz_convert(None)
df["n_words"]=df["text"].str.split().str.len()
df["lang"]=[detect_lang(t) for t in df["text"]]
# ---- spam / promo / low-signal flags ----
PROMO=re.compile(r"telegram|whatsapp (group|me)|t\.me/|join (my|our|us)|dm (me|us)|inbox me|call (me|us)|guaranteed|sebi[- ]registered|stock tips?|trading (course|tips)|crypto|bitcoin|forex|binary option|earn \$|subscribe|follow (me|us)|link in (bio|comments?)|check (out )?my (channel|video)|use (my )?(referral|code)|referral code|open (a )?demat.*(link|my)|#ad\b|promo code|click here|loan (offer|approval)|investment plan.*contact|\bmyth\b.*\bfact\b|watch (and|&) share|please watch|pls watch", re.I)
def spam_reason(row):
    t=row["text"]; w=row["n_words"]
    if PROMO.search(t): return "promo/solicit"
    if len(re.findall(r"#\w+",t))>=3: return "hashtag-spam"
    if len(re.findall(r"https?://",t))>=2: return "multi-link"
    if re.search(r"(.)\1{6,}",t): return "repeated-chars"
    if w<3: return "too-short(<3 words)"
    alpha=sum(c.isalpha() for c in t)
    if alpha/ max(1,len(t))<0.4 and w<12: return "mostly-non-alpha"
    if row["dup_n"]>=4 and w<25: return "repeated-copy(>=4)"
    if row["source"]=="x" and re.search(r"\b(sip|sipped|sipping)\b",t,re.I) and not re.search(r"invest|mutual|fund|market|nifty|sensex|returns|₹|nav|groww|zerodha|stock|portfolio|month",t,re.I): return "off-topic(beverage 'sip')"
    return ""
df["spam"]=df.apply(spam_reason,axis=1)
# ---- relevance tags ----
df["has_sip"]=df["text"].str.contains(SIP_RE)
df["has_mf"]=df["text"].str.contains(MF_RE.pattern,regex=True,flags=re.I)
df["fin_ctx"]=df["text"].str.contains(FIN_CTX_RE)
df["first_person"]=df["text"].str.contains(FIRST_PERSON_RE.pattern,regex=True,flags=re.I)
df["behaviour"]=df["text"].str.contains(BEHAV_RE.pattern,regex=True,flags=re.I)
df["first_time_cue"]=df["text"].str.contains(FIRST_TIME_RE.pattern,regex=True,flags=re.I)
thread_ctx=df["source"].isin(["youtube","tradingqna","valuepickr"])
sip_topic=(df["has_sip"]&df["fin_ctx"])|df["has_mf"]
# for thread-based sources a first-person behavioural comment under a SIP video/thread counts as in-topic even without keyword
df["relevant"]=sip_topic | (thread_ctx & df["first_person"] & df["behaviour"] & (df["n_words"]>=8))
# lang group: langdetect mislabels short romanised Hinglish/Indian-English as id/so/af/tl...; fold Latin-script 'other:*' into 'romanised-other'
def lang_group(l):
    if l in("english",): return "english"
    if l in("hinglish","tanglish","short"): return l
    if l.startswith("other:"): return "romanised-other(unclear)"
    if l in("unknown",): return "unknown"
    return "indic-script:"+l
df["lang_group"]=df["lang"].map(lang_group)
# journey_core: text that is explicitly about SIPs (the unit of analysis for the RQs)
SIPWORD=re.compile(r"\bsips?\b|systematic investment",re.I)
AUTOPAY=re.compile(r"auto-?pay|mandate|instal+ments?|step[- ]?up",re.I)
df["journey_core"]=(df["text"].str.contains(SIPWORD)|(df["text"].str.contains(AUTOPAY)&df["has_mf"]))&df["fin_ctx"]
# platform-generic app reviews ('good app') are not relevant unless they mention SIP/MF terms
# product tag
def prod_tags(row):
    tags=[p for p,rx in PRODUCT_RES.items() if rx.search(row["text"])]
    if row["source"] in ("playstore","appstore") and row["product"] and row["product"] not in tags: tags=[row["product"]]+tags
    return "|".join(tags)
df["products_mentioned"]=df.apply(prod_tags,axis=1)
import hashlib
df["doc_id"]=[s[:2].upper()+hashlib.md5(f"{s}|{r}".encode()).hexdigest()[:8] for s,r in zip(df["source"],df["raw_id"])]
assert df.doc_id.is_unique
df=df.drop(columns=["norm"])
df.to_csv("data/processed/corpus_all.csv",index=False)
df["relevant"]=df["relevant"]|df["journey_core"]
rel=df[df["relevant"]&(df["spam"]=="")]
rel.to_csv("data/processed/corpus_relevant.csv",index=False)
core=rel[rel.journey_core]; stats+= [("SIP-journey core (explicit SIP/mandate/instalment talk, non-spam)",len(core)),("unique docs",len(df)),("flagged spam/low-signal",int((df['spam']!='').sum())),("SIP/MF-relevant & non-spam",len(rel))]
print(stats)
summ=df.groupby(["source"]).agg(unique=("doc_id","size"),spam=("spam",lambda s:(s!="").sum()),relevant=("relevant","sum")).join(rel.groupby("source").size().rename("relevant_nonspam"))
print(summ); print(df["lang"].value_counts().head(12))
print(df[df.spam!=""].groupby(["source","spam"]).size().unstack(0).fillna(0).astype(int))
json.dump(stats,open("data/processed/clean_stats.json","w"))
