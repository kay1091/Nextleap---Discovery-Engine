# Groww SIP — OpenRouter AI Discovery Engine (v0.1)

**Purpose**: Extract, trace and analyze publicly available feedback that may reveal why first-time Indian mutual-fund SIP investors continue, pause or stop. Designed for the Product Management assignment due **9 Nov 2026**. It is a research tool, not investment advice.

## Run locally

1. Install Python 3.10+.
2. In this folder run `python -m pip install -r requirements.txt`.
3. Set `OPENROUTER_API_KEY` in your environment (see `.env.example`); optionally set `APIFY_TOKEN` or `YOUTUBE_API_KEY`.
4. Run `streamlit run app.py`.
5. Use the **Collect** tab to fetch limited Apple India public RSS reviews or authorized imports. Load the two **manually sourced pilot excerpts** to test the data interface offline. If your Apify plan/source terms permit, configure and trigger the optional Google Play connector.
6. Use **Analyze** to send selected source records through the OpenRouter API (one request per record; costs and rate limits depend on the selected model).
7. Set `DISCOVERY_ADMIN_PASSWORD` in Streamlit Secrets before deploying. Enter that passcode in the sidebar to enable collection, imports, human labeling and API requests. Without it, the app intentionally remains read-only.
8. Under **Human evaluation**, label ~20 source-stratified, seeded items before viewing AI labels. Compare confusion matrices, agreement and Cohen's kappa; log 2–3 genuine corrections. Export source, AI and human CSVs regularly. Use **Restore previous CSV exports** in the sidebar after a restart; restoration is manual, not a durable database.
9. Open **Evidence & themes** to compare accepted high-confidence themes by source, inspect source-linked quotes and compare rating distribution. Counts are from this collected sample, not Groww retention rates.

### Source coverage, restrictions and what is NOT provided

| Source | Collection method | Status / caveats |
|---|---|---|
| Groww Apple App Store (India) | Apple public review RSS; recent pages | Implemented, needs network connection at run time; feed is capped/limited |
| Groww Google Play (India) | Third-party Apify Actor (`webdatatools/google-play-reviews-scraper`) | Implemented optionally; verify the provider's collection method, Google terms, charges and availability yourself; not an official Google API |
| Reddit | Import only with appropriate research authorization | No Reddit crawler. As of May 2026 Reddit says academic research requires Reddit For Researchers program; no unauthenticated/bulk scraping |
| TradingQ&A / forums | Authorised source-linked CSV/JSON import | Not an indiscriminate site crawler; check license, robots, and terms |
| YouTube comments | Official YouTube Data API for selected video IDs; authorised export import | Implemented, needs API key and quota; top-level comments only by default |
| User interviews / survey | Anonymized authorized import | Keep separate from public reviews, do not include emails, PAN, account numbers |

**You cannot guarantee all historical reviews.** On-platform access limitations and terms apply. Source dates, language, region, sort order, missing pages and sample volumes must be recorded.

### How to interpret results

- The research engine cannot know whether a generic app reviewer is a first-time mutual-fund SIP investor unless they explicitly say so.
- Reports about F&O, share trading, IPOs or unrelated app usability must not be treated as SIP problems.
- Positive vs negative star ratings do not mean continued vs stopped SIP.
- Public-discussion frequencies describe *the collected sample* and not Groww's real retention or a representative distribution.
- Personal identifiers from reviews are intentionally not stored, and emails/phones/PAN are redacted where identifiable by pattern. Manually verify any remaining PII before sending to AI or sharing publicly.
- Reddit-derived text may have restrictions on onward redistribution and third-party AI processing. Check granted permissions before import and analysis.

### Validated sample and API status

The included `data/pilot_sources.json` contains two short, **manually transcribed source excerpts** from publicly visible Groww app pages, **not crawler output**. They only test the record structure and relevance logic. The repository now has offline regression tests for Apple review-link parsing (synthetic fixture based on the documented structure), API-error redaction, CSV restore and AI validation. A captured, live Apple payload is **not** yet included; live end-to-end validation and a verified OpenRouter smoke result remain pending. See `tests/` and GitHub Actions for automated checks.

### Evals and publication

The human golden set should consist of ~20 distinct records. Compare AI vs human: relevance, theme, and behavior; include mismatch examples and corrected decisions. Record how many were missing or uncertain. Human approval is required before writing product insights and only publish rights-compliant excerpts with source links. The app must be deployed separately; deployment is not confirmed by this package. For mentor testing, deploy to Streamlit Community Cloud or a supported host, configure secrets server-side, and restrict paid actions to an administrator (e.g. behind sign-in) before sharing any public link.

### Sources and docs

