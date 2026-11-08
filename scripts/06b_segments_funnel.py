"""Stage 4a: add rule-based attributes to corpus_coded.csv: explicit stop/pause language, journey stage (time cue or code default), segment tags
(age band, occupation, income stability, source of money, influence) and involuntary/voluntary lapse class.  Output: data/processed/corpus_final.csv
All tags are regex tags on self-descriptions; coverage is reported honestly in segment_coverage.csv."""
import pandas as pd, numpy as np, re
d=pd.read_csv("data/processed/corpus_coded.csv"); d["codes"]=d.codes.fillna(""); d["text"]=d.text.fillna("")
I=re.I
# ---- explicit lapse language (first-person or generic) ----
STOP=re.compile(r"(stopp?ed|paus(ed|ing)|cancel+(ed|led|ing)?|discontinu(ed|ing)|closed|quit|ended|terminat(ed|ing)|skipp?ed|bounced|failed|reduc(ed|ing)|lowered|decreas(ed|ing)).{0,25}(my |the |all |a |an |our |those |these )?(\w+ ){0,2}(sips?|instal+ments?|mandates?|autopay|auto-pay)|(sips?|instal+ments?|mandates?|autopay|auto-pay)\W+(\w+\W+){0,3}(stopp?ed|paused|cancel+ed|discontinued|failed|bounced|rejected|skipped|got (cancel|stopp|paus)\w+|was (cancel|stopp|paus)\w+|not (deducted|debited|executed|processed))|band (kar|kiya|ho)|bandh (kar|ho|kiya)|(sip|mandate) (fail|bounce)|stop(ping)? (my |the )?(sips?)|\bwant to stop\b|thinking (of|about) (stopping|pausing|cancelling|canceling)|should i (stop|pause|cancel|discontinue)", I)
d["stop_lang"]=d.text.str.contains(STOP)
d["stop_lang_first_person"]=d.stop_lang & d.text.str.contains(r"\b(i|my|me|we|our|maine|mera|meri|mere)\b",flags=I,regex=True)
# ---- stage tags ----
def months_cue(t):
    t=t.lower()
    if re.search(r"first (month|instal+ment|sip)|just (started|began|setup|set up)|(started|began|setup|set up|created) (a |my )?(sip )?(today|yesterday|last (week|few days)|this week|recently)|new(ly)? (started|investor)|brand new|1st (month|instal|sip)|about to start|want(ed)? to start|planning to start|(will|going to) start|how (to|do i) start|can i start|should i start", t): return "M0-1"
    m=re.findall(r"(\d+(?:\.\d+)?)\s*[- ]?(months?|mos?\b|yrs?|years?|weeks?)",t)
    vals=[]
    for n,u in m:
        n=float(n)
        if u.startswith("week"): vals.append(n/4.3)
        elif u.startswith("m"): vals.append(n)
        else: vals.append(n*12)
    # only treat as tenure if there is a sip-experience verb nearby
    if vals and re.search(r"(doing|running|since|for|invest(ing|ed)|continu\w+|past|last|completed|done|started|sip)\b.{0,40}\d+\s*[- ]?(months?|mos?\b|yrs?|years?)|\d+\s*[- ]?(months?|mos?\b|yrs?|years?)\s*(of|into|since|ago|now|old|back)",t):
        v=max(vals) if len(vals)==1 else min(vals)
        if v<=1.5: return "M0-1"
        if v<=3.5: return "M2-3"
        if v<=6.5: return "M4-6"
        if v<=12.5: return "M7-12"
        if v<=240: return "M12+"
    return None
STAGE_DEF={"IA_ONBOARD":"Pre/at set-up","ST_NEED_GUIDE":"Pre/at set-up","SI_MANDATE":"Pre/at set-up","ST_GOAL":"Pre/at set-up","ST_SMALL_HABIT":"Pre/at set-up","ST_EXPECT_RET":"Pre/at set-up","ST_SOCIAL":"Pre/at set-up","ST_TAX":"Pre/at set-up","ST_VS_FD":"Pre/at set-up",
 "SI_FAILED":"M0-1","SI_STUCK":"M0-1","BH_RED":"M2-3","BH_CHECK":"M2-3","BH_UNDERWHELM":"M4-6","SV_RETURNS":"M4-6","SV_MARKET":"M4-6","BH_TIMING":"M4-6","SV_CASH":"M7-12","SV_SWITCH":"M7-12","BH_FORGET":"M7-12","SI_ZOMBIE":"M7-12","BH_STEPUP":"M7-12","CO_THROUGH":"M12+"}
STAGES=["Pre/at set-up","M0-1","M2-3","M4-6","M7-12","M12+"]
st=[];ss=[]
for t,c in zip(d.text,d.codes):
    cu=months_cue(t)
    if cu: st.append(cu); ss.append("time cue")
    else:
        cs=[x for x in c.split(",") if x in STAGE_DEF]
        if cs: st.append(STAGE_DEF[cs[0]]); ss.append("inferred from code")
        else: st.append("unknown"); ss.append("unknown")
d["stage"]=st; d["stage_basis"]=ss
d["stage"]=d.stage.replace({"M0-1":"M0-1"})
# ---- segments ----
def first(rx,t): 
    m=re.search(rx,t,I); return m
def age(t):
    m=re.search(r"\b(?:i am|i'm|im|age[d]?|aged|my age is|turning)\s*:?\s*(\d{2})\b(?!\s*(?:%|k|l\b|lakh|cr|yrs? of|years? of|months?))",t,I) or re.search(r"\b(\d{2})\s?(?:m|f|male|female|yo|y/o|yrs? old|years? old)\b(?!\w)",t,I)
    if m:
        a=int(m.group(1))
        if 16<=a<=70: return "<=24" if a<=24 else ("25-34" if a<=34 else ("35-44" if a<=44 else "45+"))
    return None
