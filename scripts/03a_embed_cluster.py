"""Stage 3a (bottom-up theme discovery): multilingual sentence embeddings + KMeans, with c-TF-IDF style keywords per cluster,
plus an independent NMF topic model on TF-IDF. Outputs data/processed/clusters_*.csv/md for the analyst (me) to read and open-code."""
import pandas as pd, numpy as np, os, re, sys
from sentence_transformers import SentenceTransformer
from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF
rel=pd.read_csv("data/processed/corpus_relevant.csv")
# substantive docs only for discovery (>=8 words) - very short comments carry little theme signal
d=rel[rel.n_words>=8].copy().reset_index(drop=True)
cache="data/processed/emb_cache.npz"
store={}
if os.path.exists(cache):
    z=np.load(cache,allow_pickle=True); store=dict(zip(z["ids"],z["vecs"]))
need=[(i,t) for i,t in zip(d.doc_id,d.text) if i not in store]
if need:
    m=SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2"); m.max_seq_length=160
    vecs=m.encode([t[:1200] for _,t in need],batch_size=64,show_progress_bar=False,normalize_embeddings=True)
    for (i,_),v in zip(need,vecs): store[i]=v
    np.savez(cache,ids=np.array(list(store.keys())),vecs=np.array(list(store.values())))
E=np.array([store[i] for i in d.doc_id]); print("embedded",E.shape)
K=int(sys.argv[1]) if len(sys.argv)>1 else 28
km=MiniBatchKMeans(K,random_state=7,n_init=5,batch_size=2048).fit(E); d["cluster"]=km.labels_
cv=CountVectorizer(stop_words="english",min_df=5,ngram_range=(1,2),max_features=60000,token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b")
X=cv.fit_transform(d.text); terms=np.array(cv.get_feature_names_out())
# c-TF-IDF
cl_docs=np.vstack([np.asarray(X[d.cluster.values==k].sum(0)).ravel() for k in range(K)]).astype(float)
tf=cl_docs/cl_docs.sum(1,keepdims=True); idf=np.log(1+cl_docs.sum()/ (cl_docs.sum(0)+1)); ctf=tf*idf
lines=["# Embedding clusters (auto-generated; for analyst review)\n"]
rows=[]
for k in np.argsort(-np.bincount(d.cluster)):
    sub=d[d.cluster==k]; top=terms[np.argsort(-ctf[k])[:12]]
    cen=km.cluster_centers_[k]; idx=np.argsort(-(E[d.cluster.values==k]@cen))[:4]
    lines.append(f"\n## Cluster {k}  (n={len(sub)}; sources={sub.source.value_counts().to_dict()})\nTop terms: {', '.join(top)}\n")
    for j in idx: lines.append(f"- [{sub.iloc[j].doc_id}] {sub.iloc[j].text[:260]}")
    rows.append(dict(cluster=k,n=len(sub),top_terms=", ".join(top),sources=str(sub.source.value_counts().to_dict())))
open("data/processed/clusters_embedding.md","w").write("\n".join(lines))
pd.DataFrame(rows).to_csv("data/processed/clusters_embedding.csv",index=False)
d[["doc_id","cluster"]].to_csv("data/processed/doc_cluster.csv",index=False)
# NMF topics (independent method)
tv=TfidfVectorizer(stop_words="english",min_df=8,max_df=0.4,ngram_range=(1,2),max_features=40000,token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b")
T=tv.fit_transform(d.text); nmf=NMF(20,random_state=3,init="nndsvd",max_iter=400).fit(T)
tt=np.array(tv.get_feature_names_out()); W=nmf.transform(T); d["nmf"]=W.argmax(1)
nl=["# NMF topics (TF-IDF; auto-generated)\n"]
for k in range(20): nl.append(f"- topic {k} (n={int((d.nmf==k).sum())}): {', '.join(tt[np.argsort(-nmf.components_[k])[:12]])}")
open("data/processed/topics_nmf.md","w").write("\n".join(nl)); print("\n".join(nl))
