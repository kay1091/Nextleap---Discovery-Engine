import json
from pipeline import normal_record, dedupe, privacy_clean, read_import, validate_analysis, eval_gold, THEMES

def test_privacy():
    s=privacy_clean('Email person@example.com mobile 9876543210 pan ABCDE1234F')
    assert 'person@example.com' not in s and '9876543210' not in s and 'ABCDE1234F' not in s

def test_dedupe():
    a=normal_record('apple','https://example.com/a','2026-10-01','My SIP failed',1)
    b=normal_record('play','https://example.com/b','2026-10-02','My SIP failed',1)
    assert len(dedupe([a,b]))==1

def test_import_source_required():
    rows='text,source_url,source_date\n"a SIP issue",https://example.com,2026-10-01\n"another SIP issue",,2026-10-01\n'
    assert len(read_import(rows))==1

def test_hallucinated_excerpt_abstained():
    a=normal_record('reddit_approved','https://example.com','2026-10-01','I stopped my monthly SIP.',None)
    model={'relevance':'sip_relevant','theme':'affordability','sip_behavior':'stopped',
      'first_time_status':'confirmed','groww_status':'confirmed','evidence_excerpt':'my salary was cut','confidence':0.9}
    x=validate_analysis(a,model)
    assert x['first_time_status']=='unknown'
    assert x['groww_status']=='unknown'
    assert x['needs_human_review'] is True
    assert x['evidence_excerpt']==''

def test_gold_missing_counts_mismatch():
    gold=[{'record_id':'1','relevance':'sip_relevant','theme':'affordability','sip_behavior':'stopped'}]
    res=eval_gold(gold,[])
    assert res['fields']['theme']['correct']==0
    assert not res['ready_for_assignment']

def test_youtube_video_validation():
    from pipeline import youtube_comments
    import pytest
    with pytest.raises(ValueError):
        youtube_comments('key','not a video id')


def test_apple_feed_parse_with_offline_fixture():
    from pipeline import apple_feed
    class Response:
        status_code=200
        def raise_for_status(self): pass
        def json(self):return {'feed':{'entry':[{'title':{'label':'Good'},'content':{'label':'My first SIP was easy'},'im:rating':{'label':'5'},'id':{'label':'https://example.com/123'},'updated':{'label':'2026-10-01'}}]}}
    class Session:
        def get(self,*args,**kwargs):return Response()
    rec=apple_feed(session=Session(),pages=1)
    assert len(rec)==1 and rec[0]['rating']==5 and 'My first SIP' in rec[0]['text']


def test_csv_formula_safe():
    from pipeline import to_csv_bytes
    out=to_csv_bytes([{'text':'=HYPERLINK("malicious")','source_url':'https://example.com'}]).decode('utf-8-sig')
    assert "'=HYPERLINK" in out
