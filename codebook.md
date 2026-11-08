# Codebook (40 codes, 7 groups, multi-label)

Built bottom-up: embedding clusters + NMF topics (`data/processed/clusters_embedding.md`, `topics_nmf.md`) -> analyst (LLM) open coding of ~300 sampled documents -> 40 codes. A document can carry several codes. Document-level attributes: **stance** (E experience / Q question / A advice-to-others / O other) and **outcome** (S stopped / P paused / R reduced / C considering / K continuing / N none stated).

Per-code columns: *n* = documents carrying the code in the final corpus (SIP-journey core, N=19061); *variant* = rule used by the final coder (regex | ml | and | or), picked by 5-fold OOF F1 on training labels; *holdout P/R* = precision/recall on the 150-document blind holdout, with support (gold positives) - **supports are small, treat as indicative**.

## START - Why start / expectations

### `ST_GOAL`
- **Definition:** Starts SIP for a long-term goal (retirement, house, child, corpus, FIRE, compounding)
- **Docs coded:** 633 (3.3% of journey-core) | **variant:** and | **holdout:** support 6, P=0.40, R=0.33
- **Regex rule:** `retire|\bfire\b|fatfire|corpus|(my|long[- ]term|financial|life|big) goals?|goal[- ]based|down ?payment|child(ren)?'?s? (education|future|marriage)|(for|my) (child|daughter|son|baby|kid)|\b\d+ ?(cr|crore)\b|wealth (creation|building)|financial independence|build (a )?(corpus|wealth)`
- **Exemplar (reddit):** "I'm looking at a 10 year Horizon, goal is to fund children's education, buy a house even. Been using Groww"  _(doc RE4753807e)_
- **Exemplar (reddit):** "Want to start a sip in an instrument and build wealth over next 10 years"  _(doc RE69c62990)_

### `ST_SOCIAL`
- **Definition:** Started/was told to start because of friend, family, colleague, advisor, creator, ad (social influence)
- **Docs coded:** 78 (0.4% of journey-core) | **variant:** and | **holdout:** support 0, P=0.00, R=0.00
- **Regex rule:** `(friend|colleague|cousin|relative|parents?|dad|father|mom|mother|brother|sister|husband|wife|uncle|senior|boss)s?.{0,60}(told|suggest|recommend|advis|showed|convinc|introduc|started|asked)|(told|suggest|recommend|advis|convinc|inspired|motivat).{0,40}(by|from).{0,20}(friend|colleague|parents?|you|video|channel|sir)|because of (you|your video)|after (watching|seeing).{0,30}video|fomo|\bpeer`
- **Exemplar (reddit):** "my friend suggested invest in sip and mutual funds"  _(doc REd9648563)_
- **Exemplar (reddit):** "Since I saw some videos about sips I started investing my money in MF through sips. I don’t know much about markets and mutual funds so I just randomly picked some mutual funds"  _(doc RE3e4b961d)_

### `ST_SMALL_HABIT`
- **Definition:** Starts small / builds habit / discipline / affordable amount (₹100-₹5k, student, 'start early')
- **Docs coded:** 667 (3.5% of journey-core) | **variant:** ml | **holdout:** support 5, P=0.00, R=0.00
- **Regex rule:** `small (amount|sip|start|investment)|start(ing)? small|pocket money|\bstudents?\b|college|start(ing)? early|stipend|first (salary|job)|(₹|rs\.?|inr) ?(100|200|250|300|500|1000|1,000|1500|2000|2,000)\b(?! ?(crore|cr|lakh|l\b))|\b[1-5]k (sip|per month|monthly|pm|/month)|minimum (amount|sip)|habit`
- **Exemplar (playstore, Groww):** "As a 22 years old begglinner investor, i found groww extremely simple and user friendly. i started my fast sip last month without any hassle"  _(doc PL01623ef0)_
- **Exemplar (reddit):** "I'm a student and I'm doing an internship as part of my course for which i get stipend. I can set apart Rs 500 every month"  _(doc RE0617d689)_

### `ST_VS_FD`
- **Definition:** Frames SIP as better than FD/savings/inflation
- **Docs coded:** 605 (3.2% of journey-core) | **variant:** regex | **holdout:** support 0, P=0.00, R=0.00
- **Regex rule:** `beat inflation|better than (fd|fixed|savings|rd)|instead of (fd|fixed|savings)|fd (gives|give|return|rate|interest)|savings account.{0,30}(low|interest)|inflation`

### `ST_TAX`
- **Definition:** Tax-saving motive (ELSS, 80C)
- **Docs coded:** 638 (3.3% of journey-core) | **variant:** or | **holdout:** support 2, P=0.29, R=1.00
- **Regex rule:** `\belss\b|80c|tax[- ]sav|tax saver|save tax`

