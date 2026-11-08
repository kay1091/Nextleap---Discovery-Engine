"""Find YouTube videos about SIPs via yt-dlp search (no API key). Writes data/raw/youtube_videos.json"""
import subprocess, json
QUERIES=["SIP mutual fund for beginners India","should I stop my SIP market crash","SIP returns negative why","SIP band karna chahiye","SIP kaise start kare Groww","Groww SIP mutual fund how to","SIP step up kya hai","pause SIP or continue SIP","SIP vs FD which is better","SIP failed mandate autopay","first SIP mutual fund mistakes","XIRR vs absolute returns mutual fund explained","SIP 5 years results real experience","SIP review my portfolio is in red","Pranjal Kamra SIP","CA Rachana Ranade SIP","Warikoo mutual fund SIP","Labour Law Advisor SIP mutual funds","Groww app mutual fund review","SIP kitne saal tak karni chahiye","SIP lena chahiye ya nahi","how much to invest in SIP salary beginners","SIP stopped after 1 year","SIP me loss ho raha hai kya kare","SIP தமிழ் mutual fund beginners"]
vids={}
for q in QUERIES:
    r=subprocess.run(["yt-dlp",f"ytsearch25:{q}","--flat-playlist","--dump-json","--no-warnings"],capture_output=True,text=True,timeout=180)
    n=0
    for line in r.stdout.splitlines():
        try: j=json.loads(line)
        except: continue
        vid=j["id"]
        if vid not in vids: vids[vid]={"id":vid,"title":j.get("title"),"channel":j.get("channel") or j.get("uploader"),"view_count":j.get("view_count"),"duration":j.get("duration"),"query":q}; n+=1
    print(q,n,len(vids),r.stderr[:100].replace("\n"," "),flush=True)
json.dump(list(vids.values()),open("data/raw/youtube_videos.json","w"),ensure_ascii=False,indent=1)
