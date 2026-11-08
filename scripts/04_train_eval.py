"""Stage 3c: train + evaluate the scalable coder.
 - Gold = my (analyst-LLM) labels: TRAIN (n=303, half random / half targeted) and HOLDOUT (n=150, random, labelled blind before any classifier existed).
 - Methods compared on HOLDOUT: (1) regex rules only  (2) ML only (LogReg on multilingual-MiniLM embeddings + TF-IDF)  (3) ensemble = regex OR ML@threshold
 - ML thresholds are picked by 5-fold CV on TRAIN only. Holdout is touched once per method configuration.
Outputs metrics to data/processed/eval_*.csv and holdout predictions for human spot-check."""
import sys; sys.path.insert(0,"scripts")
import pandas as pd, numpy as np, glob, json, warnings; warnings.filterwarnings("ignore")
from codebook import *
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import precision_recall_fscore_support, cohen_kappa_score, accuracy_score, f1_score
from scipy.sparse import hstack, csr_matrix
def load(prefix):
    rows=[]
    for f in sorted(glob.glob(f"labels/{prefix}_labels_part*.txt")):
        for l in open(f):
            i,st,out,codes=l.strip().split("|"); rows.append(dict(doc_id=i,stance=st,outcome=out,codes=[] if codes=="-" else codes.split(",")))
    return pd.DataFrame(rows)
_t=pd.concat([pd.read_csv("data/processed/train_unlabelled.csv"),pd.read_csv("data/processed/train2_unlabelled.csv")]).drop_duplicates("doc_id")
tr=load("train").merge(_t[["doc_id","text","source","product","rating","pool"]],on="doc_id")
ho=load("holdout").merge(pd.read_csv("data/processed/holdout_unlabelled.csv")[["doc_id","text","source","product","rating","pool"]],on="doc_id")
CN=list(CODES)
def Y(df): return np.array([[c in cs for c in CN] for cs in df.codes]).astype(int)
Ytr,Yho=Y(tr),Y(ho)
emb=SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2"); emb.max_seq_length=160
def E(df): return emb.encode([t[:1200] for t in df.text],batch_size=64,show_progress_bar=False,normalize_embeddings=True)
import os
if os.path.exists("data/processed/emb_labelled.npz") and np.load("data/processed/emb_labelled.npz",allow_pickle=True)["n"]==len(tr)+len(ho):
    z=np.load("data/processed/emb_labelled.npz",allow_pickle=True); Etr,Eho=z["tr"],z["ho"]
else:
    Etr,Eho=E(tr),E(ho); np.savez("data/processed/emb_labelled.npz",tr=Etr,ho=Eho,n=len(tr)+len(ho))
def rx(df): return np.array([[1 if COMPILED[c].search(t) else 0 for c in CN] for t in df.text])
Rtr,Rho=rx(tr),rx(ho)
tf_w=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True,max_features=30000); tf_c=TfidfVectorizer(analyzer="char_wb",ngram_range=(3,5),min_df=3,sublinear_tf=True,max_features=40000)
def feats(df,E_,R_,fit=False):
    if fit: Aw=tf_w.fit_transform(df.text); Ac=tf_c.fit_transform(df.text)
    else: Aw=tf_w.transform(df.text); Ac=tf_c.transform(df.text)
    return hstack([Aw,Ac*0.5,csr_matrix(E_*2.0),csr_matrix(R_*1.0)]).tocsr()   # regex hits also fed as features (stacking)
Xtr=feats(tr,Etr,Rtr,True); Xho=feats(ho,Eho,Rho)
def fitpred(Xa,ya,Xb,C=3.0):
    if ya.sum()<2: return np.zeros(Xb.shape[0])
    m=LogisticRegression(C=C,class_weight="balanced",max_iter=2000).fit(Xa,ya); return m.predict_proba(Xb)[:,1]
# --- CV on train to pick per-code thresholds (maximise F1 of ensemble = regex OR ml>=t)
skf=StratifiedKFold(5,shuffle=True,random_state=0); oof=np.zeros(Ytr.shape,float)
for j,c in enumerate(CN):
    y=Ytr[:,j]
    if y.sum()<5: continue
    for a,b in skf.split(Xtr,y if y.sum()>=5 else np.zeros(len(y))):
        # refit tfidf-free features on fold: reuse global tfidf fit (unsupervised; tiny leakage of vocabulary only)
        oof[b,j]=fitpred(Xtr[a],y[a],Xtr[b])
thr={}; variant={}
for j,c in enumerate(CN):
    y=Ytr[:,j]
    if y.sum()<5: thr[c]=1.1; variant[c]="regex"; continue    # too few labelled positives for ML: rule only
    best=(-1,None,None)
    for t in np.arange(0.3,0.95,0.05):
        ml=(oof[:,j]>=t).astype(int); rg=Rtr[:,j]
        for v,p in [("and",ml&rg),("ml",ml),("or",ml|rg)]:
            f=f1_score(y,p,zero_division=0)
            if f>best[0]+1e-9: best=(f,float(t),v)
    f_rg=f1_score(y,Rtr[:,j],zero_division=0)
    if f_rg>best[0]+1e-9: thr[c]=1.1; variant[c]="regex"
    else: thr[c]=best[1]; variant[c]=best[2]
