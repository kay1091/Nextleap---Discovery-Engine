"""Launch with: streamlit run app.py"""
import json
import os
import hashlib
import hmac
from pathlib import Path
import pandas as pd
import streamlit as st
from pipeline import (apple_feed, play_apify, youtube_comments, read_import, dedupe,
    analyze_with_openrouter, eval_gold, summary, to_csv_bytes, THEMES, BEHAVIORS, RELEVANCE,
    load_export_csv, prefilter_records, is_retryable_abstention, privacy_clean)

st.set_page_config(page_title='Groww SIP | AI Discovery Engine',page_icon='🔎',layout='wide')
st.title('Groww SIP · AI Discovery Engine')
st.caption('Research tool · Public voice-of-customer evidence · OpenRouter-supported classification · Not investment advice')
st.info('Research data ≠ Groww cohort analytics. Public reviews cannot establish actual 12-month SIP retention or investor status unless stated.')

for key,default in [('records',[]),('analysis',[]),('gold',{}),('errors',[]),('api_calls',0)]:
    if key not in st.session_state: st.session_state[key]=default


def get_secret(name, default=''):
    try:
        return st.secrets.get(name, os.environ.get(name, default))
    except Exception:
        return os.environ.get(name, default)

admin_secret = str(get_secret('DISCOVERY_ADMIN_PASSWORD', '') or '')
with st.sidebar:
    st.header('Settings')
    admin_input = st.text_input('Administrator passcode', type='password',
        help='Only the administrator can collect, import, label or call external APIs.')
    is_admin = bool(admin_secret and hmac.compare_digest(admin_input, admin_secret))
    if not admin_secret:
        st.warning('Administrator passcode not configured. All write/API actions are locked.')
    elif is_admin:
        st.success('Administrator mode enabled')
    else:
        st.info('Read-only mode. Enter the passcode to run research or analysis.')

    api_key=os.environ.get('OPENROUTER_API_KEY','')
    try:
        api_key=st.secrets.get('OPENROUTER_API_KEY',api_key)
    except Exception:
        pass
    if not api_key and is_admin:
        api_key=st.text_input('OpenRouter API key (session only)',type='password')
    apify=get_secret('APIFY_TOKEN') or (st.text_input('Apify token (optional)',type='password') if is_admin else '')
    youtube_key=get_secret('YOUTUBE_API_KEY') or (st.text_input('YouTube API key (optional)',type='password') if is_admin else '')
    default_model=os.environ.get('OPENROUTER_MODEL','openrouter/free')
    try:
        default_model=st.secrets.get('OPENROUTER_MODEL',default_model)
    except Exception:
        pass
    model=st.text_input('OpenRouter model',value=default_model)
    st.caption('Set secrets as environment variables on deployment; never commit API tokens.')
    st.metric('Collected unique records',len(st.session_state.records))
    st.metric('OpenRouter classifications',len(st.session_state.analysis))
    st.metric('Human gold labels',len(st.session_state.gold))
    st.metric('API calls this session',st.session_state.api_calls)
    st.caption('Download all three CSV exports before the session ends.')
    with st.expander('Restore previous CSV exports'):
        source_restore=st.file_uploader('Restore source records CSV',type='csv',key='source_restore')
        analysis_restore=st.file_uploader('Restore AI classifications CSV',type='csv',key='analysis_restore')
        gold_restore=st.file_uploader('Restore human gold labels CSV',type='csv',key='gold_restore')
        if st.button('Restore selected files',disabled=not is_admin):
            try:
                if source_restore:
                    restored=load_export_csv(source_restore.getvalue(),'source')
                    st.session_state.records=dedupe(st.session_state.records+restored)
                if analysis_restore:
                    restored=load_export_csv(analysis_restore.getvalue(),'analysis')
                    by_id={x['record_id']:x for x in st.session_state.analysis}
                    by_id.update({x['record_id']:x for x in restored})
                    st.session_state.analysis=list(by_id.values())
                if gold_restore:
                    restored=load_export_csv(gold_restore.getvalue(),'gold')
                    st.session_state.gold.update({x['record_id']:x for x in restored})
                st.success('Valid CSV records restored. Verify counts before continuing.')
            except (ValueError, KeyError, TypeError):
                st.error('Restore failed. Check that the selected files are valid exports.')
    st.divider()
    st.markdown('**Compliance**: Reddit/forum inputs must be separately authorized. This app does not bypass login, rate limits, or site restrictions.')

collect, analyze, evidence, gold = st.tabs(['1 · Collect', '2 · Analyze', '3 · Evidence & themes', '4 · Human evaluation'])

