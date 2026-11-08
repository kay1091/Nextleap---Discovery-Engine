"""Collect TradingQnA (Zerodha community) and ValuePickr threads via Discourse public JSON (/search.json, /t/<id>.json)."""
import requests, json, time, re, html, sys
FORUMS={"tradingqna":"https://tradingqna.com","valuepickr":"https://forum.valuepickr.com"}
QUERIES=["SIP stopped","SIP paused","SIP failed","SIP mandate","SIP returns negative","first SIP","should I continue SIP","stop SIP","cancel SIP","SIP not deducted","SIP instalment failed","Groww SIP","Coin SIP","SIP step up","SIP insufficient balance","SIP bank autopay limit","new investor SIP","SIP red portfolio","SIP vs FD","SIP XIRR"]
UA={"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0 groww-discovery-research/0.1"}
def strip(h): 
    t=re.sub(r"<blockquote>.*?</blockquote>","",h,flags=re.S)  # drop quoted text
    t=re.sub(r"<[^>]+>"," ",t); return re.sub(r"\s+"," ",html.unescape(t)).strip()
log=open("logs/collect_forums.log","w")
def L(m): print(m,flush=True); log.write(m+"\n"); log.flush()
out=open("data/raw/forums_raw.jsonl","w")
for fname,base in FORUMS.items():
    topics={}
    for q in QUERIES:
        for page in range(1,4):
            try:
                r=requests.get(base+"/search.json",params={"q":q+" order:latest","page":page},headers=UA,timeout=40)
                if r.status_code!=200: L(f"FAIL {fname} search '{q}' p{page} http {r.status_code}"); time.sleep(5); break
                d=r.json(); ts=d.get("topics") or []
                for t in ts: topics.setdefault(t["id"],t.get("title"))
                if not d.get("posts"): break
            except Exception as e: L(f"FAIL {fname} search {q} {e}"); break
            time.sleep(1.2)
        L(f"{fname} q='{q}' topics_total={len(topics)}")
    n=0
    for tid,title in topics.items():
        try:
            r=requests.get(f"{base}/t/{tid}.json",headers=UA,timeout=40)
            if r.status_code!=200: L(f"FAIL topic {tid} http {r.status_code}"); time.sleep(3); continue
            d=r.json()
            for p in d["post_stream"]["posts"]:
                txt=strip(p.get("cooked",""))
                if len(txt)<20: continue
                out.write(json.dumps({"source":fname,"id":f"{fname}-{p['id']}","kind":"post" if p["post_number"]==1 else "reply","topic_id":tid,"topic_title":d.get("title"),"date":p["created_at"],"likes":p.get("like_count",0),"text":txt,"staff":bool(p.get("staff") or p.get("moderator") or p.get("admin")),"url":f"{base}/t/{d.get('slug')}/{tid}/{p['post_number']}"},ensure_ascii=False)+"\n"); n+=1
        except Exception as e: L(f"FAIL topic {tid} {e}")
        time.sleep(1.0)
        out.flush()
    L(f"DONE {fname}: topics={len(topics)} posts={n}")
