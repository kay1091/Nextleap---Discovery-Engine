"""Download top comments for selected YouTube videos with youtube-comment-downloader (no API key)."""
import json, time, threading
from concurrent.futures import ThreadPoolExecutor
from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
vids=json.load(open("data/raw/youtube_videos.json"))
vids=[v for v in vids if v.get("duration") and 150<=v["duration"]<=5400 and v.get("view_count")]
vids.sort(key=lambda v:-v["view_count"]); vids=vids[:180]
lock=threading.Lock(); out=open("data/raw/youtube_raw.jsonl","w"); log=open("logs/collect_youtube.log","w")
LIMIT=250
def work(v):
    n=0
    try:
        dl=YoutubeCommentDownloader()
        for c in dl.get_comments_from_url(f"https://www.youtube.com/watch?v={v['id']}", sort_by=SORT_BY_POPULAR):
            rec={"source":"youtube","product":None,"id":c["cid"],"date_rel":c.get("time"),"date_ts":c.get("time_parsed"),"text":c["text"],"votes":c.get("votes"),"is_reply":bool(c.get("reply")),"video_id":v["id"],"video_title":v["title"],"channel":v["channel"],"video_views":v["view_count"],"url":f"https://www.youtube.com/watch?v={v['id']}&lc={c['cid']}"}
            with lock: out.write(json.dumps(rec,ensure_ascii=False)+"\n")
            n+=1
            if n>=LIMIT: break
        msg=f"OK {v['id']} {v['channel']} | {v['title'][:60]} n={n}"
    except Exception as e: msg=f"FAIL {v['id']} n={n} {type(e).__name__} {str(e)[:100]}"
    with lock: log.write(msg+"\n"); log.flush(); out.flush()
    print(msg,flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(work,vids))
