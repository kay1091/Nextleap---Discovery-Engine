"""Collect Google Play reviews (google-play-scraper). Multiple sorts x star ratings, in/en. Logs everything."""
import json, sys, time, datetime
from google_play_scraper import reviews, Sort
APPS = {
 "Groww": ("com.nextbillion.groww", 1500),   # per (sort, star) cap
 "Zerodha Coin": ("com.zerodha.coin", 300),
 "INDmoney": ("in.indwealth", 300),
 "Kuvera": ("community.fairly.customer", 300),
 "ET Money": ("com.smartspends", 300),
 "Paytm Money": ("com.paytmmoney", 300),
}
SORTS = {"NEWEST": Sort.NEWEST, "MOST_RELEVANT": Sort.MOST_RELEVANT}
out = open("data/raw/playstore_raw.jsonl","a")
log = open("logs/collect_playstore.log","a")
def L(m):
    s=f"{datetime.datetime.now().isoformat(timespec='seconds')} {m}"; print(s); log.write(s+"\n"); log.flush()
only = sys.argv[1:] 
for prod,(pkg,cap) in APPS.items():
    if only and prod not in only: continue
    for sname,sort in SORTS.items():
        for star in [1,2,3,4,5]:
            n=0; tok=None
            try:
                while n<cap:
                    batch,tok = reviews(pkg, lang="en", country="in", sort=sort, filter_score_with=star, count=min(200,cap-n), continuation_token=tok)
                    for r in batch:
                        out.write(json.dumps({"source":"playstore","product":prod,"id":r["reviewId"],"date":r["at"].isoformat(),"rating":r["score"],"text":r["content"],"thumbs_up":r["thumbsUpCount"],"app_version":r.get("reviewCreatedVersion"),"sort":sname,"url":f"https://play.google.com/store/apps/details?id={pkg}&reviewId={r['reviewId']}"},ensure_ascii=False)+"\n")
                    n+=len(batch)
                    if not batch or tok is None or tok.token is None: break
                    time.sleep(0.4)
                L(f"OK {prod} {sname} star={star} got={n}")
            except Exception as e:
                L(f"FAIL {prod} {sname} star={star} after={n} err={type(e).__name__}: {str(e)[:150]}")
            out.flush()
