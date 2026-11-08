# Groww SIP Retention - AI-powered Discovery Engine (Part 1)

Goal metric: % of first-time mutual-fund investors with an active SIP (>=1 successful instalment in the last 30 days) 12 months after their first SIP. Product chosen: **Groww** (store reviews also collected for ET Money, INDmoney, Kuvera, Paytm Money, Zerodha Coin as comparators). Constraints respected: no fund/stock recommendations, no fear/FOMO/urgency framing.

Everything here is derived from **public text**; it is directional, not Groww internal data. Read `AI_EVIDENCE_LOG.md` for what was validated and how, and `codebook.md` for the 40 codes.

## Layout
- `scripts/` numbered pipeline (below); `data/raw/` collected records (JSONL); `data/processed/` cleaned/coded CSVs, embeddings cache, eval files; `labels/` hand labels (train, holdout, precision audit, spam audit); `outputs/` tables (scorecard, funnel, segments, quote verification, `quotes.txt`, `canvas.tsx`); `charts/` 7 PNGs; `logs/` collection and run logs.

## Pipeline (run in order from this directory)
```
python3 -m venv --system-site-packages .venv && . .venv/bin/activate
pip install google-play-scraper yt-dlp youtube-comment-downloader scikit-learn matplotlib langdetect sentence-transformers requests pandas
python scripts/01a_collect_playstore.py        # Play Store: 6 apps x 2 sorts x 5 star levels
python scripts/01h_playstore_regional.py       # extra Play Store slice
python scripts/01c_collect_appstore.py         # App Store RSS
python scripts/01b_collect_reddit.py posts     # Reddit via Arctic Shift archive (slow); also: comments [subreddit]
python scripts/01d_youtube_find_videos.py && python scripts/01e_youtube_comments.py
python scripts/01f_discourse_forums.py         # TradingQ&A, ValuePickr
python scripts/01g_parse_x.py                  # parses X search-tool outputs saved in data/raw/x_tool_outputs/
python scripts/02_clean.py                     # dedupe, language, spam, relevance, journey_core
python scripts/03a_embed_cluster.py            # bottom-up themes (clusters_embedding.md, topics_nmf.md)
python scripts/03b_sample_for_coding.py        # samples for hand labelling (labels/ already included)
python scripts/04_train_eval.py                # coder training + blind-holdout metrics
python scripts/06a_code_corpus.py              # code all SIP-journey docs
python scripts/06b_segments_funnel.py          # stop language, stage, segments, involuntary/voluntary
python scripts/07c_audit_sample.py sample      # (label -> labels/audit_labels*.txt)  then: score
python scripts/07a_analysis.py                 # frequencies, scorecard, funnel, segments, charts
python scripts/08_verify_quotes.py             # every quote must exist verbatim in raw data
python scripts/09_validation_extras.py && python scripts/10_make_docs.py && python scripts/11_build_canvas.py
```
`07b_cands.py` browses quote candidates (`python scripts/07b_cands.py CODE|AREA|regex:... [n]`). Shared definitions: `codebook.py`, `areas.py`, `common.py`.

## Data coverage (final corpus)
| source | raw | unique | spam flagged | SIP/MF relevant | SIP-journey core |
|---|---|---|---|---|---|
| App Store | 5,500 | 4,292 | 136 | 1,212 | 229 |
| Google Play | 35,550 | 25,481 | 1,791 | 5,353 | 1,124 |
| Reddit | 19,021 | 18,400 | 861 | 15,228 | 14,310 |
| TradingQ&A | 5,872 | 5,068 | 163 | 2,567 | 1,015 |
| ValuePickr | 7,708 | 7,344 | 342 | 3,394 | 437 |
| X | 137 | 136 | 49 | 58 | 49 |
| YouTube | 41,600 | 36,577 | 2,875 | 8,531 | 1,897 |
| **Total** | 115,388 | 97,298 | 6,217 | 36,343 | 19,061 |

## What could not be collected
Reddit native JSON and PullPush blocked (used the Arctic Shift archive; stopped early - r/mutualfunds comments partial; several subreddits' comments/posts not collected); Quora blocked (403/Cloudflare); Google/DDG scraping blocked; Facebook/Instagram/WhatsApp not attempted; X only 137 posts; no Groww internal data. See `logs/`.

## Limitations (short)
Self-selected, negativity-biased public text; Reddit is 75% of the analysed set; single LLM annotator (no human second coder); coder precision moderate (micro-F1 ~0.44 on a 150-doc holdout scored three times); spam filter over-removes (precision ~39% on a 36-doc audit); Hinglish/vernacular under-coded; segment tags cover 2-12% of documents; stage evidence rests on explicit time cues only; no ground truth of 12-month retention. Details in `AI_EVIDENCE_LOG.md`.
