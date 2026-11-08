"""Stage 5: quantification, opportunity scorecard, funnel, involuntary/voluntary split, segments, continuers vs droppers, triangulation, charts.
Reads corpus_final.csv (+ audit_precision.csv if present).  Writes tables to outputs/ and PNGs to charts/."""
import sys; sys.path.insert(0,"scripts")
import pandas as pd, numpy as np, json, os, re, glob
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from codebook import CODES, GROUPS
from areas import AREAS, SOURCE_FAMILY
os.makedirs("outputs",exist_ok=True); os.makedirs("charts",exist_ok=True)
d=pd.read_csv("data/processed/corpus_final.csv",low_memory=False); d["codes"]=d.codes.fillna("")
d["family"]=d.source.map(SOURCE_FAMILY); N=len(d)
CN=list(CODES)
d["codes_regex_only"]=d.codes_regex_only.fillna("")
for c in CN: d["c_"+c]=d.codes.str.split(",").apply(lambda l:c in l)
d["c_IA_ALERTS"]=d.codes_regex_only.str.contains("IA_ALERTS")   # revised after precision audit: ML-AND variant kept only 10 docs; regex-only rule audited at 0.50 precision
for a,v in AREAS.items(): d["a_"+a]=d[["c_"+c for c in v["codes"]]].any(axis=1)
fams=sorted(d.family.unique()); fam_n=d.family.value_counts()
BIG=[f for f in fams if fam_n[f]>=100]            # families big enough to enter the source-balanced average
R={}                                              # headline numbers for the report
# ---------- 1 coverage ----------
raw={}
for f in glob.glob("data/raw/*.jsonl"): raw[os.path.basename(f)]=sum(1 for _ in open(f))
corpus_all=pd.read_csv("data/processed/corpus_all.csv",low_memory=False,usecols=["source","product","spam","relevant","journey_core","lang_group"])
rel=pd.read_csv("data/processed/corpus_relevant.csv",low_memory=False,usecols=["source","journey_core"])
cov=corpus_all.groupby("source").agg(unique_docs=("source","size"),flagged_spam=("spam",lambda s:(s.fillna("")!="").sum())).join(rel.groupby("source").size().rename("relevant_nonspam")).join(rel.groupby("source").journey_core.sum().rename("sip_journey_core"))
rawmap={"playstore":["playstore_raw.jsonl","playstore_regional_raw.jsonl"],"appstore":["appstore_raw.jsonl"],"reddit":["reddit_posts_raw.jsonl","reddit_comments_raw.jsonl"],"youtube":["youtube_raw.jsonl"],"tradingqna":["forums_raw.jsonl"],"valuepickr":["forums_raw.jsonl"],"x":["x_raw.jsonl"]}
forums=[json.loads(l)["source"] for l in open("data/raw/forums_raw.jsonl")]
cov["raw_records"]=[ (sum(raw[f] for f in rawmap[s]) if s not in("tradingqna","valuepickr") else forums.count(s)) for s in cov.index]
cov=cov[["raw_records","unique_docs","flagged_spam","relevant_nonspam","sip_journey_core"]]; cov.loc["TOTAL"]=cov.sum()
cov.to_csv("outputs/coverage_by_source.csv"); print(cov)
R["coverage"]=cov.reset_index().to_dict("records")
# play/app breakdown by product
pp=corpus_all[corpus_all.source.isin(["playstore","appstore"])].groupby(["source","product"]).size().unstack(0).fillna(0).astype(int); pp.to_csv("outputs/coverage_store_by_product.csv"); print(pp)
lang=corpus_all.lang_group.value_counts(); lang.to_csv("outputs/language_mix_all_unique.csv"); R["lang_core"]=d.lang_group.value_counts().to_dict()
# ---------- 2 code + area frequencies ----------
def prev(mask_col):
    out={}
    for f in fams: out[f]=100*d.loc[d.family==f,mask_col].mean()
    return out
