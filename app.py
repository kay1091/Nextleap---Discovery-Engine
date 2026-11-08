"""Launch with: streamlit run app.py"""
import json
import os
import pandas as pd
import streamlit as st
from pipeline import (apple_feed, play_apify, youtube_comments, read_import, dedupe,
    analyze_with_grok, eval_gold, summary, to_csv_bytes, THEMES, BEHAVIORS, RELEVANCE)

st.set_page_config(page_title='Groww SIP | AI Discovery Engine',page_icon='🔎',layout='wide')
st.title('Groww SIP · AI Discovery Engine')
st.caption('Research tool · Public voice-of-customer evidence · Grok-supported classification · Not investment advice')
st.info('Research data ≠ Groww cohort analytics. Public reviews cannot establish actual 12-month SIP retention or investor status unless stated.')

for key,default in [('records',[]),('analysis',[]),('gold',{}),('errors',[])]:
    if key not in st.session_state: st.session_state[key]=default

with st.sidebar:
    st.header('Settings')
    api_key=os.environ.get('XAI_API_KEY','') or st.text_input('xAI API key (session only)',type='password')
    apify=os.environ.get('APIFY_TOKEN','') or st.text_input('Apify token (optional)',type='password')
    youtube_key=os.environ.get('YOUTUBE_API_KEY','') or st.text_input('YouTube API key (optional)',type='password')
    model=st.text_input('Grok model',value=os.getenv('XAI_MODEL','grok-4.7'))
    st.caption('Set secrets as environment variables on deployment; never commit API tokens.')
    st.metric('Collected unique records',len(st.session_state.records))
    st.metric('Grok classifications',len(st.session_state.analysis))
    st.metric('Human gold labels',len(st.session_state.gold))
    st.divider()
    st.markdown('**Compliance**: Reddit/forum inputs must be separately authorized. This app does not bypass login, rate limits, or site restrictions.')

collect, analyze, evidence, gold = st.tabs(['1 · Collect', '2 · Analyze', '3 · Evidence & themes', '4 · Human evaluation'])

with collect:
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Apple India public reviews')
        pages=st.slider('Recent pages (up to 10)',min_value=1,max_value=5,value=1)
        if st.button('Fetch Apple reviews'):
            try:
                with st.spinner('Collecting limited public feed...'):
                    fetched=apple_feed(pages=pages)
                before=len(st.session_state.records)
                st.session_state.records=dedupe(st.session_state.records+fetched)
                st.success(f'Fetched {len(fetched)}; added {len(st.session_state.records)-before} unique records.')
            except Exception as exc:st.error(f'Apple collection unavailable: {exc}')
        st.caption('Public RSS provides a limited recent window, not every historical review.')
    with c2:
        st.subheader('Google Play via Apify')
        max_reviews=st.slider('Maximum reviews',50,500,100,50)
        accepted=st.checkbox('I have reviewed the source/provider terms and accept provider charges.')
        if st.button('Fetch Play reviews',disabled=not(apify and accepted)):
            try:
                with st.spinner('Fetching Play reviews through third-party connector...'):
                    fetched=play_apify(apify,max_reviews=max_reviews)
                before=len(st.session_state.records)
                st.session_state.records=dedupe(st.session_state.records+fetched)
                st.success(f'Fetched {len(fetched)}; added {len(st.session_state.records)-before} unique records.')
            except Exception as exc:st.error(f'Google Play collection unavailable: {exc}')
        st.caption('Third-party, non-official collector; not guaranteed complete. No direct developer reviews API access to Groww.')
    st.divider()
    st.subheader('YouTube comments (official API)')
    st.write('Select a public Indian SIP/personal-finance video manually. The official API fetches recent top-level comments; not all replies.')
    video_id=st.text_input('YouTube video ID (11 characters)')
    ypages=st.slider('YouTube pages',1,3,1)
    if st.button('Fetch YouTube comments',disabled=not(youtube_key and video_id.strip())):
        try:
            out=youtube_comments(youtube_key,video_id.strip(),pages=ypages)
            old=len(st.session_state.records)
            st.session_state.records=dedupe(st.session_state.records+out)
            st.success(f'Fetched {len(out)}; added {len(st.session_state.records)-old} unique comments.')
        except Exception as exc:st.error(f'YouTube collection unavailable: {exc}')
    st.divider()
    st.subheader('Approved imports · Reddit / TradingQ&A / forums / YouTube')
    st.write('Import a CSV or JSON export obtained under the relevant platform permissions. Required columns: text, source_url, source_date. Optional: rating, record_id.')
    uploaded=st.file_uploader('Select approved data file',type=['csv','json'])
    imported_as=st.selectbox('Origin', ['reddit_approved', 'tradingqna_approved', 'youtube_approved', 'forum_approved', 'other_approved'])
    consent=st.checkbox('I confirm I have permission to process this export for the stated research use.')
    if st.button('Import evidence',disabled=uploaded is None or not consent):
        try:
            fetched=read_import(uploaded.getvalue(),filename=uploaded.name,source=imported_as)
            old=len(st.session_state.records)
            st.session_state.records=dedupe(st.session_state.records+fetched)
            st.success(f'Accepted {len(st.session_state.records)-old} new rows with links; missing-URL rows were skipped.')
        except Exception as exc:st.error(str(exc))
    with st.expander('Pilot samples (manually sourced from public app pages; not an automated crawl)'):
        st.write('These two short published excerpts let you test the import and relevance-filtering workflow. They are not a representative dataset.')
        if st.button('Load the two sourced pilot excerpts'):
            with open('data/pilot_sources.json',encoding='utf-8') as fh: examples=json.load(fh)
            out=read_import(json.dumps(examples),filename='pilot_sources.json',source='manual_public_excerpts')
            st.session_state.records=dedupe(st.session_state.records+out)
            st.success('Pilot excerpts loaded.')
    if st.session_state.records:
        st.dataframe(pd.DataFrame(st.session_state.records)[['record_id','source','source_date','rating','text','source_url']],use_container_width=True,hide_index=True)
        st.download_button('Download anonymized source records (CSV)',to_csv_bytes(st.session_state.records),'groww_source_records.csv','text/csv')

