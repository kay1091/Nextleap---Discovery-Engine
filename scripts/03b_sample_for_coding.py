"""Stage 3b: draw (1) an OPEN-CODING sample (for codebook building) and later (2) TRAIN-LABEL and (3) HOLDOUT samples from the SIP-journey core.
Samples are disjoint. Seeds fixed. Stratified by source so that no one source dominates what the analyst reads."""
import pandas as pd, numpy as np, sys
core=pd.read_csv("data/processed/corpus_relevant.csv"); core=core[core.journey_core&(core.n_words>=10)]
core["strat"]=np.where(core.source.isin(["playstore","appstore"]),np.where(core["product"]=="Groww","review_groww","review_comparator"),np.where(core.source=="reddit",core.kind.map(lambda k:"reddit_"+k),core.source))
print(core.strat.value_counts())
rng=np.random.RandomState(42)
def draw(df,quota,exclude=()):
    out=[]
    for s,q in quota.items():
        pool=df[(df.strat==s)&(~df.doc_id.isin(exclude))]; out.append(pool.sample(min(q,len(pool)),random_state=rng))
    return pd.concat(out)
mode=sys.argv[1]
import re
POOLS={
 "payment_mandate":r"autopay|auto-pay|mandate|nach|bounce|insufficient|not (deducted|debited)|failed|rejected|e-?mandate|upi",
 "pause_cancel_modify":r"pause|cancel|stop(ped)? (my )?sip|modify|change (the )?(date|amount)|can't find|how (do|to) i (stop|cancel)",
 "support_refund":r"customer (care|support|service)|refund|ticket|no response|stuck|pending",
 "metrics_confusion":r"xirr|nav|why (is|are|am).{0,20}(red|negative|loss)|absolute return|returns? (is|are) (negative|low)|in red|negative return|cagr",
 "fees":r"charge|fee|\b(rs|₹)\.? ?\d+.{0,20}(deduct|penalty)|stamp duty|brokerage",
 "cash_need":r"emi|loan|salary|expens|job|cash|emergency|afford|income|pocket money|student",
 "market_fall":r"crash|correction|market (fall|down|drop)|fall(ing)?|bear|red",
 "low_returns":r"returns? (is|are)? ?(low|poor|bad)|underperform|nothing|no (growth|returns)|compared? (to|with)|better than fd|\bfd\b|index fund",
 "step_up_features":r"step[- ]?up|weekly sip|daily sip|flexible|reminder|notification|feature|option to",
 "first_time":r"first (time|sip)|beginner|new to|just started|started (a |my )?sip|newbie|fresher",
 "continue_hold":r"still (doing|continu)|continu(e|ing)|never stopp|didn't stop|did not stop|keep (doing|going)|regret",
 "advice_question":r"should i|is it (ok|good|fine)|what (should|to do)|please (help|suggest)|advice",
}
def draw_targeted(df,per,exclude):
    out=[]
    for k,rx in POOLS.items():
        pool=df[(~df.doc_id.isin(exclude))&df.text.str.contains(rx,regex=True,flags=re.I)]
        # balance sources inside each pool
        take=[]; srcs=pool.strat.unique()
        for s_ in srcs:
            p=pool[pool.strat==s_]; take.append(p.sample(min(max(1,per//len(srcs)+1),len(p)),random_state=rng))
        t=pd.concat(take); out.append(t.sample(min(per,len(t)),random_state=rng).assign(pool=k))
    return pd.concat(out)
if mode=="label":
    opened=set(pd.read_csv("data/processed/sample_open_coding.csv").doc_id)
    hold=core[~core.doc_id.isin(opened)].sample(150,random_state=11).assign(pool="random_holdout"); hold.to_csv("data/processed/holdout_unlabelled.csv",index=False)
    ex=opened|set(hold.doc_id)
    tr_rand=core[~core.doc_id.isin(ex)].sample(150,random_state=12).assign(pool="random_train")
    ex2=ex|set(tr_rand.doc_id)
    tr_t=draw_targeted(core,13,ex2).drop_duplicates("doc_id")
    tr=pd.concat([tr_rand,tr_t]).drop_duplicates("doc_id"); tr.to_csv("data/processed/train_unlabelled.csv",index=False)
    print(len(hold),len(tr),tr.pool.value_counts().to_dict())
if mode=="open":
    q={"review_groww":50,"review_comparator":25,"reddit_post":45,"reddit_comment":45,"youtube":40,"tradingqna":35,"x":10}
    s=draw(core,q); s.to_csv("data/processed/sample_open_coding.csv",index=False)