rows=[]
for c in CN:
    p=prev("c_"+c); n=int(d["c_"+c].sum())
    rows.append(dict(code=c,group=CODES[c][0],definition=CODES[c][1],n_docs=n,pct_all=100*n/N,**{"pct_"+f:p[f] for f in fams},balanced_pct=np.mean([p[f] for f in BIG]),n_families_ge10=int(sum(((d.family==f)&d["c_"+c]).sum()>=10 for f in fams))))
CF=pd.DataFrame(rows).sort_values("n_docs",ascending=False); CF.to_csv("outputs/code_frequencies.csv",index=False)
rows=[]
for a,v in AREAS.items():
    col="a_"+a; p=prev(col); n=int(d[col].sum())
    rows.append(dict(area=a,name=v["name"],codes="+".join(v["codes"]),n_docs=n,pct_all=100*n/N,**{"pct_"+f:p[f] for f in fams},balanced_pct=np.mean([p[f] for f in BIG]),
                     n_families_ge10=int(sum(((d.family==f)&d[col]).sum()>=10 for f in fams)),n_families_ge_0p5pct=int(sum(p[f]>=0.5 for f in fams if fam_n[f]>=100))))
AF=pd.DataFrame(rows)
# ---------- 3 severity ----------
d["low_rating"]=d.rating.notna()&(d.rating<=2); rated=d.rating.notna()
base_low=d[rated].low_rating.mean()
sev=[]
for a in AREAS:
    m=d["a_"+a]; nr=int((m&rated).sum())
    sev.append(dict(area=a,stop_lang_pct=100*d.loc[m,"stop_lang"].mean(),stop_lang_fp_pct=100*d.loc[m,"stop_lang_first_person"].mean(),n_rated=nr,low_rating_pct=(100*d.loc[m&rated,"low_rating"].mean() if nr>=20 else np.nan),
                    experience_share_pct=100*(d.loc[m,"stance_pred"]=="E").mean()))
SV=pd.DataFrame(sev); base_stop=100*d.stop_lang.mean()
R["base_stop_pct"]=base_stop; R["base_low_rating_pct"]=100*base_low
# ---------- 4 audit precision (if present) ----------
if os.path.exists("outputs/audit_precision_by_area.csv"):
    AP=pd.read_csv("outputs/audit_precision_by_area.csv"); AF=AF.merge(AP[["area","audit_n","audit_precision"]],on="area",how="left")
else: AF["audit_n"]=np.nan; AF["audit_precision"]=np.nan
AF["adj_balanced_pct"]=AF.balanced_pct*AF.audit_precision.fillna(1.0)
# ---------- 5 scorecard ----------
S=AF.merge(SV,on="area"); S["mech"]=S.area.map(lambda a:AREAS[a]["mech"]); S["type"]=S.area.map(lambda a:AREAS[a]["type"])
def mm(x): x=pd.Series(x,dtype=float); return (x-x.min())/(x.max()-x.min()+1e-9)
S["freq_score"]=mm(S.adj_balanced_pct)
sevraw=0.5*mm(S.stop_lang_pct)+0.5*mm(S.low_rating_pct.fillna(S.low_rating_pct.median()))
S["sev_score"]=sevraw
S["link_score"]=(S.mech-1)/4
# confidence: source diversity + sample size + audit precision
S["conf_score"]=(0.4*(S.n_families_ge10/ max(1,len(fams))) + 0.3*np.minimum(1,np.log10(S.n_docs.clip(lower=1))/3) + 0.3*S.audit_precision.fillna(0.5)).clip(0,1)
W=dict(freq=0.30,sev=0.25,link=0.30,conf=0.15)
S["priority"]=W["freq"]*S.freq_score+W["sev"]*S.sev_score+W["link"]*S.link_score+W["conf"]*S.conf_score
S["rank"]=S.priority.rank(ascending=False,method="min").astype(int)
alt={"equal weights":dict(freq=.25,sev=.25,link=.25,conf=.25),"metric-link heavy":dict(freq=.15,sev=.2,link=.55,conf=.1),"frequency heavy":dict(freq=.55,sev=.15,link=.2,conf=.1)}
for k,w in alt.items():
    pr=w["freq"]*S.freq_score+w["sev"]*S.sev_score+w["link"]*S.link_score+w["conf"]*S.conf_score; S["rank_"+k.replace(" ","_")]=pr.rank(ascending=False,method="min").astype(int)
