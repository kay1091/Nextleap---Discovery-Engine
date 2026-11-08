import re
# ---------- lexicons shared by cleaning / coding ----------
SIP_RE = re.compile(r"\bsips?\b|systematic investment|instal+ments?|\binstalments?\b|mandates?\b|auto-?pay|\bnach\b|e-?mandate|step[- ]?up|top[- ]?up", re.I)
MF_RE = re.compile(r"mutual ?funds?|\bmfs?\b|\bnav\b|xirr|\bcagr\b|\belss\b|index fund|nifty ?(50|next)|flexi ?cap|small ?cap|mid ?cap|large ?cap|\bfolio|units? (allot|credit)|direct plan|regular plan|expense ratio|lump ?sum|fund house|\bamc\b|rupee cost|cost averaging|redeem|redemption|\bfd\b|fixed deposits?|\bppf\b|\bnps\b|portfolio|absolute returns?", re.I)
FIN_CTX_RE = re.compile(r"invest|mutual|fund|market|nifty|sensex|returns?|rs\.?\s?\d|₹|nav|groww|zerodha|coin|indmoney|kuvera|etmoney|et money|paytm money|bank|debit|deduct|portfolio|units|stock|equity|month|monthly|amc|kyc|upi|pause|stop|cancel|continue", re.I)
FIRST_PERSON_RE = re.compile(r"\b(i|i'm|im|i've|ive|i'd|my|me|mine|we|our|myself)\b|\b(maine|mai|main|mera|meri|mere|humne|hum|mujhe|apna)\b|\b(naan|enakku|en|nan)\b", re.I)
BEHAV_RE = re.compile(r"\b(stopp?ed|paus(e|ed|ing)|cancel+(ed|led)?|discontinu(e|ed)|continu(e|ed|ing)|started|start(ing)?|began|quit|skipp?ed|missed|reduc(e|ed)|increas(e|ed)|redeem(ed)?|withdr[ae]w|invest(ed|ing)?)\b|band kar|bandh|rok(a|na|ne|diya)|shuru|chalu|bachat", re.I)
FIRST_TIME_RE = re.compile(r"first[- ]time|first sip|first (mutual|investment|fund)|new (to|investor)|newbie|beginner|just start(ed)?|start(ed)? investing|never invested|fresher|first job|first salary|started (my )?(sip|investing|investment)|\bnoob\b|new to (investing|mutual|sip|stock)|started (a |my )?sip|\bshuru kiya\b|pehli (baar|sip)", re.I)
PRODUCT_RES = {
 "Groww": re.compile(r"\bgroww?\b|\bgrow app\b", re.I),
 "Zerodha Coin": re.compile(r"\bcoin\b(?! ?(price|flip|toss|market))|zerodha|\bkite\b", re.I),
 "INDmoney": re.compile(r"ind ?money", re.I),
 "Kuvera": re.compile(r"kuvera", re.I),
 "ET Money": re.compile(r"\bet ?money\b|etmoney", re.I),
 "Paytm Money": re.compile(r"paytm ?money", re.I),
 "Upstox": re.compile(r"upstox", re.I),
 "Angel One": re.compile(r"angel ?(one|broking)", re.I),
 "HDFC Sky": re.compile(r"hdfc ?sky", re.I),
 "Bank app/Direct AMC": re.compile(r"\b(sbi|hdfc|icici|axis|kotak)\b.{0,15}(app|netbanking|net banking|yono|mutual)|direct (from )?amc|mf ?central|\bcams\b|kfin", re.I),
 "Smallcase/Others": re.compile(r"smallcase|cred\b|phonepe|google ?pay|gpay|navi\b|jar\b|bajaj", re.I),
}
HINGLISH = set("kya hai hain nahi nahin kar karna karne karo kiya kiye karu karun mera meri mere mai main maine tum aap ke ki ko se par pe liye lia bhi sab kuch koi toh to ho hoga hogi hota hoti raha rahi rahe diya gaya gayi gaye wala wali aur ya lekin lekin paisa paise rupaye sahi galat accha achha bahut bohot thoda zyada kam abhi kab kyun kyu kaise kaisa kitna kitne chahiye chahie band chalu shuru bata batao bhai yaar sir madam mat mujhe humko hum unka uska iska isme usme jab tab agar warna fir phir sirf bas hi nhi nhi h hu hun tha thi the lagta lagi lag samajh samjha".split())
TANGLISH = set("panra pannunga pannu panren irukku irukkum illa illai enna romba sollunga epdi eppadi vanga vendam venum seri nalla theriyala theriyum paaru paarunga machan bro nanba anna thambi seyya seiyum kudukka kidaikkum aana aanaa illama".split())
def script_ratio(t):
    letters=[c for c in t if c.isalpha()]
    if not letters: return {}
    def frac(lo,hi): return sum(lo<=ord(c)<=hi for c in letters)/len(letters)
    return {"hi":frac(0x900,0x97F),"bn":frac(0x980,0x9FF),"gu":frac(0xA80,0xAFF),"ta":frac(0xB80,0xBFF),"te":frac(0xC00,0xC7F),"kn":frac(0xC80,0xCFF),"ml":frac(0xD00,0xD7F)}
def detect_lang(t):
    sr=script_ratio(t)
    for k,v in sr.items():
        if v>0.4: return {"hi":"hindi","ta":"tamil","te":"telugu","bn":"bengali","gu":"gujarati","kn":"kannada","ml":"malayalam"}[k]
    if sum(sr.values())>0.15: return "mixed-indic-script"
    toks=re.findall(r"[a-z']+",t.lower())
    if len(toks)<3: return "short"
    h=sum(w in HINGLISH for w in toks); ta=sum(w in TANGLISH for w in toks)
    if ta>=2 or (ta>=1 and ta/len(toks)>0.08): return "tanglish"
    if h>=3 and h/len(toks)>=0.15: return "hinglish"
    try:
        from langdetect import detect, DetectorFactory
        DetectorFactory.seed=0
        l=detect(t)
        return "english" if l=="en" else f"other:{l}"
    except Exception: return "unknown"
