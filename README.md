# Groww SIP — AI Discovery Engine (OpenRouter-only)

A student product-discovery research prototype. This is **not** Groww cohort analytics, financial advice, a validated claim about SIP retention, or a representative survey of investors.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

In Streamlit Community Cloud, use **App → Settings → Secrets**:

```toml
OPENROUTER_API_KEY = "your_real_key"
OPENROUTER_MODEL = "openrouter/free"
# Optional for public apps: restrict API usage
DISCOVERY_ADMIN_PASSWORD = "a_strong_private_password"
```

Only the OpenRouter API key is needed for AI calls. The optional admin password is **not** a second API provider. Do not commit API keys to GitHub or enter them into public text fields. `openrouter/free` routes among different free models and may have rate limits, variable behavior or reasoning-only empty responses. For reproducible evaluation, choose a fixed available OpenRouter model and record its actual ID with the output. The app safely abstains if the API fails or returns invalid JSON; it does not manufacture classifications.

## Streamlit Community Cloud deployment

1. Make a new **public** GitHub repository (separate from the SIP Performance Explainer).
2. Upload **the contents of this folder** (`app.py`, `pipeline.py`, `requirements.txt`, `data/`, `tests/`, README), not only the ZIP. Do not upload `.env` or `.streamlit/secrets.toml` containing credentials.
3. In Streamlit Community Cloud, choose your repository, its default branch (normally `main`) and main file `app.py`.
4. Deploy and add `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` under Secrets. Optionally add `DISCOVERY_ADMIN_PASSWORD` to protect paid AI calls.
5. Load the two demonstration excerpts under **Collect**, then use **Analyze** with your key. If the app shows `abstained`, do not report that as a successful AI label.
6. Use **Human evaluation** to manually label real, authorized source records and export joined evaluation evidence.

**Public access and costs:** If you deploy with an unrestricted key and no admin password, any visitor may trigger model calls and consume your available credits/quota. To restrict calls, set `DISCOVERY_ADMIN_PASSWORD` and keep it private; reviewers can still view the research interface, load samples and review existing imported data, but cannot run live model calls without the password. Streamlit's session state is not durable or shared across visitors.

## Features

- **Collect:** import authorized CSV/JSON excerpts with `text`, `source_url`, and `source_date`; two demonstration examples included.
- **Analyze:** send selected excerpts through OpenRouter for structured classification. AI output is checked against allowed label lists and source text.
- **Evidence & themes:** counts and sample theme distributions (not population estimates).
- **Human evaluation:** record independently human-labelled relevance, themes and observed behavior; inspect exact-match comparison and export CSV files.

## Source policy

No live Apify, Google Play scraping, YouTube Data API, Reddit crawler, or xAI/Grok integration. The only AI API provider is OpenRouter. Exports from these sources may be imported *only when the user has the appropriate processing and redistribution permissions*. Automated collection was intentionally removed to avoid claiming source rights or permissions we cannot verify. If data contain personal identifiers, remove them before upload; the pipeline only redacts common patterns and is not sufficient for full anonymization. The two bundled excerpts are illustrative examples and **not** validated research evidence.

## Limits and evaluation

- SIP relevance and first-time investor status cannot be inferred from a generic review, a rating or a download count.
- The AI must include an exact short quote present in the supplied excerpt; unsupported claims should be marked for human review.
- A classification `abstained` due to API failure or empty output must not count as a verified label.
- Human golden set: label approximately 20 distinct items independently, include corrected cases, and report agreement/missing outputs honestly.
- Findings describe this collected/authorized sample only, not the fraction of Groww users who stop SIPs or actual 12-month retention.
- Downloads are generated per browser session and need to be saved separately as evidence.

## Offline checks

```bash
python -m compileall -q app.py pipeline.py tests
python -m pytest -q tests
```

`pytest` is optional for developers and is not needed to run the Streamlit app.

## Reference

OpenRouter Chat Completions API: https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request
