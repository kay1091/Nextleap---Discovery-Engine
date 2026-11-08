import json
from pipeline import normal_record, dedupe, privacy_clean, read_import, validate_analysis, eval_gold, THEMES

def test_privacy():
    s=privacy_clean('Email person@example.com mobile 9876543210 pan ABCDE1234F')
    assert 'person@example.com' not in s and '9876543210' not in s and 'ABCDE1234F' not in s

def test_dedupe():
    a=normal_record('apple','https://example.com/a','2026-10-01','My SIP failed',1)
    b=normal_record('play','https://example.com/b','2026-10-02','My SIP failed',1)
    assert len(dedupe([a,b]))==2  # two independent reviewers must remain distinct

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
        def json(self):return {'feed':{'entry':[{'title':{'label':'Good'},'content':{'label':'My first SIP was easy'},'im:rating':{'label':'5'},'id':{'label':'123456789'},'link':{'attributes':{'href':'https://apps.apple.com/in/app/id1404871703?see-all=reviews&reviewId=123456789'}},'updated':{'label':'2026-10-01'}}]}}
    class Session:
        def get(self,*args,**kwargs):return Response()
    rec=apple_feed(session=Session(),pages=1)
    assert len(rec)==1 and rec[0]['rating']==5 and 'My first SIP' in rec[0]['text']


def test_csv_formula_safe():
    from pipeline import to_csv_bytes
    out=to_csv_bytes([{'text':'=HYPERLINK("malicious")','source_url':'https://example.com'}]).decode('utf-8-sig')
    assert "'=HYPERLINK" in out


def test_openrouter_sends_chat_completions_and_validates(monkeypatch):
    from pipeline import analyze_with_openrouter, normal_record
    record=normal_record('apple_app_store', 'https://example.com/a', '2026-10-01',
                         'My SIP failed yesterday and I missed an instalment')
    calls=[]
    class Response:
        ok=True
        status_code=200
        def json(self):
            return {'choices':[{'message':{'content':json.dumps({
                'relevance':'sip_relevant', 'theme':'payment_failure',
                'sip_behavior':'missed','first_time_status':'unknown',
                'groww_status':'confirmed',
                'trigger':'payment failure', 'need':'retry help',
                'evidence_excerpt':'My SIP failed yesterday',
                'confidence':0.9,'needs_human_review':False,'review_reason':''
            })},'finish_reason':'stop'}]}
    def fake_post(url, **kwargs):
        calls.append((url,kwargs))
        return Response()
    monkeypatch.setattr('pipeline.requests.post',fake_post)
    output=analyze_with_openrouter([record],'dummy-key','openrouter/free')
    assert len(output)==1 and output[0]['theme']=='payment_failure'
    assert calls[0][0]=='https://openrouter.ai/api/v1/chat/completions'
    assert calls[0][1]['json']['model']=='openrouter/free'
    assert calls[0][1]['json']['messages'][0]['role']=='system'
    assert calls[0][1]['headers']['Authorization']=='Bearer dummy-key'


def test_openrouter_empty_or_http_error_abstains(monkeypatch):
    from pipeline import analyze_with_openrouter, normal_record
    rec=normal_record('apple_app_store', 'https://example.com/a', '2026-10-01','My SIP failed')
    class EmptyResponse:
        ok=True
        status_code=200
        def json(self): return {'choices':[{'message':{'content':''}, 'finish_reason':'length'}]}
    monkeypatch.setattr('pipeline.requests.post',lambda *a,**kw: EmptyResponse())
    out=analyze_with_openrouter([rec],'test')
    assert out[0]['needs_human_review'] is True
    assert out[0]['relevance']=='uncertain'
    assert 'token limit' in out[0]['review_reason']
    class ErrorResponse:
        ok=False
        status_code=429
    monkeypatch.setattr('pipeline.requests.post',lambda *a,**kw: ErrorResponse())
    out=analyze_with_openrouter([rec],'test')
    assert out[0]['relevance']=='uncertain' and 'HTTP 429' in out[0]['review_reason']


def test_apple_uses_review_link_and_not_numeric_id():
    from pipeline import apple_feed
    class Response:
        status_code = 200
        def json(self):
            return {'feed': {'entry': [{
                'id': {'label': '987654321'},
                'link': {'attributes': {'href': 'https://apps.apple.com/in/app/id1404871703?reviewId=987654321'}},
                'title': {'label': 'SIP question'}, 'content': {'label': 'My SIPs are working'},
                'im:rating': {'label': '4'}, 'updated': {'label': '2026-11-07'}
            }]}}
    class Session:
        def get(self, *args, **kwargs):
            return Response()
    rows = apple_feed(session=Session(), pages=1)
    assert rows[0]['source_url'].endswith('reviewId=987654321')
    assert rows[0]['rating'] == 4