with collect:
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Apple India public reviews')
        pages=st.slider('Recent pages (up to 10)',min_value=1,max_value=5,value=1)
        if st.button('Fetch Apple reviews',disabled=not is_admin):
            try:
                with st.spinner('Collecting limited public feed...'):
                    fetched=apple_feed(pages=pages)
                before=len(st.session_state.records)
                st.session_state.records=dedupe(st.session_state.records+fetched)
                st.success(f'Fetched {len(fetched)}; added {len(st.session_state.records)-before} unique records.')
            except Exception:st.error('Apple collection unavailable. Check connectivity and source permissions.')
        st.caption('Public RSS provides a limited recent window, not every historical review.')
    with c2:
        st.subheader('Google Play via Apify')
        max_reviews=st.slider('Maximum reviews',50,500,100,50)
        accepted=st.checkbox('I have reviewed the source/provider terms and accept provider charges.')
        if st.button('Fetch Play reviews',disabled=not(is_admin and apify and accepted)):
            try:
                with st.spinner('Fetching Play reviews through third-party connector...'):
                    fetched=play_apify(apify,max_reviews=max_reviews)
                before=len(st.session_state.records)
                st.session_state.records=dedupe(st.session_state.records+fetched)
                st.success(f'Fetched {len(fetched)}; added {len(st.session_state.records)-before} unique records.')
            except Exception:st.error('Google Play collection unavailable; check provider quota, permissions and configuration.')
        st.caption('Third-party, non-official collector; not guaranteed complete. No direct developer reviews API access to Groww.')
    st.divider()
    st.subheader('YouTube comments (official API)')
    st.write('Select a public Indian SIP/personal-finance video manually. The official API fetches recent top-level comments; not all replies.')
    video_id=st.text_input('YouTube video ID (11 characters)')
    ypages=st.slider('YouTube pages',1,3,1)
    if st.button('Fetch YouTube comments',disabled=not(is_admin and youtube_key and video_id.strip())):
        try:
            out=youtube_comments(youtube_key,video_id.strip(),pages=ypages)
            old=len(st.session_state.records)
            st.session_state.records=dedupe(st.session_state.records+out)
            st.success(f'Fetched {len(out)}; added {len(st.session_state.records)-old} unique comments.')
        except Exception:st.error('YouTube collection unavailable; check API quota and video ID.')
    st.divider()
    st.subheader('Approved imports · Reddit / TradingQ&A / forums / YouTube')
    st.write('Import a CSV or JSON export obtained under the relevant platform permissions. Required columns: text, source_url, source_date. Optional: rating, record_id.')
    uploaded=st.file_uploader('Select approved data file',type=['csv','json'])
    imported_as=st.selectbox('Origin', ['reddit_approved', 'tradingqna_approved', 'youtube_approved', 'forum_approved', 'other_approved'])
    consent=st.checkbox('I confirm I have permission to process this export for the stated research use.')
    if st.button('Import evidence',disabled=not is_admin or uploaded is None or not consent):
        try:
            fetched=read_import(uploaded.getvalue(),filename=uploaded.name,source=imported_as)
            old=len(st.session_state.records)
            st.session_state.records=dedupe(st.session_state.records+fetched)
            st.success(f'Accepted {len(st.session_state.records)-old} new records; invalid or duplicate rows were skipped.')
        except Exception:st.error('Import could not be parsed. Check source URLs, CSV/JSON format and permission.')
    with st.expander('Pilot samples (manually sourced from public app pages; not an automated crawl)'):
        st.write('These two short published excerpts let you test the import and relevance-filtering workflow. They are not a representative dataset.')
        if st.button('Load the two sourced pilot excerpts',disabled=not is_admin):
            with (Path(__file__).resolve().parent / 'data' / 'pilot_sources.json').open(encoding='utf-8') as fh: examples=json.load(fh)
            out=read_import(json.dumps(examples),filename='pilot_sources.json',source='manual_public_excerpts')
            st.session_state.records=dedupe(st.session_state.records+out)
            st.success('Pilot excerpts loaded.')
    if st.session_state.records:
        st.dataframe(pd.DataFrame(st.session_state.records)[['record_id','source','source_date','rating','text','source_url']],width='stretch',hide_index=True)
        st.download_button('Download anonymized source records (CSV)',to_csv_bytes(st.session_state.records),'groww_source_records.csv','text/csv')


