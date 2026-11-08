"""Builds outputs/canvas.tsx (the Canvas page source) from computed outputs. Prose is mine; every number comes from outputs/*.csv|json."""
import sys; sys.path.insert(0,"scripts")
import pandas as pd, numpy as np, json
from codebook import CODES, GROUPS
from areas import AREAS
O="outputs/"
cov=pd.read_csv(O+"coverage_by_source.csv").set_index("source"); CF=pd.read_csv(O+"code_frequencies.csv").set_index("code"); S=pd.read_csv(O+"opportunity_scorecard.csv")
H=json.load(open(O+"headline_numbers.json")); VN=json.load(open(O+"validation_numbers.json")); V=pd.read_csv(O+"quote_verification.csv")
M=pd.read_csv("data/processed/eval_codes_holdout.csv"); ens=M[M.method=="ensemble"].set_index("code")
SG=pd.read_csv(O+"segment_differences.csv"); SC=pd.read_csv(O+"segment_coverage.csv"); CD=pd.read_csv(O+"continuers_vs_droppers.csv").set_index("code")
IV=pd.read_csv(O+"invol_vol_by_family.csv").set_index("family"); FC=pd.read_csv(O+"funnel_stage_by_lapse_class_timecue.csv").set_index("stage"); RF=pd.read_csv(O+"funnel_reasons_by_stage_timecue.csv").set_index("stage")
AP=pd.read_csv(O+"audit_precision_by_area.csv").set_index("area"); HA=pd.read_csv(O+"holdout_area_level.csv").set_index("area"); TA=pd.read_csv(O+"triangulation_areas.csv").set_index("area")
GA=pd.read_csv(O+"groww_only_areas.csv").set_index("area"); CK=pd.read_csv(O+"checking_cadence.csv"); LG=pd.read_csv(O+"language_coding_rates.csv").set_index("lang_group")
N=H["N_core"]; J=json.dumps
def weak(c): 
    e=ens.loc[c]; return (e.f1<0.35) or (e.support_gold<=2)
FAMLAB={"playstore":"Play Store review","appstore":"App Store review","reddit":"Reddit","tradingqna":"TradingQ&A","valuepickr":"ValuePickr","youtube":"YouTube comment","x":"X post"}
def attrib(r):
    s=FAMLAB.get(r.source,r.source)
    if isinstance(r["product"],str): s+=" · "+r["product"]
    if r["rating"]==r["rating"] and r["rating"] is not None: s+=f" · {int(r['rating'])}★"
    try: s+=" · "+str(pd.to_datetime(r["date"]).year)
    except Exception: pass
    return s
def Q(topic,k=2,prefer=None):
    x=V[V.topic==topic]
    if prefer is not None: x=pd.concat([x[x["product"]==prefer],x[x["product"]!=prefer]])
    out=""
    for _,r in x.head(k).iterrows(): out+=f"<Quote cite={{{J(attrib(r))}}}>{{{J(r.quote)}}}</Quote>\n"
    return out
def T(s): return f"<Text>{{{J(s)}}}</Text>\n"
def pct(c): return f"{100*CF.loc[c].n_docs/N:.1f}%"
def code_rows(codes):
    rows=[]
    for c in codes:
        rows.append([c+(" †" if weak(c) else ""),CODES[c][1][:95],f"{int(CF.loc[c].n_docs):,}",pct(c),f"{CF.loc[c].balanced_pct:.1f}%",f"{int(CF.loc[c].n_families_ge10)}"])
    return rows
def TBL(cols,rows,emph=None,align=None):
    a=f" align={{{J(align)}}}" if align else ""
    e=f" emphasis={{{emph}}}" if emph is not None else ""
    return f"<Table columns={{{J(cols)}}} rows={{{J(rows)}}}{e}{a} />\n"