# --- final models on all train
P=np.zeros(Yho.shape,float)
for j,c in enumerate(CN): P[:,j]=fitpred(Xtr,Ytr[:,j],Xho)
ML=np.array([[P[i,j]>=thr[c] for j,c in enumerate(CN)] for i in range(len(ho))]).astype(int)
def combine(ML_,R_):
    out=np.zeros_like(ML_)
    for j,c in enumerate(CN):
        v=variant[c]
        out[:,j]= R_[:,j] if v=="regex" else (ML_[:,j] if v=="ml" else (ML_[:,j]&R_[:,j] if v=="and" else ML_[:,j]|R_[:,j]))
    return out
ENS=combine(ML,Rho)
def metrics(Yt,Yp,name):
    rows=[]
    for j,c in enumerate(CN):
        y,p=Yt[:,j],Yp[:,j]; sup=int(y.sum())
        pr,rc,f,_=precision_recall_fscore_support(y,p,average="binary",zero_division=0)
        k=cohen_kappa_score(y,p) if (y.sum()>0 and p.sum()>0 and len(set(y))>1) else np.nan
        rows.append(dict(method=name,code=c,group=CODES[c][0],support_gold=sup,pred_pos=int(p.sum()),precision=pr,recall=rc,f1=f,kappa=k))
    return pd.DataFrame(rows)
M=pd.concat([metrics(Yho,Rho,"regex_only"),metrics(Yho,ML,"ml_only"),metrics(Yho,ENS,"ensemble")])
M.to_csv("data/processed/eval_codes_holdout.csv",index=False)
summ=[]
for name,Yp in [("regex_only",Rho),("ml_only",ML),("ensemble",ENS)]:
    sub=M[(M.method==name)&(M.support_gold>=5)]
    # micro over all code decisions
    pr,rc,f,_=precision_recall_fscore_support(Yho.ravel(),Yp.ravel(),average="binary",zero_division=0)
    summ.append(dict(method=name,codes_with_support_ge5=len(sub),macro_precision=sub.precision.mean(),macro_recall=sub.recall.mean(),macro_f1=sub.f1.mean(),mean_kappa=sub.kappa.mean(),micro_precision=pr,micro_recall=rc,micro_f1=f,micro_kappa=cohen_kappa_score(Yho.ravel(),Yp.ravel())))
S=pd.DataFrame(summ); S.to_csv("data/processed/eval_summary_holdout.csv",index=False); print(S.round(3).to_string())
# group-level (any code in group) agreement
gm=[]
for g in sorted(set(v[0] for v in CODES.values())):
    idx=[j for j,c in enumerate(CN) if CODES[c][0]==g]
    yt=Yho[:,idx].max(1)
    for name,Yp in [("regex_only",Rho),("ml_only",ML),("ensemble",ENS)]:
        yp=Yp[:,idx].max(1); pr,rc,f,_=precision_recall_fscore_support(yt,yp,average="binary",zero_division=0)
        gm.append(dict(group=g,method=name,support_gold=int(yt.sum()),precision=pr,recall=rc,f1=f,kappa=cohen_kappa_score(yt,yp) if yt.sum()>0 and yp.sum()>0 else np.nan))
G=pd.DataFrame(gm); G.to_csv("data/processed/eval_groups_holdout.csv",index=False); print(G[G.method=="ensemble"].round(3).to_string())
# stance / outcome classifiers
for tgt,labs in [("stance",STANCES),("outcome",OUTCOMES)]:
    ytr_,yho_=tr[tgt].values,ho[tgt].values
    m=LogisticRegression(C=3,class_weight="balanced",max_iter=3000).fit(Xtr,ytr_); p=m.predict(Xho)
    print(tgt,"acc",round(accuracy_score(yho_,p),3),"macroF1",round(f1_score(yho_,p,average="macro"),3),"kappa",round(cohen_kappa_score(yho_,p),3))
    pd.DataFrame({"doc_id":ho.doc_id,"gold":yho_,"pred":p}).to_csv(f"data/processed/holdout_{tgt}_pred.csv",index=False)
    json.dump(dict(acc=accuracy_score(yho_,p),macro_f1=f1_score(yho_,p,average="macro"),kappa=cohen_kappa_score(yho_,p),n=len(yho_)),open(f"data/processed/eval_{tgt}.json","w"))
json.dump(dict(thr=thr,variant=variant),open("data/processed/ml_thresholds.json","w"))
ho_out=ho[["doc_id","source","text"]].copy(); ho_out["gold_codes"]=[",".join(c) for c in ho.codes]; ho_out["ensemble_codes"]=[",".join(c for j,c in enumerate(CN) if ENS[i,j]) for i in range(len(ho))]
ho_out.to_csv("data/processed/holdout_gold_vs_pred.csv",index=False)
# train-set regex quality (for rule iteration; train only)
Mt=metrics(Ytr,Rtr,"regex_train"); Mt.to_csv("data/processed/eval_codes_train_regex.csv",index=False)
print(Mt[["code","support_gold","pred_pos","precision","recall","f1"]].round(2).to_string())
