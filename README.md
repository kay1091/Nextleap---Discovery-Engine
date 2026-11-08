# Groww SIP — OpenRouter AI Discovery Engine (v0.1)

**Purpose**: Extract, trace and analyze publicly available feedback that may reveal why first-time Indian mutual-fund SIP investors continue, pause or stop. Designed for the Product Management assignment due **9 Nov 2026**. It is a research tool, not investment advice.

## Run locally

1. Install Python 3.10+.
2. In this folder run `python -m pip install -r requirements.txt`.
3. Set `OPENROUTER_API_KEY` in your environment (see `.env.example`); optionally set `APIFY_TOKEN` or `YOUTUBE_API_KEY`.
4. Run `streamlit run app.py`.
5. Use the **Collect** tab to fetch limited Apple India public RSS reviews or authorized imports. Load the two **manually sourced pilot excerpts** to test the data interface offline. If your Apify plan/source terms permit, configure and trigger the optional Google Play connector.
6. Use **Analyze** to send selected source records through the OpenRouter API (one request per record; costs and rate limits depend on the selected model).
7. Under **Human evaluation**, label ~20 items without looking at AI output first; compare exact-match accuracy and log 2–3 corrections. Download the outputs; hosted Streamlit session state isn't durable.
8. Open **Evidence & themes** to compare tagged feedback by source; avoid interpreting these percentages as Groww's user retention rates.

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

The included `data/pilot_sources.json` contains two short, **manually transcribed source excerpts** from publicly visible Groww app pages, **not crawler output**. They only test the record structure and relevance logic. Neither a live Apple fetch nor a live OpenRouter call has been executed by this package's author because runtime internet access and API credentials were unavailable at creation. See `tests/` for offline tests.

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
```

No xAI key is needed. The original optional Apify and YouTube API features remain available; supply
`APIFY_TOKEN` or `YOUTUBE_API_KEY` using the sidebar or supported environment variables only if
you choose to use those collectors. Never commit credentials.

This version preserves all four tabs and the collection/evaluation workflow from the supplied app.
Only xAI/Grok AI classification has been replaced with OpenRouter.

For a public deployment, remember that visitors may trigger API calls using the configured OpenRouter
key. Free-model limits are finite, and model/provider outputs may differ between runs.
Consider restricting paid actions before public sharing.