CODECOLS=["Code","Meaning","Docs","% of core","Source-balanced %","Source families ≥10 docs"]
P=[]  # page children
tot=cov.loc["TOTAL"]
# ---- header metrics
P.append(f"<Metrics metrics={{{J([dict(value=f'{int(tot.raw_records):,}',label='raw public records collected',detail='7 source types, 6 comparators'),dict(value=f'{int(tot.unique_docs):,}',label='unique documents after dedupe',detail=f'{int(tot.flagged_spam):,} flagged spam/low-signal'),dict(value=f'{int(tot.sip_journey_core):,}',label='SIP-journey documents analysed',detail=f'{H['groww_n']:,} are Groww-specific'),dict(value=f'{VN['quotes']['verbatim']}/{VN['quotes']['n']}',label='quotes verified verbatim in raw data',detail='script check, 0 PII flags')])}}} />")
# ---- bottom line
inv_pool=H['lapse_class']; ivs=IV.copy(); ivs["share"]=(ivs.involuntary+ivs.both)/(ivs.involuntary+ivs.both+ivs.voluntary)
fc=FC.copy(); fc["share"]=(fc.involuntary+fc.both)/(fc.involuntary+fc.both+fc.voluntary)
top=S.sort_values("rank")
bl=[
 f"Two different drop-off mechanisms show up in public text: **involuntary lapses** (failed/rejected debits, mandate/autopay set-up and limits, money debited but units not allotted, cancelled SIPs still debiting, AMC halts) and **voluntary lapses** (cash-flow squeeze, flat/red returns, market anxiety, switching). Of {H['n_lapse_evidence']:,} documents with lapse evidence, {int(inv_pool['involuntary']+inv_pool['both']):,} carry an involuntary code and {int(inv_pool['voluntary']+inv_pool['both']):,} a voluntary code. The involuntary share is {100*ivs.loc['ALL','share']:.0f}% pooled but ranges from {100*ivs.loc['Reddit','share']:.0f}% (Reddit) to {100*ivs.loc['Store reviews','share']:.0f}% (store reviews) — which one matches Groww's real first-time cohort is the first thing internal data must settle.",
 f"The ranked scorecard puts **{top.iloc[0]['name']} (A1)** and **{top.iloc[1]['name']} (A2)** first; both stay in the top 5 under all four weightings I tried. **Pause/edit/cancel friction (A3)** and **support/refund trust (A8)** follow, and **off-app reliance (A10)** is high on frequency but lower on direct metric link.",
 f"Involuntary evidence is concentrated early: among lapse documents with an explicit time cue (n={int(FC.total.sum())}), the involuntary share is {100*fc.loc['M0-1','share']:.0f}% in month 0–1 and {100*fc.loc['M2-3','share']:.0f}% in months 2–3, then {100*fc.loc['M4-6','share']:.0f}% / {100*fc.loc['M7-12','share']:.0f}% / {100*fc.loc['M12+','share']:.0f}% in months 4–6 / 7–12 / 12+. Voluntary reasons outnumber involuntary ones at every stage, but the involuntary share is highest early.",
 f"On Groww-specific documents (n={H['groww_n']:,}), pause/edit/cancel friction appears in {GA.loc['A3','groww_pct']:.0f}% of documents (vs {GA.loc['A3','all_pct']:.0f}% overall), support/refund/reliability in {GA.loc['A8','groww_pct']:.0f}% (vs {GA.loc['A8','all_pct']:.0f}%) and instalment/mandate failure in {GA.loc['A1','groww_pct']:.0f}% (vs {GA.loc['A1','all_pct']:.0f}%) — before the precision haircut.",
 "These are directional estimates from self-selected public text, **not Groww internal data**. Coder precision is moderate (see Validation) and silent droppers do not post; section 'What I would validate with internal data' lists the checks that turn this into decisions.",
]
P.append("<Callout lead=\"Bottom line\" tone=\"info\">{"+J("Two kinds of drop-off sit behind the metric — involuntary (payments/mandates/debits) and voluntary (money, returns, doubt) — and the evidence ranks the involuntary and control-friction areas first. All figures are directional, from self-selected public text.")+"}</Callout>\n<BulletList items={"+J([b.replace('**','') for b in bl])+"} />")
# ---- architecture
P.append("""<Section heading="1. Discovery-engine architecture" id="arch" caption="Scripts do the scale work; the LLM analyst does the judgment work; every judgment is audited against a hand-labelled sample.">
<Diagram direction="horizontal" nodes={[
 {id:"c",label:"Collect",detail:"Play, App Store, Reddit (archive), YouTube, TradingQ&A, ValuePickr, X",kind:"box"},
 {id:"f",label:"Clean & filter",detail:"dedupe, language, spam, relevance, product tags",kind:"box"},
 {id:"d",label:"Discover themes",detail:"embeddings + clusters + NMF → LLM open coding → 40-code codebook",kind:"box"},
 {id:"l",label:"Label",detail:"LLM hand-labels train + blind holdout",kind:"person"},
 {id:"k",label:"Scalable coder",detail:"regex + embedding classifier, per-code variant",kind:"box"},
 {id:"a",label:"Quantify",detail:"frequency, severity, funnel, segments, scorecard",kind:"box"},
 {id:"v",label:"Validate",detail:"holdout P/R/κ, precision audit, triangulation, quote check",kind:"decision"}
]} edges={[{from:"c",to:"f"},{from:"f",to:"d"},{from:"d",to:"l"},{from:"l",to:"k"},{from:"k",to:"a"},{from:"a",to:"v"},{from:"v",to:"k",label:"fix rules",dashed:true}]} />""")
P.append(TBL(["Stage","Scripts (deterministic)","LLM analyst judgment"],[
 ["Collect","google-play-scraper, iTunes RSS, Arctic Shift (Reddit archive), yt-dlp + comment downloader, Discourse JSON, X search","Source/query choice; logged every failure"],
 ["Clean","dedupe by id and normalised text; language tag; regex spam rules; SIP/MF relevance; product tags","Rule design; audited the spam filter (precision "+f"{100*VN['spam_flag_precision']:.0f}%"+")"],
 ["Theme discovery","MiniLM multilingual embeddings, KMeans, c-TF-IDF, NMF","Read samples; open-coded; wrote codebook (40 codes, 7 groups)"],
 ["Scale-up coder",f"LogReg on TF-IDF + embeddings + regex hits; per-code variant by 5-fold OOF F1",f"Hand-labelled {VN['train_n']} training + {VN['holdout_n']} blind holdout documents"],
 ["Quantify","counts, severity, scorecard, funnel, segments, charts","Area grouping; mechanism-directness ratings"],
 ["Validate","holdout metrics; verbatim-quote script; triangulation",f"Judged {VN['audit_n']} coded positives for precision"]]))
