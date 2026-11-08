"""Stage 3d: apply the final scalable coder to the whole SIP-journey corpus.
Coder = per-code variant chosen by 5-fold OOF F1 on TRAIN labels (ml_thresholds.json): regex | ml | regex AND ml | regex OR ml.
ML = LogReg on TF-IDF(word+char) + multilingual-MiniLM embedding + regex-hit features, trained on TRAIN labels only (train + train round 2 = n labelled docs;
the 150-doc blind holdout is NOT used for fitting, so the holdout metrics describe exactly this model).
Also predicts stance (E/Q/A/O) and outcome (S/P/R/C/K/N).  Output: data/processed/corpus_coded.csv"""
import sys; sys.path.insert(0,"scripts")
import pandas as pd, numpy as np, glob, json, os, warnings; warnings.filterwarnings("ignore")
from codebook import *
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack, csr_matrix
def load(prefix):
    rows=[]
    for f in sorted(glob.glob(f"labels/{prefix}_labels_part*.txt")):
        for l in open(f):
            i,st,out,codes=l.strip().split("|"); rows.append(dict(doc_id=i,stance=st,outcome=out,codes=[] if codes=="-" else codes.split(",")))
    return pd.DataFrame(rows)
_t=pd.concat([pd.read_csv("data/processed/train_unlabelled.csv"),pd.read_csv("data/processed/train2_unlabelled.csv")]).drop_duplicates("doc_id")
tr=load("train").merge(_t[["doc_id","text"]],on="doc_id")
CN=list(CODES); thr=json.load(open("data/processed/ml_thresholds.json")); T,V=thr["thr"],thr["variant"]
rel=pd.read_csv("data/processed/corpus_relevant.csv"); core=rel[rel.journey_core].copy().reset_index(drop=True)
print("journey_core docs:",len(core),flush=True)
m=SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2"); m.max_seq_length=160
cache="data/processed/emb_cache.npz"; store={}
if os.path.exists(cache):
    z=np.load(cache,allow_pickle=True); store=dict(zip(z["ids"],z["vecs"]))
def embed(ids,texts):
    need=[(i,t) for i,t in zip(ids,texts) if i not in store]
    if need:
        for s in range(0,len(need),2048):
            ch=need[s:s+2048]; vecs=m.encode([t[:1200] for _,t in ch],batch_size=64,show_progress_bar=False,normalize_embeddings=True)
            for (i,_),v in zip(ch,vecs): store[i]=v
            print("embedded",s+len(ch),"/",len(need),flush=True)
        np.savez(cache,ids=np.array(list(store.keys())),vecs=np.array(list(store.values())))
    return np.array([store[i] for i in ids])
Etr=embed(list(tr.doc_id),list(tr.text)); Ecore=embed(list(core.doc_id),list(core.text))
def rx(texts): return np.array([[1 if COMPILED[c].search(t) else 0 for c in CN] for t in texts])
Rtr,Rcore=rx(tr.text),rx(core.text)
tf_w=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True,max_features=30000); tf_c=TfidfVectorizer(analyzer="char_wb",ngram_range=(3,5),min_df=3,sublinear_tf=True,max_features=40000)
def feats(texts,E_,R_,fit=False):
    if fit: Aw=tf_w.fit_transform(texts); Ac=tf_c.fit_transform(texts)
    else: Aw=tf_w.transform(texts); Ac=tf_c.transform(texts)
    return hstack([Aw,Ac*0.5,csr_matrix(E_*2.0),csr_matrix(R_*1.0)]).tocsr()
Xtr=feats(tr.text,Etr,Rtr,True); Xc=feats(core.text,Ecore,Rcore)
Ytr=np.array([[c in cs for c in CN] for cs in tr.codes]).astype(int)
out=np.zeros((len(core),len(CN)),int); prob=np.zeros((len(core),len(CN)))
for j,c in enumerate(CN):
    if Ytr[:,j].sum()>=2: prob[:,j]=LogisticRegression(C=3.0,class_weight="balanced",max_iter=2000).fit(Xtr,Ytr[:,j]).predict_proba(Xc)[:,1]
    ml=(prob[:,j]>=T[c]).astype(int); rg=Rcore[:,j]; v=V[c]
    out[:,j]= rg if v=="regex" else (ml if v=="ml" else (ml&rg if v=="and" else ml|rg))
core["codes"]=[",".join(c for j,c in enumerate(CN) if out[i,j]) for i in range(len(core))]
core["codes_regex_only"]=[",".join(c for j,c in enumerate(CN) if Rcore[i,j]) for i in range(len(core))]
core["n_codes"]=out.sum(1)
for tgt in ["stance","outcome"]:
    mm=LogisticRegression(C=3,class_weight="balanced",max_iter=3000).fit(Xtr,tr[tgt].values); core[tgt+"_pred"]=mm.predict(Xc)
for j,c in enumerate(CN): core["p_"+c]=prob[:,j].round(3)
core.to_csv("data/processed/corpus_coded.csv",index=False)
print(core.groupby("source").size()); print("docs with >=1 code:",(core.n_codes>0).mean().round(3))