with analyze:
    st.subheader('Grok · Structured research extraction')
    st.write('The bot classifies records into evidence-backed themes. Missing information remains **unknown**. It never treats stock/F&O complaints as SIP discontinuation without direct evidence.')
    per_run=st.slider('Maximum records in this run (API calls / possible cost)',1,40,10)
    analyzed_ids={a['record_id'] for a in st.session_state.analysis}
    queue=[r for r in st.session_state.records if r['record_id'] not in analyzed_ids]
    st.caption(f'{len(queue)} records awaiting Grok analysis. One API request per record.')
    if st.button('Analyze next batch with Grok',disabled=not api_key or not queue):
        with st.spinner('Analyzing public reviews through xAI API...'):
            new=analyze_with_grok(queue[:per_run],api_key,model)
        st.session_state.analysis+=new
        st.success(f'Processed {len(new)} items. Review low-confidence/abstained outputs before using findings.')
    if not api_key:st.warning('No xAI API key configured. Source collection, imports and manual evaluation work, but Grok analysis is unavailable.')
    if st.session_state.analysis:
        st.dataframe(pd.DataFrame(st.session_state.analysis),hide_index=True,use_container_width=True)
        st.download_button('Download Grok classifications (CSV)',to_csv_bytes(st.session_state.analysis),'groww_grok_labels.csv','text/csv')

with evidence:
    st.subheader('Sourced opportunity signals')
    if not st.session_state.records: st.write('No source records loaded yet.')
    else:
        s=summary(st.session_state.records,st.session_state.analysis)
        a,b,c=st.columns(3)
        a.metric('Unique source records',s['records'])
        b.metric('Grok-labelled SIP-relevant',s['sip_relevant'])
        c.metric('Sources represented',len(s['source_counts']))
        st.write('**Collection coverage** — these are sample counts, not Groww prevalence:')
        st.bar_chart(pd.Series(s['source_counts']))
        if s['theme_counts']:
            st.write('**Observed themes within Grok-labelled SIP records**')
            st.bar_chart(pd.Series(s['theme_counts']))
        else:st.info('No SIP-relevant classifications yet; avoid inferring thematic prevalence.')
        st.warning('App reviews tend to overrepresent UX and support issues. Forums may overrepresent highly involved investors. Segments and 12-month cohorts cannot be inferred from counts.')
        st.download_button('Download collection metadata (JSON)',json.dumps(s,indent=2),'collection_coverage.json','application/json')

with gold:
    st.subheader('Golden set: manual review')
    st.write('Manually label approximately 20 **distinct source items** and compare with the Grok output. Record 2–3 AI corrections in the final Evidence Log.')
    if not st.session_state.records:st.info('Collect/import reviews first.')
    else:
        records=st.session_state.records
        opts={r['record_id']:f"{r['record_id']} · {r['source']} · {r['text'][:90]}" for r in records}
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
            save=st.form_submit_button('Save manual label')
        if save:
            st.session_state.gold[rid]={'record_id':rid,'relevance':rel,'theme':theme,'sip_behavior':behavior,'note':note}
            st.success('Saved for this session. Download labels for persistence.')
        gold_rows=list(st.session_state.gold.values())
        st.metric('Manual items labelled',len(gold_rows),delta=f'{max(0,20-len(gold_rows))} remaining toward 20')
        if gold_rows:
            st.download_button('Download human gold labels (CSV)',to_csv_bytes(gold_rows),'groww_golden_set.csv','text/csv')
            evaluation=eval_gold(gold_rows,st.session_state.analysis)
            st.write('**AI vs human exact-match evaluation**')
            st.json(evaluation)
            combined=[]
            model_by_id={x['record_id']:x for x in st.session_state.analysis}
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
        st.write('**Important:** Missing model labels are counted as mismatches; do not report agreement until the model has analyzed the gold records.')

st.divider()
st.caption('Prototype v0.1 · No automatic Reddit scraping · No financial recommendations · Download results before closing your session.')
