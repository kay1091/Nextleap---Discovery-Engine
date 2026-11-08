"""Quote-candidate browser. Usage: python scripts/07b_cands.py <CODE|AREA|regex:...> [n] [family]
Prints random coded docs (verbatim excerpts around the first regex hit) so the analyst can pick quotes; picks go to outputs/quotes.txt (topic|||doc_id|||quote)."""
import sys; sys.path.insert(0,"scripts")
import pandas as pd, re, random
from codebook import COMPILED, CODES
from areas import AREAS, SOURCE_FAMILY
topic=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 12; fam=sys.argv[3] if len(sys.argv)>3 else None
d=pd.read_csv("data/processed/corpus_final.csv",low_memory=False); d["codes"]=d.codes.fillna(""); d["family"]=d.source.map(SOURCE_FAMILY)
if topic.startswith("regex:"): rx=re.compile(topic[6:],re.I); m=d.text.str.contains(rx)
elif topic in AREAS:
    cs=AREAS[topic]["codes"]; m=d.codes.apply(lambda c:any(x in c.split(",") for x in cs)); rx=re.compile("|".join(CODES[c][2] for c in cs),re.I)
else: m=d.codes.str.split(",").apply(lambda l:topic in l); rx=COMPILED[topic]
x=d[m&(d.n_words.between(8,120))]
if fam: x=x[x.family.str.startswith(fam)]
x=x.sample(min(n,len(x)),random_state=random.randint(0,10**6))
print(f"[{topic}] matches={int(m.sum())} shown={len(x)}")
for _,r in x.iterrows():
    t=r.text; mm=rx.search(t); s=max(0,(mm.start() if mm else 0)-60); e=min(len(t),(mm.end() if mm else 0)+160)
    print(f"{r.doc_id}|{r.family[:7]}|{r['product'] if isinstance(r['product'],str) else ''}|{r.rating if r.rating==r.rating else ''}| ...{t[s:e]}...")