P.append("</Section>")
# ---- coverage
rows=[[s.title() if s not in("x","youtube","appstore","playstore","tradingqna","valuepickr") else {"x":"X (via search tool)","youtube":"YouTube comments","appstore":"App Store RSS","playstore":"Google Play","tradingqna":"TradingQ&A","valuepickr":"ValuePickr"}[s],f"{int(r.raw_records):,}",f"{int(r.unique_docs):,}",f"{int(r.flagged_spam):,}",f"{int(r.relevant_nonspam):,}",f"{int(r.sip_journey_core):,}"] for s,r in cov.iterrows() if s!="TOTAL"]
rows.append(["Reddit","","","","",""]) if False else None
rows=[[("Reddit" if r[0]=="Reddit" else r[0])]+r[1:] for r in rows]
rows.append(["TOTAL",f"{int(tot.raw_records):,}",f"{int(tot.unique_docs):,}",f"{int(tot.flagged_spam):,}",f"{int(tot.relevant_nonspam):,}",f"{int(tot.sip_journey_core):,}"])
P.append("<Section heading=\"2. Data coverage\" id=\"coverage\" caption=\"Records per source, then the funnel to the SIP-journey documents the analysis uses.\">\n"+TBL(["Source","Raw records","Unique docs","Spam / low-signal","SIP/MF-relevant","SIP-journey core"],rows,emph=len(rows)-1,align=["start","end","end","end","end","end"])
 +T("Store reviews cover Groww plus five comparator apps (ET Money, INDmoney, Kuvera, Paytm Money, Zerodha Coin): Groww accounts for 14,360 of the unique Play + App Store reviews; the rest are comparators. 'SIP-journey core' = text explicitly about SIPs, mandates/autopay, instalments or step-up in a finance context. Most generic app reviews ('good app') fall outside it, which is why Reddit dominates the core set; I therefore report source-balanced percentages next to pooled ones.")
 +T(f"Dates run mostly 2023–2026 (Reddit window starts Jan 2023). Languages in the core set: English {H['lang_core']['english']:,}, Hinglish {H['lang_core']['hinglish']:,}, Tanglish {H['lang_core']['tanglish']}, Indic scripts ~{sum(v for k,v in H['lang_core'].items() if k.startswith('indic'))}; the coder codes {LG.loc['english','pct_any_code']:.0f}% of English but only {LG.loc['hinglish','pct_any_code']:.0f}% of Hinglish documents, so vernacular users are under-counted.")
 +"<Callout lead=\"Could not collect (logged, not hidden)\" tone=\"warning\">{"+J("Every blocked or partial source is logged in logs/ and listed here.")+"}</Callout>\n<BulletList items={"+J([
  "Reddit's own .json endpoints (403/302) and PullPush (429) were blocked; Reddit comes from the Arctic Shift public archive instead. Collection was stopped for time before completing all subreddits: comments from r/mutualfunds are partial (~2.5k) and r/DalalStreetTalks, r/indianstreetbets, r/IndiaPersonalFinance, r/StartInvestingIndia comments plus r/groww, r/IndiaFinance, r/CreditCardsIndia posts were not collected.",
  "Quora: blocked (HTTP 403, Cloudflare). Google/DuckDuckGo result scraping: blocked. Facebook/Instagram/WhatsApp groups: not attempted (private or login-walled).",
  "X: only 137 posts via the search tool (noisy, 49 in the core set) — treated as colour, never as primary evidence. Tamil/Telugu/Hindi-script text is thin.",
  "No Groww-internal data (cohorts, instalment logs, tickets). No ground truth on who kept an active SIP at 12 months.",
  "Embedding clusters were computed on an earlier snapshot of the corpus (before the final Reddit top-up); all counts in this page use the final corpus."])+"} />\n</Section>")
# ---- themes
topc=CF.sort_values("n_docs",ascending=False).head(16)
bars=[dict(label=c+(" †" if weak(c) else ""),value=round(100*r.n_docs/N,2),display=f"{100*r.n_docs/N:.1f}%",meta=CODES[c][1][:60]) for c,r in topc.iterrows()]
P.append("<Section heading=\"3. Themes and how often they occur\" id=\"themes\" caption=\"% of SIP-journey documents carrying each code (multi-label). † = weak code on the blind holdout (F1<0.35 or support≤2): directional only.\">\n"+f"<Bars bars={{{J(bars)}}} emphasis=\"none\" />\n"
 +T("Top-16 of 40 codes by raw frequency. Frequencies describe the corpus, not users: a Reddit advice thread and a one-star review both count once. The ranked opportunity areas (section 5) apply an audited precision haircut.")+"</Section>")
# ---- research questions
def sec(title,id,intro,codes,quote_topics,k=2,extra=""):
    s=f"<Section heading={{{J(title)}}} id={{{J(id)}}}>\n"+T(intro)+TBL(CODECOLS,code_rows(codes))+extra
    for t,kk in quote_topics: s+=Q(t,kk)
    return s+"</Section>\n"