- OpenRouter: https://openrouter.ai/docs/quickstart
- Apple Groww: https://apps.apple.com/in/app/groww-stocks-mutual-fund-ipo/id1404871703
- Google Play Groww: https://play.google.com/store/apps/details?id=com.nextbillion.groww
- Google Play official developer review API (for apps with authorized developer account): https://developers.google.com/android-publisher/api-ref/rest/v3/reviews/list
- Apple public feed format used: https://itunes.apple.com/in/rss/customerreviews/page=1/id=1404871703/sortby=mostrecent/json
- Apify actor: https://apify.com/webdatatools/google-play-reviews-scraper
- Reddit policy (2026): https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data

## Research milestone sequence

1. Collect a bounded, traceable sample (e.g. recent Apple reviews + permitted Play reviews + authorised forum records), with balanced ratings and sources.
2. Deduplicate and filter SIP-relevant mentions. Record source and keyword denominators.
3. Use OpenRouter to extract behavioral claims, causes, unmet needs, certainty, explicit user-status, and exact supporting excerpts.
4. Validate 20 manual labels and correct 2–3 model errors.
5. Compare candidate opportunity areas across sources, alongside 5–6 real interviews, then select the problem and build the separate user-facing MVP.

## Deploy with Streamlit Community Cloud

Deploy `app.py` from the repository root on the `main` branch (or your actual default branch).
In App Settings > Secrets enter:

```toml
OPENROUTER_API_KEY = "your_actual_openrouter_key"
OPENROUTER_MODEL = "openrouter/free"
DISCOVERY_ADMIN_PASSWORD = "choose_a_strong_unique_passcode"
```

No xAI key is needed. The original optional Apify and YouTube API features remain available; supply
`APIFY_TOKEN` or `YOUTUBE_API_KEY` using the sidebar or supported environment variables only if
you choose to use those collectors. Never commit credentials.

This version preserves all four tabs and the collection/evaluation workflow from the supplied app.
Only xAI/Grok AI classification has been replaced with OpenRouter.

For a public deployment, remember that visitors may trigger API calls using the configured OpenRouter
key. Free-model limits are finite, and model/provider outputs may differ between runs.
Consider restricting paid actions before public sharing.


## Security and research-quality updates (8 November 2026)

- Privileged actions are locked until a server-side `DISCOVERY_ADMIN_PASSWORD` is set and provided through the sidebar. This is a basic demo passcode, **not** strong user authentication. Do not distribute the passcode with the public link.
- Each session has a maximum of 30 AI calls. **This is not a global rate limit**; keep the key restricted to a low-spend team budget and consider provider-side limits.
- Apple reviews use source links from the RSS entry. Missing per-review links are skipped rather than replaced with generic app URLs. Live feed shape must still be checked.
- Collector errors shown to visitors are generic or status-only; never display query strings, request headers, or API tokens. The Apify connector uses a Bearer header. YouTube's documented API still sends `key=` in its request but failure URLs are not displayed.
- Both successful AI labels and abstentions can be exported. Transient HTTP 429/5xx, timeout and empty-output rows can be removed from the completion queue with **Retry abstained API requests** and analyzed again.
- Data exists only in Streamlit session state. Export and manually restore the **source**, **analysis**, and **gold** CSVs after a reload; there is no server-side persistence database. CSV exports prefix formula-looking spreadsheet cells with an apostrophe, which can affect round-tripping of raw free-text values.
- A case-insensitive SIP keyword prefilter reduces unnecessary AI calls; the dashboard reports both included and unmatched source counts. This filter is not a substitute for relevance labeling and may miss genuine non-keyword cases.
- Manual labels are selected in a stable source-interleaved hashed order, with AI findings hidden until 20 human labels are saved. This is a source-stratified convenience sampler, not a representative randomized investor sample.
- Agreement, confusion matrices and Cohen's kappa are exploratory with n≈20 and should not be portrayed as representative model validity. The router `openrouter/free` may use multiple models; actual model identifiers are logged for new classifications where supplied by the API.
- AI theme summaries exclude low-confidence and human-review flagged entries. The `other` bucket and first-time-status uncertainty remain explicit limitations.
- Do not send restricted Reddit/forum records, financial account identifiers or personal data to a free model without checking third-party provider processing permissions; the app's redaction filters are incomplete by nature. Authorizing the import alone does **not** grant permission for external AI transmission.
- Apify actor input and data rights remain unverified, and Apple review collection may be restricted by platform rules. The administrator must review compliance independently before using live collectors.

### Running tests

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m compileall -q app.py pipeline.py tests
python -m pytest -q
```

### Live smoke test still required

1. Set the administrator passcode and OpenRouter key in Streamlit Secrets, then reboot.
2. Fetch one permitted Apple review page; confirm source links navigate to the corresponding review (not just the generic app page). If the collection is disallowed, skip it rather than bypassing access controls.
3. Load pilot examples, run one OpenRouter classification, record the actual model and validation outcome.
4. Label one source manually, export the three CSVs, reload, restore them and verify counts.
5. Test an artificial 429/mock response via offline tests and a real rate-limit event only if it occurs naturally. Do not manufacture evidence.