### `ST_EXPECT_RET`
- **Definition:** Explicit expectation/ask about returns or maturity value ('will I get 12%', 'how much in 10 yrs', '1 crore')
- **Docs coded:** 223 (1.2% of journey-core) | **variant:** ml | **holdout:** support 3, P=0.00, R=0.00
- **Regex rule:** `expected? (return|growth)|how much (will|would|can|do).{0,40}(get|grow|become|return|corpus)|will (i|it) (get|become|reach)|\b1[0-5] ?% (return|cagr|xirr|p\.?a)|returns? (calculator|expected)|\bmaturity\b|sip calculator|guarantee|crore in|1 ?cr(ore)? (in|by)`
- **Exemplar (youtube):** "Mera to sip 2% return dikha rha hain , 3 saal ho gye hain"  _(doc YO15fd064f)_
- **Exemplar (valuepickr):** "15% CAGR looks like a more realistic and safer bet, considering a conservative approach"  _(doc VA0bcc9bce)_

### `ST_NEED_GUIDE`
- **Definition:** Beginner unsure how/where/what/how much to start; asks for basics
- **Docs coded:** 1280 (6.7% of journey-core) | **variant:** and | **holdout:** support 16, P=0.53, R=0.50
- **Regex rule:** `beginner|newbie|new (to|investor)|first[- ]time|complete(ly)? (new|clueless|beginner)|noob|clueless|no (idea|knowledge|clue)|where (to|do i|should i) start|how (to|do i|should i) (start|begin|invest)|just start(ed|ing)|planning to start|started (my )?(sip|investing|investment)|which (fund|mutual fund|sip|app)|konse? fund|kaise (start|shuru)|first sip`

## BEHAV - Behaviour after start / checking

### `BH_CHECK`
- **Definition:** Checks portfolio/returns frequently or wants daily visibility
- **Docs coded:** 71 (0.4% of journey-core) | **variant:** regex | **holdout:** support 1, P=1.00, R=1.00
- **Regex rule:** `check(ing|ed)?.{0,25}(daily|every day|everyday|often|frequently|regularly|weekly|every week|once a)|daily (check|growth|change|return|nav|portfolio)|track(ing)? daily|(look|looking) at (my )?portfolio|portfolio (once|daily)|every day.{0,20}(portfolio|nav|return)`
- **Exemplar (playstore, Zerodha Coin):** "The ability to track daily portfolio wide and individual mutual fund returns. 2. Clear filters for paused/active SIPs. Lumping them in the same window with a tag often causes confusion"  _(doc PL985cd861)_
- **Exemplar (reddit):** "Hope I don't get obsessed with checking the MF everyday tho"  _(doc RE34d364d1)_

### `BH_RED`
- **Definition:** Sees red/negative/flat returns on SIP/portfolio (market fall, loss, -x%)
- **Docs coded:** 54 (0.3% of journey-core) | **variant:** and | **holdout:** support 2, P=0.50, R=0.50
- **Regex rule:** `\bin (the )?red\b|negative (return|xirr|nav|growth|sip)|(portfolio|sip|fund|returns?|investment)s?.{0,30}(red|negative|loss|in loss|down)|(down|loss|negative|minus) (by )?\d|(-|−) ?\d+(\.\d+)? ?%|no returns?|zero returns?|0 ?% return|gave (me )?(loss|negative)|(sip|fund)s? (is|are) (negative|in loss)`
- **Exemplar (reddit):** "If you stop the SIP now you ll be at a loss of 8%"  _(doc REfff8a161)_
- **Exemplar (reddit):** "having negative returns int he first few years is a good thing. The lower the NAV is, the more units you get"  _(doc RE62c8edac)_

### `BH_UNDERWHELM`
- **Definition:** Returns underwhelming vs expectation / vs FD / vs friend / vs index after months-years
- **Docs coded:** 324 (1.7% of journey-core) | **variant:** ml | **holdout:** support 3, P=0.33, R=0.33
- **Regex rule:** `nothing|no growth|gone nowhere|stagnan|flat\b|underperform|poor (return|perform)|low (return|xirr)|(return|xirr|growth).{0,20}(low|poor|disappoint|pathetic|bad)|\d ?% ?(xirr|return).{0,40}(after|in|since|for)|only \d+(\.\d+)? ?%|barely|not worth|after (\d+|one|two|three|four|five|1|2|3|4|5) (year|yr|month)s?.{0,60}(return|loss|nothing|negative|profit)|dragging|beaten by|lagging|\bsucks\b.{0,40}ret...`
- **Exemplar (youtube):** "After 3 years of sip investment I would suggest don't put your money in mutual funds the growth rate is nearly 9% on an average we already get 7.1 from fd"  _(doc YOb95d4c06)_
- **Exemplar (reddit):** "be happy with 10% xirr in this market condition even i have been doing sip for 5 years mine is also 11% xirr"  _(doc RE71057917)_

### `BH_STEPUP`
- **Definition:** Increases/steps up SIP amount, adds SIPs, annual increments
- **Docs coded:** 1009 (5.3% of journey-core) | **variant:** and | **holdout:** support 3, P=0.25, R=0.67
- **Regex rule:** `step[- ]?up|increas(e|ed|ing) (my |the )?(sip|amount|investment)|bump(ed)?|top[- ]?up|raise (my )?sip|hike.{0,40}(sip|invest)|increment|annual(ly)? (increase|raise)|(increase|raise|increasing) .{0,15}sip`
- **Exemplar (playstore, INDmoney):** "after I have done enough research and want to increase my SIP, I currently have to pause my existing ones and make a new one"  _(doc PL3e4d2cfc)_