with analyze:
    st.subheader('OpenRouter · Structured research extraction')
    st.write('AI outputs are proposals, not ground truth. Human-review any uncertain labels.')
    candidates, excluded = prefilter_records(st.session_state.records)
    st.caption(f'SIP-keyword candidates: {len(candidates)} of {len(st.session_state.records)}; other records: {len(excluded)}. This is only a filter, not a verified SIP count.')
    bypass = st.checkbox('Include records without SIP keywords (exploratory; extra cost)',value=False)
    pool = st.session_state.records if bypass else candidates
    analyzed_ids = {a['record_id'] for a in st.session_state.analysis}
    queue = [r for r in pool if r['record_id'] not in analyzed_ids]
    retry_ids = {a['record_id'] for a in st.session_state.analysis if is_retryable_abstention(a)}
    st.caption(f'{len(queue)} new records awaiting analysis; {len(retry_ids)} retryable abstentions.')
    if st.button('Retry abstained API requests',disabled=not is_admin or not retry_ids):
        st.session_state.analysis = [
            a for a in st.session_state.analysis if a['record_id'] not in retry_ids
        ]
        st.success(f'Queued {len(retry_ids)} transient failures for another attempt.')
        st.rerun()
    per_run = st.slider('Maximum requests per run',1,10,3)
    cap = 30
    remaining = max(0, cap - st.session_state.api_calls)
    st.caption(f'API request budget for this session: {remaining} / {cap} remaining. This is a session cap, not a global spending limit.')
    if st.button('Analyze next batch with OpenRouter',
        disabled=not (is_admin and api_key and queue and remaining > 0)):
        count=min(per_run,len(queue),remaining)
        progress=st.progress(0)
        status=st.empty()
        new=[]
        with st.spinner('Classifying reviews...'):
            for index, item in enumerate(queue[:count]):
                status.caption(f'Processing {index+1} of {count} source items')
                st.session_state.api_calls += 1
                new.extend(analyze_with_openrouter([item],api_key,model))
                progress.progress((index+1)/count)
        st.session_state.analysis.extend(new)
        status.caption(f'Completed {count} API requests; review abstentions before interpreting themes.')
        st.success('Batch complete. Download the analysis CSV to retain the results.')
    if not api_key:
        st.warning('OpenRouter key not configured.')
    if st.session_state.analysis:
        if len(st.session_state.gold) >= 20:
            st.dataframe(pd.DataFrame(st.session_state.analysis),hide_index=True,width='stretch')
        else:
            st.info('Blind labeling active: AI classifications remain hidden until 20 human labels are recorded.')
        if is_admin:
            st.download_button('Download OpenRouter classifications (CSV)',
                to_csv_bytes(st.session_state.analysis),'groww_openrouter_labels.csv','text/csv')

with evidence:
    st.subheader('Sourced opportunity signals')
    if not st.session_state.records:
        st.write('No source records loaded in this session. Administrator can restore a saved source CSV.')
    else:
        counts, missed = prefilter_records(st.session_state.records)
        st.metric('Unique collected records',len(st.session_state.records))
        st.metric('SIP keyword candidates (not verified)',len(counts))
        st.metric('No SIP keyword match',len(missed))
        ratings=pd.Series([str(x.get('rating') or 'unknown') for x in st.session_state.records]).value_counts()
        st.write('**Rating distribution of collected sample**')
        st.bar_chart(ratings)
        if len(st.session_state.gold) < 20:
            st.info('AI findings and theme charts are hidden until 20 blinded human labels are saved.')
        else:
            stats=summary(st.session_state.records,st.session_state.analysis)
            st.metric('Accepted, unflagged SIP-relevant labels',stats['sip_relevant'])
            st.write('**Collection coverage by source**')
            st.bar_chart(pd.Series(stats['source_counts']))
            if stats['source_theme_counts']:
                rows=[{'source':src,'theme':theme,'count':number}
                    for src,items in stats['source_theme_counts'].items()
                    for theme,number in items.items()]
                st.write('**Theme comparison across sources**')
                st.dataframe(pd.DataFrame(rows).pivot_table(index='source',columns='theme',values='count',fill_value=0),width='stretch')
            if stats['theme_counts']:
                st.bar_chart(pd.Series(stats['theme_counts']))
            by_id={x['record_id']:x for x in st.session_state.analysis}
            accepted=[
                {'theme':by_id[r['record_id']]['theme'],
                 'exact_quote':by_id[r['record_id']].get('evidence_excerpt',''),
                 'source_url':r['source_url'],'source':r['source'],
                 'model':by_id[r['record_id']].get('model_used','')}
                for r in st.session_state.records if r['record_id'] in by_id
                and by_id[r['record_id']].get('relevance')=='sip_relevant'
                and not by_id[r['record_id']].get('needs_human_review',True)
                and float(by_id[r['record_id']].get('confidence',0) or 0) >= 0.70
                and by_id[r['record_id']].get('evidence_excerpt')]
            if accepted:
                st.subheader('Exact source excerpts supporting selected themes')
                st.dataframe(pd.DataFrame(accepted),hide_index=True,width='stretch')
            st.download_button('Download collection coverage (JSON)',
                json.dumps(stats,indent=2),'collection_coverage.json','application/json')
        st.warning('This is a convenience sample, not Groww retention data. First-time investor status is rarely observed directly.')