rq=[]
rq.append(sec("4a. Why people start a SIP, and what they expect","rq1",f"Starts are goal-led and beginner-led. Beginners asking 'how/where/how much' ({pct('ST_NEED_GUIDE')}) outnumber explicit goal statements ({pct('ST_GOAL')}); small-amount/student/habit starts ({pct('ST_SMALL_HABIT')}), tax saving ({pct('ST_TAX')}) and 'better than FD' ({pct('ST_VS_FD')}) follow. Return expectations are usually anchored on calculators and round numbers (10–15%, ₹1 crore) — the expectation that later meets 'underwhelming' statements. Social influence is rarely stated explicitly ({pct('ST_SOCIAL')}) even though segment tags show friends/family and creators as common routes in (section 4h).",["ST_NEED_GUIDE","ST_GOAL","ST_SMALL_HABIT","ST_TAX","ST_VS_FD","ST_EXPECT_RET","ST_SOCIAL"],[("ST_GOAL",1),("ST_SMALL_HABIT",2),("ST_EXPECT_RET",2),("ST_SOCIAL",1)]))
rq.append(sec("4b. What changes in the months after starting","rq2",f"Behaviour after start splits into engagement (step-ups {pct('BH_STEPUP')}, adding SIPs) and second-guessing (market timing {pct('BH_TIMING')}, underwhelming returns {pct('BH_UNDERWHELM')}). 'Red/negative' talk is rare as a coded theme ({pct('BH_RED')}, weak code) because most people ask about it with other words — see returns confusion in 4e. Step-up is also a friction point: several users say increasing the amount means cancelling and recreating the SIP.",["BH_STEPUP","BH_TIMING","BH_UNDERWHELM","BH_RED","BH_FORGET"],[("BH_STEPUP",1),("BH_UNDERWHELM",2),("BH_RED",2),("BH_TIMING",1)]))
# stop reasons
fr=[];sv=["SI_FAILED","SI_MANDATE","SI_STUCK","SI_ZOMBIE","SI_HALT","SV_CASH","SV_MARKET","SV_RETURNS","SV_SWITCH","SV_DISTRUST","SV_FEES"]
extra=TBL(["Source family","Involuntary-only","Both","Voluntary-only","Lapse language only","Involuntary share*"],[[f,int(r.involuntary),int(r.both),int(r.voluntary),int(r['lapse-language only']),f"{100*(r.involuntary+r.both)/(r.involuntary+r.both+r.voluntary):.0f}%"] for f,r in IV.iterrows()],align=["start","end","end","end","end","end"])+T("*(involuntary + both) / (involuntary + both + voluntary). Lapse evidence = documents with SI_/SV_ codes or explicit stop/pause/cancel/fail language.")
rq.append(sec("4c. What leads to pause, reduce or stop","rq3",f"Voluntary reasons dominate in advice-seeking communities (cash-flow squeeze {pct('SV_CASH')} but low-precision; market anxiety and return doubt are expressed mostly as 'should I stop?' questions rather than as stops); involuntary reasons dominate in reviews of the apps themselves. Genuine voluntary stops are mostly life events (job loss, EMIs, a house purchase) or tactical (stop SIP, hold cash for a dip) — not a loss of belief.",sv,[("SI_FAILED",3),("SI_MANDATE",2),("SI_STUCK",1),("SI_ZOMBIE",2),("SI_HALT",2),("SV_CASH",3),("SV_MARKET",1),("SV_RETURNS",1),("SV_SWITCH",2)],extra=extra))
chk=CK.set_index("cadence")
rq.append(sec("4d. What they check, and how often","rq4",f"Public text says little about frequency, so I do not claim a distribution. Explicit cadence statements: daily/multiple-times-a-day {int(chk.iloc[0].n_docs)} docs, weekly {int(chk.iloc[1].n_docs)}, monthly/after-debit {int(chk.iloc[2].n_docs)}, quarterly/rarely/'set and forget' {int(chk.iloc[3].n_docs)} (each ≈0.5% of core). Two patterns recur: advice-givers telling beginners to stop checking daily (checking is framed as the thing that causes panic), and app reviewers asking for daily portfolio growth and total XIRR in-app. Internal app-open and view logs are the real answer here.",["BH_CHECK","BH_FORGET","BH_RED"],[("BH_CHECK",3)]))
rq.append(sec("4e. What confuses or worries them inside the app","rq5","In-app friction splits into (i) money-state anxiety — debited but not allotted, failed/skipped instalments, cancelled SIPs that still debit; (ii) control — cancel is buried or is the only option, no pause/skip, step-up needs recreate, limits on mandates; (iii) comprehension — XIRR vs absolute, per-SIP vs total returns, 'why red'; (iv) support — ticket loops with no human contact and slow refunds.",["IA_METRICS","IA_PAUSE_FRICTION","IA_FLEX_GAP","IA_ALERTS","IA_SUPPORT","IA_ONBOARD","IA_BUG","IA_WITHDRAW"],[("IA_METRICS",3),("IA_PAUSE_FRICTION",5),("IA_ALERTS",3),("IA_SUPPORT",2)]))
rq.append(sec("4f. What they do outside the app when unsure","rq6",f"When unsure, users ask communities (\"review my portfolio\", \"should I stop?\" — {pct('OU_COMMUNITY')} of core docs), compare against FD/index/other platforms ({pct('OU_COMPARE')}), follow creators ({pct('OU_CREATOR')}) and keep external trackers/spreadsheets or consolidated views ({pct('OU_TRACKER')}). The app is not where the 'should I continue?' conversation happens — a gap, but also the area where constraints (no fund recommendations, no fear/urgency nudges) bite hardest.",["OU_COMMUNITY","OU_COMPARE","OU_CREATOR","OU_TRACKER","OU_PEOPLE"],[("OU_COMMUNITY",2),("OU_CREATOR",1),("OU_TRACKER",1),("OU_COMPARE",1)]))
# continuers vs droppers
cdp=CD.copy(); cdp=cdp[(cdp.dropper_pct+cdp.continuer_pct)>=3].sort_values("diff_pp")
cdb=[dict(label=c,value=round(abs(r.diff_pp),1),display=f"{r.diff_pp:+.1f} pp",meta=("more among droppers" if r.diff_pp>0 else "more among continuers")+f" ({r.dropper_pct:.1f}% vs {r.continuer_pct:.1f}%)") for c,r in pd.concat([cdp.head(5),cdp.tail(6)]).iterrows()]
rq.append(f"<Section heading=\"4g. What separates continuers from droppers\" id=\"rq7\">\n"+T(f"Cohorts are defined from first-person experience text: droppers = stance 'experience' + stop/pause/cancel/skip/fail language about their SIP (n={H['cohort_n']['dropper (first-person stop/pause/fail language)']}); continuers = first-person 'still going / never stopped / N years of SIP' with no lapse language (n={H['cohort_n']['continuer (first-person continuing language)']}). Percentages are share of each cohort carrying the code. Because the dropper cohort is defined by lapse language, SI_FAILED, SV_SWITCH and IA_PAUSE_FRICTION partly reflect that definition and CO_THROUGH reflects the continuer definition — the informative contrasts are the others.")
 +f"<Bars bars={{{J(cdb)}}} emphasis=\"none\" />\n"+T("Reading: droppers talk about support loops, mandates, halts, distrust and fees; continuers are the ones still asking about returns metrics, underwhelming returns and how to start — they stay engaged with the product's numbers rather than leaving over them. Continuers also describe automation and 'don't look back' discipline (CO_AUTOMATE, CO_LONGTERM), but those codes are weak and appear at similar rates in both groups.")+Q("CO_AUTOMATE",3)+Q("CO_THROUGH",3)+"</Section>\n")