S=S.sort_values("rank"); S.to_csv("outputs/opportunity_scorecard.csv",index=False)
print(S[["rank","area","name","n_docs","balanced_pct","adj_balanced_pct","stop_lang_pct","low_rating_pct","mech","n_families_ge10","audit_precision","priority","rank_equal_weights","rank_metric-link_heavy","rank_frequency_heavy"]].round(2).to_string())
# ---------- 6 funnel + involuntary/voluntary ----------
lapse=d[(d.lapse_class!="")&d.lapse_class.notna()|d.stop_lang]
lapse=lapse.copy(); lapse["lapse_class"]=lapse.lapse_class.fillna("").replace("","lapse-language only")
STAGES=["Pre/at set-up","M0-1","M2-3","M4-6","M7-12","M12+","unknown"]
F=lapse.groupby(["stage","lapse_class"]).size().unstack(fill_value=0).reindex(STAGES).fillna(0).astype(int); F["total"]=F.sum(1); F.to_csv("outputs/funnel_stage_by_lapse_class.csv"); print(F)
Fcue=lapse[lapse.stage_basis=="time cue"].groupby(["stage","lapse_class"]).size().unstack(fill_value=0); Fcue.to_csv("outputs/funnel_time_cue_only.csv")
IV=lapse.groupby("family").lapse_class.value_counts().unstack(fill_value=0); IV["total"]=IV.sum(1); IV.loc["ALL"]=IV.sum(); IV.to_csv("outputs/invol_vol_by_family.csv"); print(IV)
tot=lapse.lapse_class.value_counts(); R["lapse_class"]=tot.to_dict(); R["n_lapse_evidence"]=len(lapse)
# per-code drop-off reasons among lapse docs by stage (specific reasons funnel)
reason_cols=["SI_FAILED","SI_MANDATE","SI_STUCK","SI_ZOMBIE","SI_HALT","SV_MARKET","SV_RETURNS","SV_CASH","SV_SWITCH","SV_DISTRUST","SV_FEES"]
lc=lapse[lapse.stage_basis=="time cue"]    # primary funnel = ONLY docs whose stage comes from an explicit time cue (code-default stages would be circular)
RF=pd.DataFrame({r:lc.groupby("stage")["c_"+r].sum() for r in reason_cols}).reindex(STAGES).fillna(0).astype(int); RF["n_docs"]=lc.groupby("stage").size().reindex(STAGES); RF.to_csv("outputs/funnel_reasons_by_stage_timecue.csv"); print(RF)
FC=lc.groupby(["stage","lapse_class"]).size().unstack(fill_value=0).reindex(STAGES[:-1]).fillna(0).astype(int); FC["total"]=FC.sum(1); FC.to_csv("outputs/funnel_stage_by_lapse_class_timecue.csv"); print(FC)
# ---------- 7 segments ----------
seg_rows=[]
for col in ["seg_occupation","seg_age","seg_income_stability","seg_money_source","seg_influence"]:
    x=d[d[col].notna()].copy()
    if col=="seg_influence": x=x.assign(**{col:x[col].str.split("|")}).explode(col)
    for k,g in x.groupby(col):
        row=dict(attribute=col,segment=k,n_docs=len(g),inv_pct=100*g.codes.str.contains("SI_").mean(),vol_pct=100*g.codes.str.contains("SV_").mean(),stop_lang_pct=100*g.stop_lang.mean(),
                 **{a+"_pct":100*g["a_"+a].mean() for a in AREAS})
        row["flag"]="n<30: anecdotal" if len(g)<30 else ""
        seg_rows.append(row)