### `BH_TIMING`
- **Definition:** Tries to time the market: lumpsum on dips, skipping/pausing SIPs for dips, waiting for correction
- **Docs coded:** 805 (4.2% of journey-core) | **variant:** and | **holdout:** support 14, P=0.62, R=0.57
- **Regex rule:** `buy (the )?dip|on dips?|\bdips?\b|time the market|timing the market|market timing|wait(ing)? (for|till|until).{0,30}(fall|correction|crash|dip|low|bottom)|lump ?sum.{0,40}(fall|dip|correct|crash)|(fall|dip|correct|crash).{0,40}lump ?sum|extra (units|investment)|invest(ing)? more (when|during)|all[- ]time high|\bpe\b|valuation`
- **Exemplar (reddit):** "I wish for dip every month during my sip date"  _(doc RE244f35de)_

### `BH_FORGET`
- **Definition:** Loses attention / forgets / irregular / unaware SIP stopped or skipped ('noticed 6 months later')
- **Docs coded:** 389 (2.0% of journey-core) | **variant:** regex | **holdout:** support 3, P=0.43, R=1.00
- **Regex rule:** `forg[eo]t|forgot|unaware|didn'?t (notice|realis|realiz|know)|noticed (it )?(\w+ ){0,3}(later|after)|months? later|irregular|lost track|no idea (that )?(it|my)|stopped visiting|haven'?t (checked|opened)|never (checked|opened)`

## STOP-VOL - Voluntary stop/pause triggers

### `SV_MARKET`
- **Definition:** Stops/pauses/considers stopping because of market fall or fear of losses
- **Docs coded:** 53 (0.3% of journey-core) | **variant:** and | **holdout:** support 1, P=0.00, R=0.00
- **Regex rule:** `(stop|pause|paus|cancel|discontinu|band kar|bandh kar|rok|exit)(ped|ing)?.{0,50}(market|crash|fall|correction|downturn|red|bear|war|tariff)|(market|crash|fall|correction|downturn|bear).{0,50}(stop|pause|paused|cancel|discontinue|band kar|bandh|exit)`
- **Exemplar (youtube):** "One should stop sip or stay invested!?"  _(doc YOa0b39d53)_
- **Exemplar (reddit):** "My SIP portfolio is down by 25%. What should I do now?"  _(doc RE009b1dde)_

### `SV_RETURNS`
- **Definition:** Stops/pauses/reconsiders because of poor returns or fund underperformance
- **Docs coded:** 51 (0.3% of journey-core) | **variant:** and | **holdout:** support 2, P=0.00, R=0.00
- **Regex rule:** `(stop|pause|paus|cancel|discontinu|switch|redeem|exit|shift)(ped|ing)?.{0,60}(because|due to|as|since).{0,40}(return|xirr|underperform|poor|loss|lagging|dragging|low)|(return|xirr|underperform|poor)s?.{0,40}(so|therefore).{0,20}(stop|switch|exit)|(stopped|paused|switch(ed)?|exit(ed)?|redeem(ed)?) .{0,30}(fund|sip).{0,40}(underperform|poor|low return|dragging|lagging)|(dragging|underperform).{0,60}...`
- **Exemplar (reddit):** "My debt fund got more return than that. Should I stop SIP and do a SWP and invest in another mutual fund"  _(doc RE23879caa)_
- **Exemplar (reddit):** "Should i stop the sip and shift to the large midcap index fund?"  _(doc RE2b6da155)_

### `SV_CASH`
- **Definition:** Cash-flow/life constraint: EMI/loan, job/income change, irregular income, expenses, emergency, relocation, student/pocket money
- **Docs coded:** 1143 (6.0% of journey-core) | **variant:** and | **holdout:** support 3, P=0.25, R=0.33
- **Regex rule:** `\bemi\b|(home|education|personal|car) loan|pay(ing)? off.{0,15}loan|job (loss|change|gap)|lost (my )?job|laid off|layoff|salary (cut|delay)|income (is )?(irregular|unstable|fluctuat)|irregular income|freelanc|cash[- ]?flow|cash crunch|can'?t afford|short on (cash|money)|financial (stress|crisis|emergency|problem)|medical (emergency|expense)|hospital|moving (to|abroad|out)|relocat|studies abroad|\b...`
- **Exemplar (reddit):** "I’ve stopped my SIP ever since I lost my job in dec 2023. Only my gold kitty continuing and that too I’m planning to close. Need to first pay off my EMIs"  _(doc RE8e2a37a5)_
- **Exemplar (reddit):** "Do you think pausing the SIP/ Savings for a while to repay the loan is good idea?"  _(doc RE51865478)_

### `SV_SWITCH`
- **Definition:** Voluntary re-allocation: stops one SIP to start/switch another fund/plan/platform, rebalancing, goal done
- **Docs coded:** 236 (1.2% of journey-core) | **variant:** and | **holdout:** support 5, P=1.00, R=0.20
- **Regex rule:** `switch(ed|ing)? (from|to|my|the|over)|shift(ed|ing)? (my |the )?(sip|fund|money|to|from)|stop(ped)? (the |my )?sip.{0,60}(start|new|another|instead)|start(ed)? (a )?(new )?sip.{0,40}(instead|another)|diverted|rebalanc|moved (to|from)|exit (the )?fund|regular to direct|move (my )?sips?`
- **Exemplar (reddit):** "i stopped my sip's and started giving liquidity in options"  _(doc REba8a0631)_
- **Exemplar (reddit):** "When market reached 25000+ levels, I stopped the SIP, and now did the lumpsum instead at 23500 level"  _(doc RE19fa6b2d)_