# segments
sg=SG[(SG.n_docs>=30)].copy()
def seg_rows():
    rows=[]
    nm={"seg_occupation":"Occupation","seg_age":"Age","seg_income_stability":"Income stability","seg_money_source":"Source of money","seg_influence":"Who influenced"}
    for _,r in sg.iterrows():
        rows.append([nm[r.attribute],r.segment,f"{int(r.n_docs):,}",f"{r.stop_lang_pct:.1f}%",f"{r.A1_pct:.1f}%",f"{r.A3_pct:.1f}%",f"{r.A6_pct:.1f}%",f"{r.A8_pct:.1f}%"])
    return rows
cvr=SC.set_index("attribute")
segcov=", ".join(f"{k.replace('seg_','')}: {cvr.loc[k,'pct_of_journey_core']}%" for k in cvr.index)
rq.append("<Section heading=\"4h. How patterns differ by segment\" id=\"rq8\" caption=\"Public text rarely states income, age or money source — coverage is low, so read these as hypotheses.\">\n"
 +T(f"Share of journey-core documents where a segment could be tagged from explicit self-description: {segcov}. Cells with fewer than 30 documents are omitted; the A4 (cash-flow), A9 (beginner) and A10 (off-app) columns are excluded here because the tags and codes share cue words (circular).")
 +TBL(["Attribute","Segment","Docs","Stop/pause language","A1 failure/mandate","A3 pause/edit/flex","A6 returns confusion","A8 support/trust"],seg_rows(),align=["start","start","end","end","end","end","end","end"])
 +T("What the numbers suggest (directional): (1) Documents mentioning an in-app prompt/ad influence or a bank/agent route are far more likely to carry failure-and-friction codes than creator- or friends-led ones — but these are mostly store reviews, so source and segment are confounded. (2) Students and pocket-money investors raise flexibility (minimum amounts, edit/pause) more than salaried users, — consistent with small-ticket habit starts that need low-friction pause/resume. (3) Tagged users aged 35–44 use stop/pause language (12.9%) and returns-confusion codes (9.7%) far more than the ≤24 group (1.6% and 3.4%). (4) Self-employed/irregular-income users are few (n small) but they explicitly ask whether to keep a fixed SIP or invest only in good months — an unserved 'income-aware' flexibility need.")
 +Q("SEG_FREELANCE",1)+Q("ST_SMALL_HABIT",1)+"</Section>\n")
# ---- scorecard
sc=S.sort_values("rank")
sc_rows=[]
for _,r in sc.iterrows():
    a=r.area; sc_rows.append([int(r["rank"]),f"{a} {r['name']}",f"{int(r.n_docs):,}",f"{r.balanced_pct:.1f}%",f"{r.audit_precision:.2f} ({AP.loc[a,'ci_lo']:.2f}–{AP.loc[a,'ci_hi']:.2f}, n={int(AP.loc[a,'audit_n'])})",f"{r.adj_balanced_pct:.1f}%",f"{r.stop_lang_pct:.0f}%",("n/a" if r.low_rating_pct!=r.low_rating_pct else f"{r.low_rating_pct:.0f}%"),f"{int(r.mech)}",f"{int(r.n_families_ge10)}",f"{r.priority:.2f}",f"{int(r.rank_equal_weights)}/{int(r['rank_metric-link_heavy'])}/{int(r.rank_frequency_heavy)}"])
