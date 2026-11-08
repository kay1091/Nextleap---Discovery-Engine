"""Groww Play reviews in Hindi/Tamil/Telugu/etc. UI-language filters to capture non-English / Hinglish text."""
import json, time
from google_play_scraper import reviews, Sort
out=open("data/raw/playstore_regional_raw.jsonl","w"); log=open("logs/collect_playstore_regional.log","w")
for lang in ["hi","ta","te","bn","mr","gu","kn"]:
  for sname,sort in [("NEWEST",Sort.NEWEST),("MOST_RELEVANT",Sort.MOST_RELEVANT)]:
    n=0; tok=None
    try:
        while n<1000:
            b,tok=reviews("com.nextbillion.groww",lang=lang,country="in",sort=sort,count=200,continuation_token=tok)
            for r in b: out.write(json.dumps({"source":"playstore","product":"Groww","id":r["reviewId"],"date":r["at"].isoformat(),"rating":r["score"],"text":r["content"],"thumbs_up":r["thumbsUpCount"],"app_version":r.get("reviewCreatedVersion"),"sort":sname+"_"+lang,"url":f"https://play.google.com/store/apps/details?id=com.nextbillion.groww&reviewId={r['reviewId']}"},ensure_ascii=False)+"\n")
            n+=len(b)
            if not b or tok is None or tok.token is None: break
            time.sleep(0.4)
        m=f"OK lang={lang} {sname} got={n}"
    except Exception as e: m=f"FAIL lang={lang} {sname} {e}"
    print(m,flush=True); log.write(m+"\n")
