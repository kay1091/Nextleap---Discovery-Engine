"""Apple App Store reviews via iTunes customer-reviews RSS JSON feed (country in). Feed exposes max 10 pages x 50 per sort."""
import requests, json, time
APPS={"Groww":1404871703,"Zerodha Coin":1392892554,"INDmoney":1450178837,"Kuvera":1329701793,"ET Money":1212752482,"Paytm Money":1344431352}
import sys
# resolve comparator ids via iTunes search
def lookup(name):
    r=requests.get("https://itunes.apple.com/search",params={"term":name,"country":"in","entity":"software","limit":3},timeout=30).json()
    return [(x["trackId"],x["trackName"]) for x in r.get("results",[])]
out=open("data/raw/appstore_raw.jsonl","w"); log=open("logs/collect_appstore.log","w")
def L(m): print(m); log.write(m+"\n")
for name,aid in APPS.items():
    for sortby in ["mostrecent","mosthelpful"]:
        n=0
        for page in range(1,11):
            url=f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={aid}/sortby={sortby}/json"
            try:
                r=requests.get(url,timeout=30,headers={"User-Agent":"Mozilla/5.0"}); 
                if r.status_code!=200: L(f"FAIL {name} {sortby} p{page} http {r.status_code}"); break
                ent=r.json()["feed"].get("entry",[])
                ent=[e for e in ent if "im:rating" in e]
                for e in ent:
                    out.write(json.dumps({"source":"appstore","product":name,"id":e["id"]["label"],"date":e["updated"]["label"],"rating":int(e["im:rating"]["label"]),"title":e["title"]["label"],"text":e["content"]["label"],"app_version":e["im:version"]["label"],"sort":sortby,"url":f"https://apps.apple.com/in/app/id{aid}?see-all=reviews"},ensure_ascii=False)+"\n")
                n+=len(ent)
                if not ent: break
            except Exception as ex: L(f"FAIL {name} {sortby} p{page} {ex}"); break
            time.sleep(0.5)
        L(f"OK {name} {sortby} got={n}")
for n in []:
    L(f"lookup {n}: {lookup(n)}")