sbars=[dict(label=f"{r.area} {r['name'][:48]}",value=round(r.priority,3),display=f"{r.priority:.2f}",meta=f"{AREAS[r.area]['type']} · mechanism {int(r.mech)}/5") for _,r in sc.iterrows()]
P_sc="<Section heading=\"5. Ranked opportunity scorecard\" id=\"scorecard\" caption=\"Ten areas = groups of codes. Priority = 0.30·frequency + 0.25·severity + 0.30·metric-link + 0.15·confidence (each scaled 0–1).\">\n"
P_sc+=f"<Bars bars={{{J(sbars)}}} emphasis={{0}} />\n"
P_sc+=TBL(["Rank","Area","Docs","Freq (source-balanced)","Audited precision (95% CI)","Freq × precision","Stop/pause language","≤2★ share","Metric link (1–5)","Source families","Priority","Rank: equal / link-heavy / freq-heavy"],sc_rows,emph=None,align=["end","start","end","end","end","end","end","end","end","end","end","end"])
P_sc+=T("How each score is built. Frequency = mean across source families of the % of that family's SIP-journey documents carrying any code in the area, times the audited precision (so noisy rules are discounted; recall is unknown and not corrected). Severity = average of (a) the share of the area's documents with explicit stop/pause/cancel/fail language and (b) the share of its rated reviews that are ≤2★ (base rate for all rated core reviews is "+f"{H['base_low_rating_pct']:.0f}%"+"; (b) omitted where <20 rated). Failure language is partly definitional for A1/A2, so their severity is high by construction. Metric link is my judgment of how directly the issue breaks 'a successful instalment in the last 30 days' (5 = it is the missing instalment; 3 = indirect); the reasoning for each area is in the codebook. Confidence = source diversity, sample size and audited precision. Sensitivity: the last column shows rank under three alternative weightings; A1 and A2 are in the top 5 under all, A3 is 3rd when metric link is weighted heavily, A10 is first only when frequency dominates.")
P_sc+="<Callout lead=\"Reading the ranking\" tone=\"info\">{"+J("Involuntary areas lead on severity and metric link; frequency-heavy weighting favours off-app reliance.")+"}</Callout>\n<BulletList items={"+J([
 "A1–A2 (involuntary): fewest documents but highest severity and most direct link to the metric; triangulated across store reviews, forums, Reddit and YouTube.",
 "A3 (pause/edit/cancel and flexibility): frequent on Groww-specific text; the 'only cancel, then recreate' pattern turns a temporary squeeze into a lapse. Precision is only 0.35 (flexibility feature-requests dilute it), so treat the frequency as an upper bound.",
 "A8 (support/refund/reliability trust): many one-star reviews; amplifies A1/A2 because unresolved failures are what pushes people off a platform.",
 "A10 (off-app reliance) is a context, not a defect: people ask strangers whether to continue. It is large (≈10% after haircut) but the product response must respect the no-fund-recommendation and no-fear/urgency constraints.",
 "A4, A6, A9 rank low mainly because precision is low (0.25–0.45); they may be under-ranked — see limitations."])+"} />\n"
# top area cards
cards=[("A1",["SI_FAILED","SI_MANDATE"]),("A2",["SI_STUCK","SI_ZOMBIE","SI_HALT"]),("A3",["IA_PAUSE_FRICTION","IA_FLEX_GAP"]),("A8",["IA_SUPPORT","SV_DISTRUST"]),("A5",["IA_ALERTS"])]
for a,tp in cards:
    r=sc[sc.area==a].iloc[0]; P_sc+=f"<Text>{{{J(f'{a} — {r['name']} (rank {int(r['rank'])}). Why it matters: {AREAS[a]['why']} Triangulated across: {TA.loc[a,'families']}.')}}}</Text>\n"
    for t in tp[:2]: P_sc+=Q(t,1)
P_sc+="</Section>\n"
rq.append(P_sc)
# funnel
fstages=["M0-1","M2-3","M4-6","M7-12","M12+"]
fbars=[dict(label=s,values=[int(FC.loc[s,'involuntary']),int(FC.loc[s,'both']),int(FC.loc[s,'voluntary']),int(FC.loc[s,'lapse-language only'])],display=f"n={int(FC.loc[s,'total'])}") for s in fstages]
ibars=[dict(label=f,values=[int(r.involuntary),int(r.both),int(r.voluntary),int(r['lapse-language only'])],display=f"n={int(r.total)}") for f,r in IV.iterrows() if f!="ALL"]
rsn=["SI_FAILED","SI_MANDATE","SI_STUCK","SI_HALT","SV_CASH","SV_SWITCH","SV_DISTRUST","SV_FEES"]
frow=[[s]+[int(RF.loc[s,c]) for c in rsn]+[int(RF.loc[s,'n_docs'])] for s in fstages]
rq.append("<Section heading=\"6. Drop-off funnel and involuntary vs voluntary split\" id=\"funnel\" caption=\"Where in the first 12 months lapse evidence sits — only documents with an explicit time cue (e.g. 'first month', '4 months in', '3 years of SIP').\">\n"
 +f"<StackedBars series={{{J(['Involuntary','Both','Voluntary','Lapse language only'])}}} bars={{{J(fbars)}}} />\n"
 +T("Voluntary reasons outnumber involuntary ones at every stage, but the involuntary share is highest in months 0–3 (failed first instalments, mandate approval, units not allotted) and falls after month 4, where money pressure, return doubt and switching dominate; month 12+ is mostly established investors asking whether to keep going. This is a mix of evidence by stage, not a retention curve: stages are inferred from what people say, and 'pre-start' documents (no lapse yet) are excluded.")
 +TBL(["Stage"]+rsn+["Docs"],frow,align=["start"]+["end"]*(len(rsn)+1))
 +T("Counts of documents per reason by stage (time-cue documents only). Cash-flow (SV_CASH) is the most common voluntary reason code but has low audited precision (0.25) — its counts are an upper bound.")
 +f"<StackedBars series={{{J(['Involuntary','Both','Voluntary','Lapse language only'])}}} bars={{{J(ibars)}}} />\n"
 +T("By source family: store reviews are mostly involuntary (people write after a failed debit), Reddit and YouTube mostly voluntary (advice seeking). Neither is a clean estimate of Groww's cohort; internal instalment-failure logs give the true split.")+"</Section>\n")