### `SV_DISTRUST`
- **Definition:** Distrust/scepticism: SIP/MF is a scam/marketing, fear of fund bankruptcy, unreliable platform, government/regulation anger, 'survivorship bias'
- **Docs coded:** 439 (2.3% of journey-core) | **variant:** ml | **holdout:** support 5, P=0.00, R=0.00
- **Regex rule:** `\bscam|fraud|cheat|looted|loot(ing)?\b|don'?t trust|can'?t trust|no trust|lost trust|distrust|trust (issue|the app)|misselling|mis-sell|manipulat|survivorship|marketing gimmick|fooling|hype|bankrupt|ponzi|mislead|shady|fake|stop fooling|collusion|unreliable|reliability`
- **Exemplar (playstore, Groww):** "portfolios are also fake on this app when you are part of the sip it will show you loss and once you are tired of it and redeem it will show you hight interest suddenly"  _(doc PL0adcfcee)_

### `SV_FEES`
- **Definition:** Fees/charges/penalties/commissions cited as friction or reason (platform fee, bounce charges, stamp duty, commission, expense ratio)
- **Docs coded:** 760 (4.0% of journey-core) | **variant:** and | **holdout:** support 5, P=0.38, R=0.60
- **Regex rule:** `\bcharges?\b|\bfees?\b|\bcharged\b|penalt(y|ies)|bounce charge|ecs bounc|commission|platform fee|expense ratio|stamp duty|₹ ?\d+ (per month|monthly|charge|penalty)|\b\d+ ?rs ?(charge|penalty|fine)`

## STOP-INV - Involuntary lapse triggers

### `SI_FAILED`
- **Definition:** Instalment failed/skipped/rejected/bounced; insufficient balance; bank/debit failure; repeated failures
- **Docs coded:** 291 (1.5% of journey-core) | **variant:** ml | **holdout:** support 4, P=0.25, R=0.25
- **Regex rule:** `(sip|instal+ment|autopay|auto[- ]?debit|mandate|payment|debit).{0,40}(fail|failed|failing|reject|rejected|bounce|bounced|skipp?ed|declin|unsuccessful|not (processed|executed|triggered|deducted|debited|going through)|cancel+ed (automatically|by))|(fail|failed|reject|bounce|skipp?ed|missed).{0,30}(sip|instal+ment|autopay|auto[- ]?debit|payment)|insufficient (balance|fund)|not deducted|not debited|ne...`
- **Exemplar (playstore, Groww):** "the SIPs are not deducted even with adequate account balance and you are then charged ecs bouncing charges"  _(doc PL5c21656f)_
- **Exemplar (playstore, ET Money):** "Missing Sip payment equals cheque bounce in terms of bank charges"  _(doc PL189d19ad)_

### `SI_MANDATE`
- **Definition:** Autopay/e-mandate/NACH/UPI-autopay setup, limits, approval time, expiry, bank not supported, forced mandate
- **Docs coded:** 548 (2.9% of journey-core) | **variant:** and | **holdout:** support 2, P=1.00, R=1.00
- **Regex rule:** `mandates?|auto[- ]?pay|e-?mandate|nach\b|easy ?pay|auto[- ]?debit|upi (autopay|mandate)|debit mandate|mandate (limit|form|expired|approval|rejected)|(1|one) ?lakh limit|25 ?lacs?|autopay (limit|option|fail)|setup autopay|set up auto ?pay`
- **Exemplar (playstore, Paytm Money):** "I am forced to choose the maximum auto debit limit as 25 lacs. Actually you should not force us to choose such a high limit"  _(doc PL27507268)_
- **Exemplar (playstore, Zerodha Coin):** "problem is bank mandate not goes well. You have to add money every month for your SIP installments"  _(doc PL65c8b1bc)_

### `SI_STUCK`
- **Definition:** Money debited but SIP/units not allotted; stuck/pending/processing; NAV-date mismatch; delayed allotment
- **Docs coded:** 152 (0.8% of journey-core) | **variant:** and | **holdout:** support 3, P=0.00, R=0.00
- **Regex rule:** `(money|amount|payment|sip).{0,60}(debited|deducted|held|stuck|blocked|pending|processing|hold).{0,60}(no |not |nothing|yet|still|but)|stuck (in|at) (processing|pending)|(no|not|without) units? (allot|credit|receiv)|units? (not )?(allot|credit)|order (sent to|stuck|pending)|pending (for|since)|still pending|\bnav (of|date|is|was|on)|(next|later|wrong|2 ?days? later|t\+\d) nav|nav (manipulat|delay)|...`
- **Exemplar (playstore, Paytm Money):** "my payment of sip investment is still to be in processing in past 5 days (it usually takes 2-3 days)"  _(doc PL240b5fa7)_
- **Exemplar (reddit):** "My SIP was scheduled for 9th of the month, amount got debited on 9th (early morning) but the units haven't been allotted"  _(doc REaed063c5)_