OCC=[("student",r"\bstudents?\b|college|pocket money|\bb\.?tech\b|\bmba\b|hostel|university|class (11|12)|\bschool\b|intern(ship)?\b|stipend"),
     ("salaried",r"salar(y|ied)|\bctc\b|\bin-hand\b|take[- ]home|my (job|employer|company)|work(ing)? (in|at|for) (an? )?(it|mnc|company|corporate|bank|software)|software (engineer|developer)|corporate|\bsde\b|bonus|appraisal|\bhike\b|in my 20s|first job|fresher|\bwfh\b"),
     ("self-employed/freelance/gig",r"freelanc|self[- ]employed|\bmy (own )?business\b|business owner|shop(keeper)?|gig|consultant|contract(or|ual)|\bstartup founder|irregular income|variable income|commission[- ]based|uncertain income|\bdriver\b|delivery partner"),
     ("homemaker/retired/other",r"homemaker|housewife|house wife|retired|pension(er)?|\bparents'? (sip|money)\b")]
def occ(t):
    for k,rx in OCC:
        if re.search(rx,t,I): return k
    return None
def incstab(t):
    if re.search(r"irregular income|variable income|uncertain income|income (is )?(not )?(stable|fluctuat)|unstable income|income (varies|fluctuat)|commission[- ]based|no fixed income|job loss|lost (my )?job|laid off|layoff|between jobs|unemploy|job (is )?(unstable|insecure)|salary (delay|cut)|pay ?cut|freelanc|self[- ]employed",t,I): return "irregular/at-risk"
    if re.search(r"stable (income|job)|fixed (income|salary)|regular (income|salary)|government job|govt job|steady (income|job)|monthly salary|salary (credit|date|comes|gets credited)|\bsalaried\b",t,I): return "stable/regular"
    return None
def money(t):
    if re.search(r"pocket money|from (my )?(parents|dad|father|mom|mother)|parents? (give|gave|sends?|funds?|money)",t,I): return "family/pocket money"
    if re.search(r"bonus|windfall|inheritance|\bsold (my|a) (house|flat|land|property|car)|maturity|lump ?sum from|(side|extra) (income|hustle)|dividend income",t,I): return "bonus/windfall/side income"
    if re.search(r"from (my )?(monthly )?(salary|income|savings)|(out of|part of) (my )?(salary|income)|monthly (savings|surplus)|salary|take[- ]home|in-hand|\bemi\b.{0,30}(sip|invest)|savings",t,I): return "salary/regular savings"
    return None
def infl(t):
    out=[]
    if re.search(r"(friend|colleague|cousin|relative|parents?|dad|father|mom|mother|brother|sister|husband|wife|uncle|senior|boss)s?.{0,60}(told|suggest|recommend|advis|showed|convinc|introduc|started|asked)|(told|suggest|recommend|advis|convinc|inspired).{0,40}(by|from).{0,20}(friend|colleague|parents?|cousin)",t,I): out.append("friends/family")
    if re.search(r"youtube|\byt\b|finfluencer|influencer|your (video|channel)|(watched|saw|seen).{0,25}(video|reel|channel)|podcast|instagram|reel|twitter|\bx\.com",t,I): out.append("creator/social media")
    if re.search(r"\b(bank|relationship manager|\brm\b|distributor|agent|advisor|adviser|financial planner|broker)\b.{0,50}(told|said|suggest|sold|recommend|advis|push|pitch)",t,I): out.append("bank/agent/advisor")
    if re.search(r"(app|groww|zerodha|paytm|phonepe|google pay).{0,30}(ad|advert|promo|banner|notification|suggest|recommended?)|saw (an )?ad\b",t,I): out.append("app/ad prompt")
    return "|".join(out) if out else None
d["seg_age"]=[age(t) for t in d.text]; d["seg_occupation"]=[occ(t) for t in d.text]; d["seg_income_stability"]=[incstab(t) for t in d.text]
d["seg_money_source"]=[money(t) for t in d.text]; d["seg_influence"]=[infl(t) for t in d.text]
d.loc[d.seg_occupation.eq("student")&d.seg_money_source.isna(),"seg_money_source"]=None
# ---- involuntary vs voluntary ----
def lapse_class(c,stop):
    cs=set(c.split(","))
    inv=bool(cs&{"SI_FAILED","SI_MANDATE","SI_STUCK","SI_ZOMBIE","SI_HALT"}); vol=bool(cs&{"SV_MARKET","SV_RETURNS","SV_CASH","SV_SWITCH","SV_DISTRUST","SV_FEES"})
    return "both" if inv and vol else ("involuntary" if inv else ("voluntary" if vol else ("lapse-language only" if stop else "")))
d["lapse_class"]=[lapse_class(c,s) for c,s in zip(d.codes,d.stop_lang)]
d["is_experience"]=(d.stance_pred=="E")
d.to_csv("data/processed/corpus_final.csv",index=False)
cov=[]
n=len(d)
for k in ["seg_age","seg_occupation","seg_income_stability","seg_money_source","seg_influence"]:
    cov.append(dict(attribute=k,tagged=int(d[k].notna().sum()),pct_of_journey_core=round(100*d[k].notna().mean(),1),pct_of_experience_docs=round(100*d[d.is_experience][k].notna().mean(),1)))
pd.DataFrame(cov).to_csv("data/processed/segment_coverage.csv",index=False); print(pd.DataFrame(cov))
print(d.stage.value_counts()); print(d.stage_basis.value_counts()); print(d.lapse_class.value_counts()); print(d.stop_lang.mean())