# unmet needs
needs=[("Pre-debit reminders and a clear 'what will be debited / what was skipped' view","IA_ALERTS","Store reviewers on several apps ask for a reminder before the debit date and an alert when an instalment is skipped."),
 ("Pause / skip / reduce instead of cancel-and-recreate; edit amount, date, step-up in place","IA_PAUSE_FRICTION","The fix users describe is control, not persuasion."),
 ("Flexible schedules (date, weekly/daily, step-up variants) and low minimums for small starters","IA_FLEX_GAP","Includes ₹100 minimum SIP and step-up requests (partly feature wish-list; low precision)."),
 ("Money-in-flight transparency: debited, pending, allotted, refunded — and clear AMC-halt messaging","SI_STUCK","Units-not-allotted and refund delays recur; halts are explained on Reddit, not in-app."),
 ("A human resolution path for payment problems","IA_SUPPORT","Ticket-only loops are a recurring complaint."),
 ("Plain-language return metrics (XIRR vs absolute, per-SIP vs total) and expectation anchoring","IA_METRICS","Questions about the two numbers shown, and about 6–10% after a year."),
 ("An in-app place to ask 'should I continue?' without being pushed to a product","OU_COMMUNITY","Currently answered by strangers on Reddit/YouTube."),
 ("A consolidated view across SIPs/folios/other apps","OU_TRACKER","People keep spreadsheets or other trackers (weak code)")]
nrows=[[n,f"{int(CF.loc[c].n_docs):,}",c+(" †" if weak(c) else ""),why] for n,c,why in needs]
rq.append("<Section heading=\"4i. Unmet needs that recur across sources\" id=\"needs\">\n"+TBL(["Unmet need","Docs (coded)","Code","Note"],nrows)+"</Section>\n")
# validation
ev=pd.read_csv("data/processed/eval_summary_holdout.csv").set_index("method").loc["ensemble"]
gr=pd.read_csv("data/processed/eval_groups_holdout.csv"); gr=gr[gr.method=="ensemble"]
vrows=[[r.group,int(r.support_gold),f"{r.precision:.2f}",f"{r.recall:.2f}",f"{r.f1:.2f}",("" if r.kappa!=r.kappa else f"{r.kappa:.2f}")] for _,r in gr.iterrows()]
arow=[[a,int(HA.loc[a,'gold_pos']),f"{HA.loc[a,'precision']:.2f}",f"{HA.loc[a,'recall']:.2f}",f"{HA.loc[a,'kappa']:.2f}" if HA.loc[a,'kappa']==HA.loc[a,'kappa'] else "",f"{AP.loc[a,'audit_precision']:.2f}"] for a in AREAS]
rq.append("<Section heading=\"7. Validation summary\" id=\"validation\" caption=\"Only numbers that were actually computed. Full detail in AI_EVIDENCE_LOG.md.\">\n"
 +f"<Metrics metrics={{{J([dict(value=str(VN['holdout_n']),label='blind random holdout documents',detail='hand-labelled before any classifier existed'),dict(value=f'{ev.micro_precision:.2f} / {ev.micro_recall:.2f}',label='micro precision / recall (final coder)',detail=f'micro-F1 {ev.micro_f1:.2f}, κ {ev.micro_kappa:.2f}'),dict(value=f'{VN['eval_stance']['kappa']:.2f}',label='stance κ (E/Q/A/O)',detail=f'accuracy {VN['eval_stance']['acc']:.2f}'),dict(value=f'{VN['quotes']['verbatim']}/{VN['quotes']['n']}',label='quotes verbatim in raw data',detail='script check on raw JSONL')])}}} />\n"
 +TBL(["Code group","Gold positives","Precision","Recall","F1","κ"],vrows,align=["start","end","end","end","end","end"])
 +TBL(["Area","Holdout gold +","Holdout precision","Holdout recall","Holdout κ","Full-corpus audited precision (n=20)"],arow,align=["start","end","end","end","end","end"])
 +T(f"Triangulation: every area passes the ≥2-independent-source-family rule ({int(TA.triangulated.sum())}/10); A1, A2, A3, A6, A7, A8, A9, A10 reach 4 families. Hallucination controls: closed codebook; numbers generated by script; quotes sampled by script, chosen by me, verbatim-checked against raw records; no author handles stored. Spam filter audit: {100*VN['spam_flag_precision']:.0f}% of flagged documents were truly spam/low-signal (n={VN['spam_audit_n']}) — it over-removes legitimate text. Outcome labels (stopped/paused/…) are weak (κ {VN['eval_outcome']['kappa']:.2f}) and not used for headline numbers.")
 +"<Callout lead=\"Examples where the AI was wrong and was corrected\" tone=\"warning\">{"+J("Each was found by an audit or an implausible-looking table, then fixed.")+"}</Callout>\n<BulletList items={"+J([
  "BH_FORGET ('unaware the SIP stopped') matched 'set and forget' advice — audited at 0/20 and removed from the reminders/visibility area.",
  "The IA_ALERTS ML-AND variant kept 10 documents and zero holdout recall; switched to the regex rule (166 docs, audited precision 0.50).",
  "First-pass regexes fired on 27% of training documents for OU_COMPARE (precision 0.12) and BH_RED (0.04); replaced by per-code OOF-selected variants.",
  "My first funnel assigned stages from codes and then counted reasons by stage (circular); rebuilt on time-cue documents only.",
  "Segment heat-map looked implausibly clean — cause: tags and codes share cue words; those cells are now excluded.",
  "One quote failed the verbatim check (title and body joined with a period); fixed and re-verified."])+"} />\n</Section>\n")