### `SI_ZOMBIE`
- **Definition:** Cancelled/paused/deleted SIP still debited, re-activated, or notifications/penalties continue
- **Docs coded:** 9 (0.0% of journey-core) | **variant:** and | **holdout:** support 0, P=0.00, R=0.00
- **Regex rule:** `(cancel+ed|paused|pause|deleted|deactivated|stopped|closed|account deleted).{0,60}(still|again|yet|continue|keep).{0,30}(debit|deduct|charged|notification|trigger|reminder|active|reactivat)|(still|again).{0,20}(debit|deduct|charged).{0,40}(cancel|pause|stopp|delet)|unauthori[sz]ed debit|reactivated|became active again|suddenly.{0,20}active|despite (cancel|pausing|stopping)|even (after|if) .{0,20}(...`
- **Exemplar (playstore, Groww):** "Even after raising tickets 4 times, the issue is not yet resolved. Repeatedly getting notifications of failed sip payment, even after the the sip is cancelled 2 months ago"  _(doc PLa79c28b7)_
- **Exemplar (playstore, Groww):** "amount has been debited for a SIP that I didn't want to start"  _(doc PL179cf1d7)_

### `SI_HALT`
- **Definition:** Product-side halt: AMC/fund suspended SIPs or lumpsum (e.g., overseas-fund limits), SIP auto-paused/not resumed, SIP deleted by platform
- **Docs coded:** 217 (1.1% of journey-core) | **variant:** ml | **holdout:** support 3, P=0.33, R=0.67
- **Regex rule:** `(suspend|suspension|stopped (taking|accepting)|stop(ped)? (the )?(fresh|new|lump ?sum)|paus(ed|ing) (by|with)|halt|temporarily (stopped|paused|closed)|closed for|not (accepting|allowing)|cap on|overseas (limit|cap)|\$ ?\d+ ?(billion|bn)|inflows? (stopped|closed|paused)|stopped on (their|its) own|no longer (available|allow)|fund (house|amc) (stopped|paused)|sip (was )?(paused|stopped|cancel+ed|dele...`
- **Exemplar (reddit):** "They have stopped lumpsum last year itself. But recently they have stopped new SIP registrations too"  _(doc RE5250f319)_
- **Exemplar (tradingqna):** "This month, Zerodha placed order for it as usual, but few days later AMC refunded the whole money"  _(doc TRf50ab741)_

## IN-APP - In-app confusion & friction

### `IA_METRICS`
- **Definition:** Confusion/ask about how returns are shown: XIRR vs absolute vs CAGR, NAV vs returns, 'why red', calculation, invested vs current
- **Docs coded:** 348 (1.8% of journey-core) | **variant:** and | **holdout:** support 3, P=0.60, R=1.00
- **Regex rule:** `xirr|\birr\b|absolute (return|gain)|\bcagr\b|how (is|are|do).{0,25}(return|xirr|calculated|calculate)|(return|xirr|profit).{0,40}(match|mismatch|doesn'?t (match|add)|wrong|incorrect|confus|differ)|declared returns?|why (is|are|am|do).{0,30}(red|negative|loss|less|low)|invested (amount|value).{0,40}(current|more|less|wrong|mismatch)|nav (badne|increase|decrease)|(unit|units) (kam|less)|returns? (di...`
- **Exemplar (tradingqna):** "Measuring your returns in XIRR makes sense only for SIPs where the duration of investments is more than 1 year"  _(doc TR3ee7f4e0)_
- **Exemplar (reddit):** "XIRR of my current portfolio is 22.63% and the absolute returns are 33.17%"  _(doc RE71825839)_

### `IA_PAUSE_FRICTION`
- **Definition:** Cannot find/perform pause, cancel, skip, edit amount/date/bank; only 'cancel & recreate'; cancel confusion; mandate/bank switch difficulty
- **Docs coded:** 373 (2.0% of journey-core) | **variant:** ml | **holdout:** support 4, P=0.60, R=0.75
- **Regex rule:** `(no|not|can'?t|cannot|unable|difficult|hard|didn'?t find|couldn'?t find|nowhere|missing).{0,40}(pause|cancel|skip|stop|modify|edit|change|switch|delete|resume|update)|(pause|cancel|skip|stop|modify|edit|change|switch|delete|resume).{0,40}(not (possible|available|allowed|working)|option (is )?(not|missing)|only (option|cancel|delete)|difficult|impossible|nightmare)|(have to|had to|need to|must|only...`
- **Exemplar (tradingqna):** "Will I get Refund if I Stop the SIP After Paying the Initial Investment?"  _(doc TRbd024b0f)_
- **Exemplar (playstore, ET Money):** "I am not able to cancel SIP on this app. They give option to cancel but don't let you cancel the SIP and takes you back to all sips page"  _(doc PL2a92a8ee)_