SG=pd.DataFrame(seg_rows); SG.to_csv("outputs/segment_differences.csv",index=False)
segcov=pd.read_csv("data/processed/segment_coverage.csv"); segcov.to_csv("outputs/segment_coverage.csv",index=False)
print(SG[["attribute","segment","n_docs","inv_pct","vol_pct","stop_lang_pct","A1_pct","A3_pct","A4_pct","A6_pct","A7_pct"]].round(1).to_string())
# ---------- 8 continuers vs droppers ----------
CONT=re.compile(r"(still|been|am|keep|kept|continu\w+|running|doing|going).{0,30}(sip|investing)\b.{0,40}(since|for|from)|never (stopped|paused|missed|skipped)|haven'?t (stopped|missed|paused)|(\d+|\w+) (years?|yrs?) (of )?(sip|investing)|continu(e|ed|ing) (my |the )?sips?|didn'?t stop|did not stop|not stopp?ing",re.I)
d["cohort"]=np.where(d.stop_lang_first_person&(d.stance_pred=="E"),"dropper (first-person stop/pause/fail language)",np.where(d.text.str.contains(CONT)&~d.stop_lang&(d.stance_pred=="E"),"continuer (first-person continuing language)","other"))
cc=d[d.cohort!="other"]; R["cohort_n"]=cc.cohort.value_counts().to_dict()
rows=[]
for c in CN:
    a=cc[cc.cohort.str.startswith("dropper")]["c_"+c].mean()*100; b=cc[cc.cohort.str.startswith("continuer")]["c_"+c].mean()*100
    rows.append(dict(code=c,dropper_pct=a,continuer_pct=b,diff_pp=a-b,ratio=(a+0.5)/(b+0.5)))
CD=pd.DataFrame(rows).sort_values("diff_pp"); CD.to_csv("outputs/continuers_vs_droppers.csv",index=False)
# ---------- 9 checking behaviour ----------
CHK=[("multiple times a day / daily",r"(daily|every ?day|everyday|day ?to ?day|every morning|multiple times a day|several times a day|hourly|regularly)\W+(\w+\W+){0,6}(check|look|open|track|monitor)|(check|look(ing)?|open|track|monitor)\w*\W+(\w+\W+){0,6}(daily|every ?day|everyday|multiple times a day|several times a day|hourly|all the time|constantly)"),
     ("weekly",r"(check|look|review|track|monitor)\w*\W+(\w+\W+){0,6}(weekly|every week|once a week|each week)|weekly (check|review)"),
     ("monthly / after each instalment",r"(check|look|review|track|monitor)\w*\W+(\w+\W+){0,6}(monthly|every month|once a month|each month|once in a month)|monthly (check|review)"),
     ("quarterly / yearly / rarely",r"(check|look|review|track|monitor)\w*\W+(\w+\W+){0,6}(quarterly|every (three|3|six|6) months|yearly|annually|once a year|twice a year|rarely|once in a while|seldom)|(quarterly|annual|yearly|half[- ]yearly) (check|review)|don'?t (check|look|track)|never (check|look)|(forget|forgot)ten? (about )?(it|them|my sips?)|set and forget|put and forget")]
rows=[]
for k,rx in CHK:
    m=d.text.str.contains(rx,flags=re.I,regex=True); rows.append(dict(cadence=k,n_docs=int(m.sum()),pct_of_core=100*m.mean(),sources=int((d[m].family.value_counts()>=5).sum())))