with gold:
    st.subheader('Golden set: manual review')
    st.write('Manually label approximately 20 **distinct source items** and compare with the AI output. Record 2–3 AI corrections in the final Evidence Log.')
    if not st.session_state.records:st.info('Collect/import reviews first.')
    else:
        records=st.session_state.records
        # Stable, source-interleaved order avoids selecting only the earliest reviews.
        source_groups={}
        for r in records:
            source_groups.setdefault(r['source'],[]).append(r)
        for group in source_groups.values():
            group.sort(key=lambda r: hashlib.sha256(('groww-sample-2026:'+r['record_id']).encode()).hexdigest())
        ordered=[]
        while any(source_groups.values()):
            for src in sorted(source_groups):
                if source_groups[src]:
                    ordered.append(source_groups[src].pop(0))
        opts={r['record_id']:f"{r['record_id']} · {r['source']} · {r['text'][:90]}" for r in ordered}
        rid=st.selectbox('Source record to label',list(opts),format_func=lambda x:opts[x])
        source=next(r for r in records if r['record_id']==rid)
        st.write('**Original excerpt**:',source['text'])
        st.write('Source:',source['source_url'])
        old=st.session_state.gold.get(rid,{})
        with st.form('gold_form'):
            rel=st.selectbox('SIP relevance',RELEVANCE,index=RELEVANCE.index(old.get('relevance','uncertain')))
            theme=st.selectbox('Primary theme',THEMES,index=THEMES.index(old.get('theme','other')))
            behavior=st.selectbox('Observed behavior',BEHAVIORS,index=BEHAVIORS.index(old.get('sip_behavior','unknown')))
            note=st.text_area('Human reasoning / correction',value=old.get('note',''))
            save=st.form_submit_button('Save manual label',disabled=not is_admin)
        if save:
            st.session_state.gold[rid]={'record_id':rid,'relevance':rel,'theme':theme,'sip_behavior':behavior,'note':privacy_clean(note)}
            st.success('Saved for this session. Download labels for persistence.')
        gold_rows=list(st.session_state.gold.values())
        st.metric('Manual items labelled',len(gold_rows),delta=f'{max(0,20-len(gold_rows))} remaining toward 20')
        if gold_rows:
            st.download_button('Download human gold labels (CSV)',to_csv_bytes(gold_rows),'groww_golden_set.csv','text/csv')
            evaluation=eval_gold(gold_rows,st.session_state.analysis) if len(gold_rows)>=20 else None
            if evaluation:
                st.write('**AI vs human evaluation (small sample)**')
                st.json(evaluation)
            else:
                st.info('Complete 20 human labels before viewing the AI evaluation.')
            combined=[]
            model_by_id={x['record_id']:x for x in st.session_state.analysis} if len(gold_rows)>=20 else {}
            record_by_id={x['record_id']:x for x in st.session_state.records}
            for human in gold_rows:
                original=record_by_id.get(human['record_id'],{})
                ai=model_by_id.get(human['record_id'],{})
                combined.append({'record_id':human['record_id'],'source':original.get('source'),
                    'source_url':original.get('source_url'),'date':original.get('source_date'),
                    'text':original.get('text'),'human_relevance':human.get('relevance'),
                    'ai_relevance':ai.get('relevance'),'human_theme':human.get('theme'),
                    'ai_theme':ai.get('theme'),'human_behavior':human.get('sip_behavior'),
                    'ai_behavior':ai.get('sip_behavior'),'human_correction':human.get('note'),
                    'ai_abstained':not bool(ai),'ai_review_reason':ai.get('review_reason')})
            st.download_button('Download joined Evidence Log (CSV)',to_csv_bytes(combined),'groww_ai_evidence_log.csv','text/csv')
            if len(gold_rows)<20:st.warning('Interim evaluation only. Approximately 20 manually labelled items required for assignment.')
        st.write('**Important:** Missing model labels count as mismatches. The first 20 manual labels are chosen without model output visible.')

st.divider()
st.caption('Research prototype · No automatic Reddit scraping · No financial recommendations · Save exports before closing your session. OpenRouter may route data to third-party models; do not submit restricted or personal text without provider permission.')