### `IA_FLEX_GAP`
- **Definition:** Missing/limited flexibility features: weekly/daily/quarterly SIP, flexible date, step-up variants, top-up, SIP in stocks/US stocks, one-shot payment, mandate limit choice, SIP-calendar
- **Docs coded:** 1401 (7.4% of journey-core) | **variant:** ml | **holdout:** support 14, P=0.50, R=0.57
- **Regex rule:** `(weekly|daily|bi[- ]?weekly|fortnightly|quarterly) (sip|option|investment|installment|instalment)|\b(weekly|daily|quarterly) sip|flexible (sip|date|frequency)|(change|modify|edit).{0,15}(sip )?(date|amount)|choose (the )?(sip )?date|sip (in|for) (stocks?|us stocks|etfs?)|stock sip|(feature|option).{0,30}(missing|lack|not available|required|need|add|please)|(please|pls|plz|kindly) (add|provide|incl...`
- **Exemplar (playstore, Zerodha Coin):** "Coin is not sending mobile notification when an SIP order is ready for payment"  _(doc PL896e19cd)_
- **Exemplar (tradingqna):** "Still questions regarding editing the installment amount"  _(doc TR0e4d19f4)_

### `IA_ALERTS`
- **Definition:** Lacks reminders/notifications/status clarity before or after a debit; cannot see upcoming/next SIP, status or totals; wants alerts when SIP skipped/failed
- **Docs coded:** 166 (0.9% of journey-core) | **variant:** and | **holdout:** support 3, P=0.00, R=0.00
- **Regex rule:** `remind(er)?s?\b|notification|notify|alert|intimat|no (message|sms|mail|email|update) (before|about|when|if)|without (letting|informing|intimat|notice)|can'?t (see|know|track).{0,30}(sip|debit|next|upcoming|total)|next (sip|installment|instalment|renewal|due|debit) date|upcoming (sip|debit)|(didn'?t|did not) (get|receive) (any )?(notification|message|alert|sms|mail|email)`
- **Exemplar (playstore, Zerodha Coin):** "person should get a notification to check that proper fund is available in zerodha account for SIP order"  _(doc PL6becdb01)_
- **Exemplar (playstore, Zerodha Coin):** "Please give notifications regarding order processing ,order placed, money added , pending orders,sip reminder when insufficient funds"  _(doc PL86068229)_

### `IA_SUPPORT`
- **Definition:** Support/grievance/refund unresponsive or slow (tickets, email-only, no call, refund delays, blame-shifting to AMC/bank)
- **Docs coded:** 331 (1.7% of journey-core) | **variant:** and | **holdout:** support 2, P=0.40, R=1.00
- **Regex rule:** `customer (care|support|service|executive)|\bsupport\b.{0,40}(poor|bad|worst|pathetic|useless|no (response|reply|help)|not respond|unresponsive|horrible|terrible|slow|never|nobody|no one)|\bticket|raised (a )?(complaint|issue|ticket)|refund|no (response|reply|one (is |was )?(responding|replying|respond))|not (respond|reply|resolv)|(didn'?t|did not|never) (respond|reply|resolve|get back)|helpline|to...`
- **Exemplar (playstore, Groww):** "my Money deducted from my account and that was not added into My SIP"  _(doc PL9d613922)_
- **Exemplar (playstore, ET Money):** "who is the responsible for penalty charged by bank"  _(doc PLc56fd30d)_

### `IA_ONBOARD`
- **Definition:** Onboarding/KYC/account/bank-verification friction before first instalment (KYC pending, video KYC, bank link, account opening, login/OTP)
- **Docs coded:** 47 (0.2% of journey-core) | **variant:** and | **holdout:** support 1, P=0.00, R=0.00
- **Regex rule:** `\bkyc\b|ekyc|e-kyc|video kyc|account (opening|open|creation|verification|activation|not (active|opened|verified))|bank (verification|link|add|account (add|link|verif))|penny ?drop|pan (card|link|verif|mismatch)|verification (pending|failed|issue)|aadhaar|aadhar|onboarding|sign ?up|log ?in (issue|problem|error)|otp (not|issue|problem|never)|nominee|activation|inactive account|account is inactive|ca...`

### `IA_BUG`
- **Definition:** App reliability/UX bugs: portfolio not updating/sync, wrong values, crashes, lag, glitches, duplicate orders, unclear UI
- **Docs coded:** 167 (0.9% of journey-core) | **variant:** ml | **holdout:** support 7, P=0.67, R=0.29
- **Regex rule:** `\bbugs?\b|glitch|crash(es|ed|ing)?\b|\blaggy\b|not (loading|opening|working|updating|syncing|reflecting|refreshing)|server (down|issue|error)|duplicate (order|payment|debit|transaction)|incorrect|wrong (value|data|amount|balance|nav)|(portfolio|dashboard|holdings?).{0,30}(not|wrong|incorrect|zero|missing|disappear|empty|mismatch)|cluttered|after (the )?(latest |recent |new )?update`

### `IA_WITHDRAW`
- **Definition:** Redemption/withdrawal delays, blocked or missing money (trust-eroding exit experience)
- **Docs coded:** 179 (0.9% of journey-core) | **variant:** regex | **holdout:** support 1, P=0.00, R=0.00
- **Regex rule:** `(redeem|redemption|withdraw|withdrawal|exit).{0,60}(delay|stuck|not (received|credited|processed|reflect)|pending|still|days|weeks|month|blocked|failed|error|haven'?t|never)|(money|amount|funds?).{0,40}(stuck|blocked|not (received|credited)|haven'?t received)|(not|never) (able|allowed) to (withdraw|redeem)|can'?t (withdraw|redeem)|(withdraw|redeem)(al)? (request|order)`