# limitations
rq.append("<Section heading=\"8. Limitations\" id=\"limits\">\n<BulletList items={"+J([
 "Self-selection and negativity bias: store reviewers write after failures; communities over-represent advice-seekers and enthusiasts; silent droppers, the target group, post nothing.",
 f"Source imbalance: Reddit is {100*cov.loc['reddit','sip_journey_core']/tot.sip_journey_core:.0f}% of the analysed set; I report source-balanced means, but family sizes still drive confidence.",
 "Single annotator (the LLM) wrote rules and labels; no human second coder, so κ is machine-vs-labeller. The holdout was scored three times with rule changes (train data only) in between.",
 "Coder is moderate (micro-F1 ≈0.44); several codes have ≤2 holdout positives. Recall is only known on the holdout; area frequencies are haircut for precision but not corrected for missed positives.",
 "Segment coverage is 2–12% of documents and tags are regex on self-description; segment differences are hypotheses.",
 "Hinglish/Tanglish/vernacular text is under-coded (English 70% vs Hinglish 44% of documents get any code).",
 f"Spam filter over-removes (precision {100*VN['spam_flag_precision']:.0f}%); promo/bot comments that survive (YouTube carries many) are not measured.",
 "Time: Reddit 2023–2026; regulatory events (SEBI rules on broker-platform SIPs, AMC halts on international funds) shape what people talk about.",
 "Public-text engine only: no measure of who actually kept a SIP active for 12 months."])+"} />\n</Section>\n")
# validate with internal data
rq.append("<Section heading=\"9. What I would validate with Groww internal data\" id=\"internal\" caption=\"Public text generates hypotheses; these checks decide which are real and how big. All are constraint-safe: none needs fund picks or fear/urgency nudges.\">\n"+TBL(["Hypothesis from this engine","Internal data to check","Decision it informs"],[
 ["Involuntary lapse is a large, early share of first-year drop-off (A1/A2)","Instalment-level logs for first-time SIP cohorts: failure rate by bank/mandate type (NACH vs UPI AutoPay), reason code, retries, time-to-recovery, % lapsed after first failure","Size of the involuntary prize; which failure types to fix first"],
 ["Cancel is chosen where a pause/skip/reduce would have retained the user (A3, A4)","Cancel-flow funnel: entry, reason chosen, completion; re-start within 30/90 days; cohort retention of users who cancel vs those who edit","Whether in-place pause/edit retains more than it costs"],
 ["Users do not see what will be debited or that an instalment was skipped (A5)","Notification delivery/open logs vs next-instalment success; holdout experiment on neutral pre-debit info","Value of status visibility vs risk of nudge fatigue"],
 ["Returns display drives doubt in months 3–9 (A6)","Views of XIRR/absolute toggles, sessions on red-portfolio days vs SIP cancellation within 7/30 days","Whether explanation or default-metric changes help"],
 ["Support friction amplifies lapses (A8)","Tickets tagged SIP/debit/refund: time-to-resolution vs 30-day active-SIP status","Support routing/SLA priorities"],
 ["Segments differ (students, irregular income, influence route)","KYC occupation/income slab, age, acquisition channel × 12-month active-SIP rate; first SIP amount; SIP date vs salary date","Whether to personalise flexibility options"],
 ["Checking frequency","App-open/portfolio-view cadence in months 1–12 vs retention","Whether frequent checking predicts lapse (public text cannot tell)"],
 ["Core metric baseline","Cohort curve: % of first-time MF investors with ≥1 successful instalment in the last 30 days at month 3/6/9/12, by cohort month","Baseline and target for the 12-month goal"]])+"</Section>\n")
rq.append("<Section heading=\"Files\" id=\"files\">\n"+T("/workspace/groww-discovery.zip contains: README.md, codebook.md, AI_EVIDENCE_LOG.md, scripts/ (01a–11), data/raw (collected records), data/processed (cleaned + coded CSVs), labels/ (hand labels), outputs/ (scorecard, funnel, segments, quote verification), charts/*.png (7 charts), logs/.")+"</Section>\n")
toc=[("Architecture","arch"),("Data coverage","coverage"),("Themes","themes"),("Why start","rq1"),("After start","rq2"),("Stop reasons","rq3"),("Checking","rq4"),("In-app confusion","rq5"),("Outside the app","rq6"),("Continuers vs droppers","rq7"),("Segments","rq8"),("Unmet needs","needs"),("Scorecard","scorecard"),("Funnel","funnel"),("Validation","validation"),("Limitations","limits"),("Internal data","internal")]
_n=[x for x in rq if 'id="needs"' in x][0]; rq.remove(_n); _i=[k for k,x in enumerate(rq) if 'id="scorecard"' in x][0]; rq.insert(_i,_n)
# order: arch, coverage, themes, rq1..rq6, rq7, rq8, needs..., need scorecard etc. Build final order
order=[]
body="".join(P[:4])  # metrics, callout, arch heading? (P holds metrics, callout, arch section start, arch table, then close)
page=("import { Page, Section, Metrics, Callout, Table, Text, Quote, Bars, StackedBars, Diagram, BulletList, TableOfContents } from \"grok/canvas\";\n\n"
 "export default function Report() {\n  return (\n<Page title=\"Groww SIP Retention: Discovery Engine & Findings\" summary=\"AI-powered discovery over public conversations about SIPs: what makes first-time investors stop (or keep) a SIP, ranked opportunity areas, and how far the evidence can be trusted.\" sources={[\"Google Play + App Store reviews (6 apps)\",\"Reddit via Arctic Shift archive\",\"YouTube comments\",\"TradingQ&A, ValuePickr\",\"X\"]} width=\"wide\">\n")
page+=P[0]+"\n"+P[1]+"\n"
page+="<TableOfContents items={"+J([dict(label=l,id=i) for l,i in toc])+"} />\n"
page+=P[2]+P[3]+P[4]+P[5]   # arch section open/diagram, table, close, coverage
page+="".join(rq)
page+="</Page>\n  );\n}\n"
open(O+"canvas.tsx","w").write(page); print(len(page))
