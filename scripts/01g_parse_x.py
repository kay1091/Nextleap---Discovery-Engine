"""Parse saved outputs of the `x` MCP tool (search_posts_all, recent+full-archive public X search) into JSONL.
The searches themselves were issued by the agent via the MCP tool; queries are listed in logs/x_queries.txt"""
import json, glob, re
seen={}; files=sorted(glob.glob("data/raw/x_tool_outputs/*.txt"))
for f in files:
    t=open(f).read(); i=t.find("{")
    try: d=json.loads(t[i:t.rfind("}")+1])
    except Exception as e: print("parse fail",f,e); continue
    for p in d.get("data",[]):
        seen[p["id"]]={"source":"x","product":None,"id":p["id"],"date":p["created_at"],"text":p["text"],"lang":p.get("lang"),"likes":p.get("public_metrics",{}).get("like_count"),"impressions":p.get("public_metrics",{}).get("impression_count"),"url":p.get("url"),"is_reply":any(r["type"]=="replied_to" for r in p.get("referenced_tweets",[]))}
with open("data/raw/x_raw.jsonl","w") as o:
    for r in seen.values(): o.write(json.dumps(r,ensure_ascii=False)+"\n")
print(len(files),"files ->",len(seen),"unique posts")