## OUTSIDE - What they do outside the app

### `OU_COMMUNITY`
- **Definition:** Posts to community for review/advice/'should I continue/stop' ('rate my portfolio', 'suggestions please')
- **Docs coded:** 1985 (10.4% of journey-core) | **variant:** ml | **holdout:** support 20, P=0.59, R=0.65
- **Regex rule:** `(please|pls|plz|kindly|kind people)? ?(review|rate|critique|evaluate|check|sanity check) (my|the|this).{0,40}(portfolio|sip|plan|allocation|funds?|strategy|investment|mix)|(my|this) (portfolio|sip|allocation|plan|strategy)|any (suggestions?|advice|changes|feedback|thoughts|pointers|inputs|recommendation)|(suggest|advice|advise|guide|help|guidance|feedback|opinion|thoughts).{0,15}(needed|required|p...`
- **Exemplar (reddit):** "My age is 24 and I earn around 38-40k. Please suggest me anything that I can do better"  _(doc RE7e49568b)_
- **Exemplar (reddit):** "I want some opinions on my portfolio, anything redundant I should remove? Or any fund I'm missing out in my portfolio"  _(doc RE43c4bb2e)_

### `OU_COMPARE`
- **Definition:** Compares SIP/MF with alternatives: FD/RD/PPF, index/Nifty, gold/silver, real estate, stocks, other apps/brokers, direct vs regular
- **Docs coded:** 1947 (10.2% of journey-core) | **variant:** and | **holdout:** support 6, P=0.20, R=0.33
- **Regex rule:** `\b(fd|fixed deposit|rd|ppf|nps|gold|real estate)\b.{0,40}(vs|or|better|instead|compare|rather)|\b(vs|versus|compare|compared|comparison|better than|instead of|rather than)\b|sip (vs|or) lump|lump ?sum (vs|or)|direct (vs|or) regular|other apps?|(switch|shift|moved?)(ed)? (from|to) (groww|zerodha|coin|kuvera|et ?money|indmoney|paytm|lemonn)|(index fund|etf).{0,30}(vs|or|instead|better)|\bfd\b`
- **Exemplar (reddit):** "Stop all voluntary investments like SIP, FD, gold and continue with epf, term insurance premium, health insurance premium"  _(doc REee8036a3)_

### `OU_CREATOR`
- **Definition:** Learns from/asks YouTube creators, finfluencers, books, podcasts ('your video', 'sir make a video', 'as per X')
- **Docs coded:** 478 (2.5% of journey-core) | **variant:** ml | **holdout:** support 5, P=1.00, R=0.80
- **Regex rule:** `your (video|videos|channel|content|podcast|playlist)|(make|made|create|do|upload) (a |one )?(detailed |full )?(video|series|playlist)|video (on|about|please|plz|banao|banaye)|(watched|watching|saw|seen).{0,20}(video|channel|reel|podcast|youtube)|youtube(r|rs)?|finfluencer|influencer|podcast|pranjal|kamra|rachana|ranade|warikoo|labour law|freefincal|varsity`
- **Exemplar (youtube):** "Please make a video on today's market condition where there is a issue of smallcap and Midcap mutual funds not accepting the sip"  _(doc YO3c1a4e8c)_

### `OU_PEOPLE`
- **Definition:** Consults/was influenced by friends, family, bank RM, distributor/agent, advisor in person
- **Docs coded:** 287 (1.5% of journey-core) | **variant:** or | **holdout:** support 1, P=0.33, R=1.00
- **Regex rule:** `(friend|colleague|cousin|relative|parent|dad|father|mother|brother|wife|husband)s?.{0,40}(said|says|told|suggest|advis|recommend)|(bank|relationship manager|\brm\b|distributor|agent|advisor|adviser|\bria\b|financial planner|broker).{0,50}(told|said|suggest|sold|mis ?sold|recommend|advis|commission|push|pitch)|(my|our) (advisor|adviser|distributor|agent|banker|rm|financial planner)`

### `OU_TRACKER`
- **Definition:** Uses/needs external tracker, import/consolidation (CAS, MFCentral, spreadsheet, other app) to see SIP/portfolio
- **Docs coded:** 898 (4.7% of journey-core) | **variant:** or | **holdout:** support 0, P=0.00, R=0.00
- **Regex rule:** `(external|outside|other) (mf|mutual fund|portfolio|holdings?|investments?|funds?|folios?)|import(ing)? (my )?(existing|external|portfolio|data|funds?|sips?)|consolidated|\bcas\b|mf ?central|mfu\b|spreadsheet|excel|google sheet|track(er|ing)? (all|my|everything)|tracking app|track (my|all) (investment|sip|portfolio)|existing folio|add (existing|my)? ?folio|all (investments?|funds?) (in|at) (one|sin...`
- **Exemplar (playstore, Zerodha Coin):** "Show daily growth 2. Show IRR/XIRR 3. Show the complete amount not 2.1L. 4. Reduce the minimum investment amount to 500"  _(doc PLbc071180)_

## CONTINUE - What continuers say/do

