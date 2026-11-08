import json

from pipeline import (
    normal_record, dedupe, privacy_clean, read_import,
    validate_analysis, eval_gold, to_csv_bytes,
    analyze_with_openrouter, summary,
)


def example():
    return normal_record(
        'manual_pilot_excerpts', 'https://example.com/item', '2026-10-01',
        'I started my first SIP and my payment failed.', None,
    )


def test_privacy():
    s = privacy_clean('Email person@example.com mobile 9876543210 pan ABCDE1234F')
    assert 'person@example.com' not in s
    assert '9876543210' not in s
    assert 'ABCDE1234F' not in s


def test_dedupe():
    a = example()
    b = normal_record('another', 'https://example.com/b', '', a['text'])
    assert len(dedupe([a, b])) == 1


def test_import_requires_source():
    data = 'text,source_url,source_date\n"SIP failed",https://example.com,2026-10-01\n"missing URL",,2026-10-01\n'
    assert len(read_import(data)) == 1


def test_invented_excerpt_flagged():
    obj = {
        'relevance': 'sip_relevant', 'theme': 'payment_failure',
        'sip_behavior': 'missed', 'first_time_status': 'confirmed',
        'groww_status': 'confirmed', 'evidence_excerpt': 'imaginary quote',
    }
    x = validate_analysis(example(), obj)
    assert x['needs_human_review'] is True
    assert x['evidence_excerpt'] == ''
    assert x['groww_status'] == 'unknown'


def test_gold_missing_is_mismatch():
    human = [{'record_id': 'a', 'relevance': 'sip_relevant', 'theme': 'payment_failure', 'sip_behavior': 'missed'}]
    x = eval_gold(human, [])
    assert x['fields']['relevance']['correct'] == 0


def test_spreadsheet_export_safe():
    out = to_csv_bytes([{'text': '=1+1'}]).decode('utf-8-sig')
    assert "'=1+1" in out


class FakeResponse:
    ok = True
    status_code = 200
    def __init__(self, content, finish='stop'):
        self.content = content
        self.finish = finish
    def json(self):
        return {
            'model': 'mock/model',
            'choices': [{'finish_reason': self.finish, 'message': {'content': self.content}}],
        }


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []
    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_openrouter_valid_classification():
    payload = {
        'relevance': 'sip_relevant', 'theme': 'payment_failure',
        'sip_behavior': 'missed', 'first_time_status': 'confirmed',
        'groww_status': 'unknown', 'trigger': 'payment failed',
        'need': 'payment recovery guidance', 'evidence_excerpt': 'my payment failed',
        'confidence': 0.93, 'needs_human_review': False, 'review_reason': '',
    }
    fake = FakeSession(FakeResponse(json.dumps(payload)))
    out = analyze_with_openrouter([example()], 'test-not-real', session=fake)
    assert out[0]['analysis_status'] == 'classified'
    assert out[0]['theme'] == 'payment_failure'
    assert fake.calls[0][1]['json']['model'] == 'openrouter/free'
    assert fake.calls[0][1]['headers']['Authorization'] == 'Bearer test-not-real'


def test_openrouter_empty_completion_abstains():
    fake = FakeSession(FakeResponse('', 'length'))
    out = analyze_with_openrouter([example()], 'test-not-real', session=fake)
    assert out[0]['analysis_status'] == 'abstained'
    assert out[0]['confidence'] == 0
    assert summary([example()], out)['sip_relevant'] == 0


def test_openrouter_http_400_abstains():
    response = FakeResponse('')
    response.ok = False
    response.status_code = 400
    out = analyze_with_openrouter([example()], 'test-not-real', session=FakeSession(response))
    assert out[0]['analysis_status'] == 'abstained'
    assert '400' in out[0]['review_reason']


def test_openrouter_empty_json_does_not_count_as_classification():
    out = analyze_with_openrouter([example()], 'test-not-real', session=FakeSession(FakeResponse('{}')))
    assert out[0]['analysis_status'] == 'abstained'


def test_openrouter_unverified_quote_requires_review():
    obj = {
        'relevance': 'sip_relevant', 'theme': 'payment_failure',
        'sip_behavior': 'missed', 'first_time_status': 'confirmed',
        'groww_status': 'unknown', 'trigger': 'payment failed',
        'need': 'help', 'evidence_excerpt': 'invented quotation',
        'confidence': 0.95, 'needs_human_review': False, 'review_reason': '',
    }
    out = analyze_with_openrouter([example()], 'test-not-real', session=FakeSession(FakeResponse(json.dumps(obj))))
    assert out[0]['needs_human_review'] is True
    assert out[0]['evidence_excerpt'] == ''