def test_plural_sip_and_first_time_evidence():
    from pipeline import validate_analysis, normal_record
    row = normal_record('apple_app_store', 'https://example.com/review', '',
                        'My SIPs are fine, on the first of every month.')
    result = validate_analysis(row, {
        'relevance': 'sip_relevant', 'theme': 'positive_experience',
        'sip_behavior': 'continuing', 'first_time_status': 'confirmed',
        'groww_status': 'confirmed', 'confidence': 0.95,
        'needs_human_review': 'false'
    })
    assert result['relevance'] == 'sip_relevant'
    assert result['first_time_status'] == 'unknown'
    assert result['needs_human_review'] is True
    assert 'First-time status' in result['review_reason']


def test_json_import_malformed_rows_and_stable_ids():
    from pipeline import read_import
    a = [
        {'text': 'I have a SIP', 'source_url': 'https://example.com/a', 'rating': '4'},
        None, {'text': 'no URL', 'source_url': 123},
        {'text': 'Mutual funds', 'source_url': 'https://example.com/b', 'rating': '2'}
    ]
    first = read_import(json.dumps(a), filename='approved.json')
    second = read_import(json.dumps(list(reversed(a))), filename='approved.json')
    assert len(first) == 2
    assert {x['record_id'] for x in first} == {x['record_id'] for x in second}
    assert all(isinstance(x['rating'], int) for x in first)


def test_import_csv_restore_and_formula_escaping():
    from pipeline import load_export_csv, to_csv_bytes
    original = [{'record_id':'abc', 'relevance':'sip_relevant',
                 'theme':'payment_failure','needs_human_review':False,
                 'confidence':0.85,'retryable':False}]
    restored = load_export_csv(to_csv_bytes(original), 'analysis')
    assert restored[0]['record_id'] == 'abc'
    assert restored[0]['needs_human_review'] is False
    assert restored[0]['confidence'] == 0.85


def test_retryable_429_and_empty_response():
    from pipeline import empty_analysis, is_retryable_abstention
    row = {'record_id':'x'}
    assert is_retryable_abstention(empty_analysis(row,'OpenRouter HTTP 429; abstain.',retryable=True))
    assert is_retryable_abstention(empty_analysis(row,'OpenRouter returned empty classification; abstain.',retryable=True))
    assert not is_retryable_abstention(empty_analysis(row,'Unsupported first-time status',retryable=False))


def test_kappa_confusion_and_human_match():
    from pipeline import eval_gold
    gold = [
        {'record_id':'1','relevance':'sip_relevant','theme':'payment_failure','sip_behavior':'stopped'},
        {'record_id':'2','relevance':'not_sip_related','theme':'not_sip_related','sip_behavior':'unknown'},
    ]
    ai = [
        dict(gold[0]), dict(gold[1])
    ]
    result=eval_gold(gold,ai)
    assert result['fields']['relevance']['correct']==2
    assert result['fields']['relevance']['cohen_kappa']==1
    assert result['fields']['relevance']['confusion_matrix']['sip_relevant']['sip_relevant']==1


def test_apify_sends_bearer_not_query_token(monkeypatch):
    from pipeline import play_apify
    observed={}
    class Response:
        status_code=200
        def json(self):
            return [{'reviewId':'p1','text':'My SIPs','date':'2026-11-07','rating':'5'}]
    def mock_post(url, **kwargs):
        observed.update(kwargs)
        return Response()
    monkeypatch.setattr('pipeline.requests.post', mock_post)
    rows=play_apify('test-private-token')
    assert observed['headers']['Authorization']=='Bearer test-private-token'
    assert 'token' not in observed.get('params',{})
    assert rows[0]['rating']==5


def test_privacy_extended_patterns():
    from pipeline import privacy_clean
    text='UPI: person@okhdfc phone +91 98765 43210 and aadhaar 1234 5678 9012'
    cleaned=privacy_clean(text)
    assert 'person@okhdfc' not in cleaned
    assert '98765 43210' not in cleaned
    assert '1234 5678 9012' not in cleaned


def test_json_prose_prefix_parsed():
    from pipeline import parse_model_json
    obj=parse_model_json('Here is the result: {"relevance":"uncertain","confidence":0.8} rest')
    assert obj['relevance']=='uncertain'