CK=pd.DataFrame(rows); CK.to_csv("outputs/checking_cadence.csv",index=False); print(CK)
d["checks_any"]=d.text.str.contains(r"check(ing)? (my )?(portfolio|sip|returns?|nav|app|investments?|folio)|(track|monitor)(ing)? (my )?(portfolio|sip|returns?|investments?)|portfolio (check|review)",flags=re.I,regex=True)
R["checks_any_n"]=int(d.checks_any.sum())
# ---------- 10 Groww view ----------
d["is_groww"]=d.products_mentioned.fillna("").str.contains("Groww")
G=d[d.is_groww]; R["groww_n"]=len(G)
GA=pd.DataFrame({"area":list(AREAS),"name":[v["name"] for v in AREAS.values()],"groww_n":[int(G["a_"+a].sum()) for a in AREAS],"groww_pct":[100*G["a_"+a].mean() for a in AREAS],"all_pct":[100*d["a_"+a].mean() for a in AREAS]}); GA.to_csv("outputs/groww_only_areas.csv",index=False)
# ---------- 11 triangulation ----------
T=[]
for a in AREAS:
    r=AF[AF.area==a].iloc[0]; fam_counts={f:int((d.family==f).__and__(d["a_"+a]).sum()) for f in fams}
    ok=[f for f in fams if fam_counts[f]>=10 and 100*fam_counts[f]/fam_n[f]>=0.5]
    T.append(dict(area=a,name=AREAS[a]["name"],**{"n_"+f:fam_counts[f] for f in fams},independent_families_confirming=len(ok),families=", ".join(ok),triangulated=len(ok)>=2))
pd.DataFrame(T).to_csv("outputs/triangulation_areas.csv",index=False)
T2=[]
for c in CN:
    ok=[f for f in fams if ((d.family==f)&d["c_"+c]).sum()>=10 and 100*((d.family==f)&d["c_"+c]).sum()/fam_n[f]>=0.5]; T2.append(dict(code=c,independent_families=len(ok),families=", ".join(ok)))