### `CO_THROUGH`
- **Definition:** Continued/continues SIP through dips or tells others not to stop (evidence of persistence or norm)
- **Docs coded:** 528 (2.8% of journey-core) | **variant:** and | **holdout:** support 7, P=0.50, R=0.43
- **Regex rule:** `(don'?t|do not|never|didn'?t|did not|won'?t|will not|wouldn'?t) (stop|pause|cancel|discontinue|exit|touch|interfere|break|quit)|never (stopped|paused|missed|skipped)|kept (doing|going|investing|my sip)|keep(ing)? (doing|going|investing) (my |the )?(sip|on)?|continu(e|ed|ing|es) (my |the |our |with )?(sip|invest|doing)|still (doing|continu|investing|running)|stay(ed)? invested|religiously|haven'?t ...`
- **Exemplar (youtube):** "I never stop SIP whether the market is up or down"  _(doc YOc3486774)_
- **Exemplar (reddit):** "So never skipped any SIp"  _(doc RE587906c7)_

### `CO_AUTOMATE`
- **Definition:** Credits automation/autopay/'set and forget'/discipline/habit for persistence ('put and forget', 'no decisions', 'removes emotion')
- **Docs coded:** 426 (2.2% of journey-core) | **variant:** ml | **holdout:** support 6, P=0.25, R=0.17
- **Regex rule:** `set and forget|put and forget|set it and forget|fire and forget|forget (about )?it|automat(e|ed|ic|ion|ically)|auto[- ]?pilot|take(s)? the emotion|remov(e|es|ing) (the )?emotion|no (need|decision)|disciplin|on autopilot|don'?t (look|check|track)|without (looking|checking|thinking)`
- **Exemplar (reddit):** "I've been doing SIP with auto-pay without any problem"  _(doc RE8f8e74a6)_
- **Exemplar (reddit):** "Staying consistent with your SIPs keeps you disciplined and turns market ups and downs to your advantage"  _(doc RE3438204c)_

### `CO_LONGTERM`
- **Definition:** Long-horizon belief: compounding, time in market, rupee-cost-averaging, 'markets recover', 5-10+ years
- **Docs coded:** 1439 (7.5% of journey-core) | **variant:** and | **holdout:** support 3, P=0.09, R=0.33
- **Regex rule:** `long[- ]?term|long run|compound(ing)?|time in (the )?market|rupee[- ]cost|cost averaging|\brca\b|average(s|d)? out|markets? (will|always|would|can) (recover|go up|bounce|rise|rebound)|(10|15|20|25|30)\+? ?(yrs?|years?)|decades?|stay invested`

## Opportunity areas (groups of codes used in the scorecard)

| area | name | codes | mechanism_rating_1to5 | why |
|---|---|---|---|---|
| A1 | Instalment failure & autopay/mandate reliability | SI_FAILED, SI_MANDATE | 5 | A failed or un-set-up debit is by definition a missing 'successful instalment in the last 30 days'. |
| A2 | Debit/allotment integrity: stuck, zombie & halted SIPs | SI_STUCK, SI_ZOMBIE, SI_HALT | 4 | Money debited but not allotted, cancelled SIPs still debiting, or product-side halts break trust and the instalment trail. |
| A3 | Pause / edit / cancel friction & schedule flexibility | IA_PAUSE_FRICTION, IA_FLEX_GAP | 4 | If the only way to cope with a bad month is cancel-and-recreate, a temporary shock becomes a permanent stop. |
| A4 | Cash-flow shocks & affordability | SV_CASH | 4 | EMI, job/income change or expenses are stated stop reasons; a graceful reduce/pause path may retain the habit. |
| A5 | Status visibility, reminders & unnoticed lapses | IA_ALERTS | 4 | Users who cannot see what will be debited, or never notice a skip, drift out without a decision. |
| A6 | Returns comprehension & expectation gap (XIRR/absolute/NAV, 'why red') | IA_METRICS, BH_RED, BH_UNDERWHELM, SV_RETURNS, ST_EXPECT_RET | 4 | Early statements look flat or red; mis-read metrics and unanchored expectations feed the 'underwhelming first statements' drop. |
| A7 | Market-dip behaviour: timing, skipping, stopping | SV_MARKET, BH_TIMING | 4 | Users pause/skip or try to time dips; calm, non-fear context during drawdowns is the design space. |
| A8 | Support, refund, withdrawal & app-reliability trust | IA_SUPPORT, IA_WITHDRAW, IA_BUG, SV_DISTRUST, SV_FEES | 3 | Unresolved issues and exit pain erode the willingness to keep money flowing. |
| A9 | First-SIP set-up, KYC & beginner guidance | IA_ONBOARD, ST_NEED_GUIDE | 3 | Sets the starting cohort: friction before the first instalment and unanswered 'how much / which / how' questions. |
| A10 | Off-app reliance: communities, creators, comparisons & switching | OU_COMMUNITY, OU_COMPARE, OU_CREATOR, OU_PEOPLE, OU_TRACKER, SV_SWITCH | 3 | When unsure, users ask strangers 'should I continue?' or compare/switch platforms; the app is not their decision-support source. |

**Revision note:** after the precision audit, `BH_FORGET` was removed from area A5 (audit precision 0/20: it mostly matched 'set and forget' advice) and A5 uses the regex-only `IA_ALERTS` rule (the AND-variant kept only 10 documents).
