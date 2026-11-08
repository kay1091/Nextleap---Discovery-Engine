import pandas as pd, sys
f,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); W=int(sys.argv[4]) if len(sys.argv)>4 else 300
s=pd.read_csv(f)
for _,r in s.iloc[a:b].iterrows():
    print(f"{r.doc_id}|{r.strat[:4]}|{'' if r.rating!=r.rating else int(r.rating)}| {r.text[:W]}")
