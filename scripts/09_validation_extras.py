"""Extra validation numbers for AI_EVIDENCE_LOG.md: area-level holdout metrics, spam-filter audit, language handling, label counts."""
import sys; sys.path.insert(0,"scripts")
import pandas as pd, numpy as np, glob, json, re
from sklearn.metrics import precision_recall_fscore_support, cohen_kappa_score
from codebook import CODES, COMPILED
from areas import AREAS
out={}
ho=pd.read_csv("data/processed/holdout_gold_vs_pred.csv"); ho[["gold_codes","ensemble_codes"]]=ho[["gold_codes","ensemble_codes"]].fillna("")
rows=[]
for a,v in AREAS.items():
    g=ho.gold_codes.apply(lambda c:any(x in c.split(",") for x in v["codes"])).astype(int)
    if a=="A5": p=ho.text.apply(lambda t:int(bool(COMPILED["IA_ALERTS"].search(t))))
    else: p=ho.ensemble_codes.apply(lambda c:any(x in c.split(",") for x in v["codes"])).astype(int)
    pr,rc,f,_=precision_recall_fscore_support(g,p,average="binary",zero_division=0)
    rows.append(dict(area=a,gold_pos=int(g.sum()),pred_pos=int(p.sum()),precision=pr,recall=rc,f1=f,kappa=cohen_kappa_score(g,p) if g.sum() and p.sum() else np.nan))
A=pd.DataFrame(rows); A.to_csv("outputs/holdout_area_level.csv",index=False); print(A.round(2))
# spam audit
L=pd.read_csv("labels/spam_audit_labels.txt",sep="|",header=None,names=["doc_id","ok"]); out["spam_audit_n"]=len(L); out["spam_flag_precision"]=float(L.ok.mean())
# labelled counts
def cnt(prefix):
    n=0
    for f in glob.glob(f"labels/{prefix}_labels_part*.txt"): n+=sum(1 for l in open(f) if l.strip())
    return n
out.update(train_n=cnt("train"),holdout_n=cnt("holdout"),audit_n=cnt("audit"))
# language handling: coded-rate by language
d=pd.read_csv("data/processed/corpus_final.csv",low_memory=False); d["codes"]=d.codes.fillna("")
lg=d.groupby("lang_group").agg(n=("doc_id","size"),pct_any_code=("codes",lambda s:100*(s!="").mean()),mean_words=("n_words","mean")).sort_values("n",ascending=False); lg.to_csv("outputs/language_coding_rates.csv"); print(lg.round(1))
ho_src=pd.read_csv("data/processed/holdout_unlabelled.csv"); out["holdout_by_source"]=ho_src.source.value_counts().to_dict()
# holdout language mix
try:
    allc=pd.read_csv("data/processed/corpus_all.csv",low_memory=False,usecols=["doc_id","lang_group"]); h=ho_src.merge(allc,on="doc_id",how="left"); out["holdout_lang"]=h.lang_group.value_counts().to_dict()
except Exception as e: out["holdout_lang"]=str(e)
out["eval_summary"]=pd.read_csv("data/processed/eval_summary_holdout.csv").round(3).to_dict("records"); out["eval_stance"]=json.load(open("data/processed/eval_stance.json")); out["eval_outcome"]=json.load(open("data/processed/eval_outcome.json"))
V=pd.read_csv("outputs/quote_verification.csv"); out["quotes"]=dict(n=len(V),verbatim=int(V.verbatim_in_raw.sum()),pii=int(V.pii_flag.sum()),sources=V.source.value_counts().to_dict())
json.dump(out,open("outputs/validation_numbers.json","w"),indent=1,default=str); print(json.dumps(out,indent=1,default=str)[:2500])