pd.DataFrame(T2).to_csv("outputs/triangulation_codes.csv",index=False)
# stance / outcome distribution
R["stance_pred"]=d.stance_pred.value_counts().to_dict(); R["outcome_pred_E"]=d[d.stance_pred=="E"].outcome_pred.value_counts().to_dict(); R["N_core"]=N
R["n_years"]=d.date.str[:4].value_counts().sort_index().to_dict() if d.date.notna().any() else {}
json.dump(R,open("outputs/headline_numbers.json","w"),default=str,indent=1)
# ---------- charts ----------
plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False})
c=cov.drop("TOTAL")
fig,ax=plt.subplots(figsize=(8,3.8)); x=np.arange(len(c)); ax.bar(x-0.27,c.unique_docs,0.27,label="unique docs"); ax.bar(x,c.relevant_nonspam,0.27,label="SIP/MF-relevant (non-spam)"); ax.bar(x+0.27,c.sip_journey_core,0.27,label="SIP-journey core (analysed)")
ax.set_xticks(x); ax.set_xticklabels(c.index,rotation=20); ax.set_yscale("log"); ax.set_ylabel("documents (log)"); ax.legend(frameon=False); ax.set_title("Data funnel by source"); plt.tight_layout(); plt.savefig("charts/01_data_funnel_by_source.png",dpi=160); plt.close()
top=CF.sort_values("balanced_pct").tail(22); colmap=dict(zip(GROUPS,plt.cm.tab10.colors))
fig,ax=plt.subplots(figsize=(8,6)); ax.barh(top.code,top.balanced_pct,color=[colmap[g] for g in top.group]); ax.set_xlabel("% of SIP-journey docs (source-balanced mean across families)"); ax.set_title("Top 22 coded themes (raw coder output, before precision audit)")
from matplotlib.patches import Patch; ax.legend(handles=[Patch(color=colmap[g],label=GROUPS[g]) for g in GROUPS],frameon=False,fontsize=7,loc="lower right"); plt.tight_layout(); plt.savefig("charts/02_theme_frequency.png",dpi=160); plt.close()
fig,ax=plt.subplots(figsize=(11,5)); s=S.sort_values("priority"); ax.barh(s.area+" "+s.name.str[:62],s.priority,color=["#c0392b" if t.startswith("involuntary") else "#2874a6" for t in s.type]); ax.set_xlabel("priority score 0-1 (weights: frequency .30, severity .25, metric-link .30, confidence .15)"); ax.set_title("Opportunity scorecard (red = involuntary, blue = voluntary/mixed)"); plt.tight_layout(); plt.savefig("charts/03_opportunity_scorecard.png",dpi=160); plt.close()
fig,ax=plt.subplots(figsize=(8,4)); FF=FC.drop("Pre/at set-up",errors="ignore")[[c for c in ["involuntary","voluntary","both","lapse-language only"] if c in FC.columns]]; FF.plot(kind="bar",stacked=True,ax=ax,color=["#c0392b","#2874a6","#8e44ad","#aab7b8"]); ax.set_ylabel("docs with lapse evidence"); ax.set_title("Lapse evidence by journey stage (only docs with an explicit time cue)"); plt.xticks(rotation=0); ax.legend(frameon=False); plt.tight_layout(); plt.savefig("charts/04_funnel_dropoff_stage.png",dpi=160); plt.close()
fig,ax=plt.subplots(figsize=(8,3.6)); p=IV.drop("ALL"); p=p[[c for c in ["involuntary","voluntary","both","lapse-language only"] if c in p.columns]]; (p.div(p.sum(1),axis=0)*100).plot(kind="barh",stacked=True,ax=ax,color=["#c0392b","#2874a6","#8e44ad","#aab7b8"]); ax.set_xlabel("% of lapse-evidence docs"); ax.set_title("Involuntary vs voluntary lapse evidence by source family"); ax.legend(frameon=False,fontsize=7,bbox_to_anchor=(1,1)); plt.tight_layout(); plt.savefig("charts/05_involuntary_vs_voluntary.png",dpi=160); plt.close()
sg=SG[(SG.n_docs>=30)&SG.attribute.isin(["seg_occupation","seg_age","seg_income_stability","seg_money_source","seg_influence"])]
if len(sg):
    hm=sg.set_index(sg.attribute.str.replace("seg_","")+": "+sg.segment+" (n="+sg.n_docs.astype(str)+")")[[a+"_pct" for a in AREAS]]; hm.columns=list(AREAS); hm=hm.drop(columns=["A4"])  # A4 (cash-flow) shares cue words with income/occupation tags -> circular, excluded
    fig,ax=plt.subplots(figsize=(8,max(3,0.32*len(hm)+1.2))); im=ax.imshow(hm.values,cmap="Blues",aspect="auto"); ax.set_xticks(range(len(hm.columns))); ax.set_xticklabels(hm.columns); ax.set_yticks(range(len(hm))); ax.set_yticklabels(hm.index,fontsize=7)
    for i in range(hm.shape[0]):
        for j in range(hm.shape[1]): ax.text(j,i,f"{hm.values[i,j]:.0f}",ha="center",va="center",fontsize=6.5)
    ax.set_title("Segments (n>=30 only): % of segment docs mentioning each opportunity area"); plt.tight_layout(); plt.savefig("charts/06_segment_heatmap.png",dpi=160); plt.close()
x=CD[(CD.dropper_pct+CD.continuer_pct)>=3].copy(); x=pd.concat([x.head(8),x.tail(8)]).drop_duplicates()
fig,ax=plt.subplots(figsize=(8,4.5)); ax.barh(x.code,x.diff_pp,color=["#2e86c1" if v<0 else "#c0392b" for v in x.diff_pp]); ax.axvline(0,color="k",lw=.6); ax.set_xlabel("dropper % minus continuer % (percentage points)"); ax.set_title(f"Droppers vs continuers (n={R['cohort_n']})"); plt.tight_layout(); plt.savefig("charts/07_droppers_vs_continuers.png",dpi=160); plt.close()
print("done")
