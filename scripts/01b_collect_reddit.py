"""Collect Reddit posts+comments from Arctic Shift (public Reddit archive API). 
Reddit's own .json endpoints return 403/302 from this network; PullPush returns 429 ('no free scraping for agents').
Keyword search is only supported in narrow windows, so we use adaptive date windows (halve on timeout).
Usage: python 01b_collect_reddit.py posts|comments
"""
import requests, json, time, sys, datetime as dt
mode=sys.argv[1]
BASE="https://arctic-shift.photon-reddit.com/api"
UA="groww-discovery-research/0.1 (academic PM case study; contact: n/a)"
SUBS=(["IndiaInvestments","IndianStockMarket","personalfinanceindia","FIREIndia","mutualfunds","DalalStreetTalks","indianstreetbets","IndiaPersonalFinance","StartInvestingIndia"] if mode=="comments" else ["IndianStockMarket","personalfinanceindia","FIREIndia","mutualfunds","DalalStreetTalks","indianstreetbets","IndiaPersonalFinance","StartInvestingIndia","groww","IndiaFinance","CreditCardsIndia"])
if len(sys.argv)>2: SUBS=sys.argv[2].split(",")
START=dt.date(2023,1,1); END=dt.date(2026,10,29)
QUERIES = ["SIP"] if mode=="comments" else ["SIP","groww"]
log=open(f"logs/collect_reddit_{mode}.log","a")
def L(m):
    s=f"{dt.datetime.now().isoformat(timespec='seconds')} {m}"; print(s,flush=True); log.write(s+"\n"); log.flush()
def get(path, params, tries=4):
    for i in range(tries):
        try:
            r=requests.get(BASE+path, params=params, headers={"User-Agent":UA}, timeout=60)
            if r.status_code==200:
                d=r.json()
                if d.get("error"): 
                    if "imeout" in d["error"]:
                        time.sleep(4*(i+1)); continue
                    L(f"API error {d['error'][:100]}"); return None
                return d["data"] or []
            if r.status_code==429: time.sleep(10*(i+1)); continue
            if r.status_code!=422: L(f"HTTP {r.status_code} {params}")
            return []
        except Exception as e:
            time.sleep(3)
    return None
seen=set()
out=open(f"data/raw/reddit_{mode}_raw.jsonl","a")
def window(sub,q,a,b,depth=0):
    p={"subreddit":sub,"after":a.isoformat(),"before":b.isoformat(),"limit":100,"sort":"asc"}
    if mode=="posts": p["query"]=q
    else: p["body"]=q
    path="/posts/search" if mode=="posts" else "/comments/search"
    data=get(path,p); time.sleep(1.0)
    if data is None:
        if (b-a).days<=2: L(f"GIVEUP {sub} {q} {a}"); return 0
        mid=a+(b-a)/2; mid=a+dt.timedelta(days=max(1,(b-a).days//2))
        return window(sub,q,a,mid,depth+1)+window(sub,q,mid,b,depth+1)
    n=0
    if len(data)>=100 and (b-a).days>2:  # saturated page -> split to avoid truncation
        mid=a+dt.timedelta(days=max(1,(b-a).days//2))
        return window(sub,q,a,mid,depth+1)+window(sub,q,mid,b,depth+1)
    for x in data:
        if x["id"] in seen: continue
        seen.add(x["id"]); n+=1
        rec={"source":"reddit","kind":"post" if mode=="posts" else "comment","id":x["id"],"subreddit":x.get("subreddit"),"date":dt.datetime.utcfromtimestamp(x["created_utc"]).isoformat(),"score":x.get("score"),
             "title":x.get("title"),"text":(x.get("selftext") if mode=="posts" else x.get("body")),"num_comments":x.get("num_comments"),"link_id":x.get("link_id"),"parent_id":x.get("parent_id"),
             "url":("https://www.reddit.com"+x["permalink"]) if x.get("permalink") else None,"query":q}
        out.write(json.dumps(rec,ensure_ascii=False)+"\n")
    out.flush(); return n
for sub in SUBS:
    for q in QUERIES:
        tot=0; a=START
        while a<END:
            b=min(a+dt.timedelta(days=30),END)
            tot+=window(sub,q,a,b); a=b
        L(f"DONE {mode} r/{sub} q={q} new={tot}")
