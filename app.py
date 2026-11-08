"""Run with: streamlit run app.py"""
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from pipeline import (
    BEHAVIORS,
    RELEVANCE,
    THEMES,
    analyze_with_openrouter,
    dedupe,
    eval_gold,
    read_import,
    summary,
    to_csv_bytes,
)

st.set_page_config(
    page_title="Groww SIP | AI Discovery Engine",
    page_icon="🔎",
    layout="wide",
)
st.title("Groww SIP · AI Discovery Engine")
st.caption("Research prototype · OpenRouter-only AI analysis · Educational product discovery")
st.info(
    "Public feedback is exploratory, not Groww cohort analytics. "
    "It cannot establish actual 12-month SIP retention or first-time investor status unless explicitly reported."
)


def setting(name, default=""):
    """Read secrets without requiring a local Streamlit secrets file."""
    try:
        return st.secrets.get(name, os.environ.get(name, default))
    except (FileNotFoundError, OSError, KeyError):
        return os.environ.get(name, default)


api_key = str(setting("OPENROUTER_API_KEY", "") or "").strip()
model = str(setting("OPENROUTER_MODEL", "openrouter/free") or "openrouter/free").strip()
admin_password = str(setting("DISCOVERY_ADMIN_PASSWORD", "") or "")

for key, initial in (
    ("records", []),
    ("analysis", []),
    ("gold", {}),
    ("attempted_count", 0),
):
    if key not in st.session_state:
        st.session_state[key] = initial

with st.sidebar:
    st.header("AI settings")
    st.write("**Provider:** OpenRouter")
    st.caption(f"**Configured model:** `{model}`")
    if api_key:
        st.success("OpenRouter key configured")
    else:
        st.warning("OpenRouter key missing. Add it in Streamlit App Settings → Secrets.")

    authorized = True
    if admin_password:
        password_input = st.text_input("Research administrator password", type="password")
        authorized = password_input == admin_password
        st.caption("AI requests require administrator access to help control API usage.")

    st.metric("Unique source records", len(st.session_state.records))
    classified = sum(x.get("analysis_status") == "classified" for x in st.session_state.analysis)
    st.metric("AI-classified records", classified)
    st.metric("Human-reviewed items", len(st.session_state.gold))
    st.divider()
    st.caption(
        "Only approved/permissioned imports and two pilot excerpts are supported. "
        "No scraping, Apify, YouTube API, or other AI-provider credentials."
    )

collect, analyze, evidence, gold = st.tabs(
    ["1 · Collect", "2 · Analyze", "3 · Evidence & themes", "4 · Human evaluation"]
)

with collect:
    st.subheader("Import authorized source-linked research")
    st.write(
        "Upload a CSV or JSON dataset collected with permission. "
        "Required fields: `text`, `source_url`, `source_date`. "
        "Optional: `rating`, `record_id`. Invalid source links are skipped."
    )
    uploaded = st.file_uploader("Authorized CSV or JSON", type=["csv", "json"])
    imported_as = st.selectbox(
        "Source category",
        ["reddit_approved", "youtube_approved", "play_approved",
         "forum_approved", "apple_approved", "other_approved"],
    )
    consent = st.checkbox(
        "I have permission to process and send these excerpts to the selected AI provider, "
        "and have checked the records for personal information."
    )
    if st.button("Import evidence", disabled=uploaded is None or not consent):
        try:
            incoming = read_import(uploaded.getvalue(), filename=uploaded.name, source=imported_as)
            before = len(st.session_state.records)
            st.session_state.records = dedupe(st.session_state.records + incoming)
            st.success(f"Imported {len(st.session_state.records) - before} new source-linked records.")
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            st.error(f"Import failed: {type(exc).__name__}. Verify the CSV/JSON columns.")

    with st.expander("Pilot examples — demonstrate the workflow without uploads"):
        st.write(
            "These two short prepackaged excerpts are **demonstration data only**, "
            "not a representative or independently verified research dataset. "
            "Review their source links and rights before publishing or redistributing."
        )
        if st.button("Load two pilot excerpts"):
            example_file = Path(__file__).parent / "data" / "pilot_sources.json"
            sample = json.loads(example_file.read_text(encoding="utf-8"))
            incoming = read_import(
                json.dumps(sample),
                filename="pilot_sources.json",
                source="manual_pilot_excerpts",
            )
            st.session_state.records = dedupe(st.session_state.records + incoming)
            st.success(f"Pilot loaded. {len(st.session_state.records)} total unique records.")

    if st.session_state.records:
        view = pd.DataFrame(st.session_state.records)
        columns = [
            col for col in ("record_id", "source", "source_date", "rating", "text", "source_url")
            if col in view.columns
        ]
        st.dataframe(view[columns], use_container_width=True, hide_index=True)
        st.download_button(
            "Download source records CSV",
            to_csv_bytes(st.session_state.records),
            file_name="discovery_source_records.csv",
            mime="text/csv",
        )

with analyze:
    st.subheader("OpenRouter · Evidence-backed theme extraction")
    st.write(
        "The AI labels SIP relevance, possible user behavior, and themes. "
        "Unsupported claims remain uncertain; quotations must appear in the supplied text."
    )
    batch = st.slider("Records to analyze (one API request per record)", 1, 5, 2)
    completed_ids = {
        x["record_id"] for x in st.session_state.analysis
        if x.get("analysis_status") == "classified"
    }
    queue = [r for r in st.session_state.records if r["record_id"] not in completed_ids]
    st.caption(f"{len(queue)} records available for analysis · Free routing can change model between calls.")

    allowed = bool(api_key and authorized and queue)
    if st.button("Analyze next batch with OpenRouter", disabled=not allowed):
        with st.spinner("Classifying the selected source excerpts..."):
            new = analyze_with_openrouter(queue[:batch], api_key, model)
        by_id = {r["record_id"]: r for r in st.session_state.analysis}
        by_id.update({r["record_id"]: r for r in new})
        st.session_state.analysis = list(by_id.values())
        success = sum(r.get("analysis_status") == "classified" for r in new)
        st.success(f"{success} classified; {len(new) - success} abstained or require retry.")
        if success < len(new):
            st.warning("Some responses were unavailable or invalid. Review the per-record reason below.")
    if not api_key:
        st.warning("OpenRouter analysis is offline until OPENROUTER_API_KEY is set in Secrets.")
    elif not authorized:
        st.info("Enter the research administrator password to enable paid API requests.")

    if st.session_state.analysis:
        st.dataframe(pd.DataFrame(st.session_state.analysis), hide_index=True, use_container_width=True)
        st.download_button(
            "Download OpenRouter classification CSV",
            to_csv_bytes(st.session_state.analysis),
            file_name="discovery_openrouter_labels.csv",
            mime="text/csv",
        )

with evidence:
    st.subheader("Traceable opportunity signals")
    if not st.session_state.records:
        st.info("Load pilot examples or import an authorized dataset first.")
    else:
        metrics = summary(st.session_state.records, st.session_state.analysis)
        c1, c2, c3 = st.columns(3)
        c1.metric("Unique source records", metrics["records"])
        c2.metric("AI-labelled SIP-relevant", metrics["sip_relevant"])
        c3.metric("Source categories", len(metrics["source_counts"]))
        st.write("**Source coverage in this sample**")
        st.bar_chart(pd.Series(metrics["source_counts"]))
        if metrics["theme_counts"]:
            st.write("**Themes in AI-labelled SIP-relevant excerpts**")
            st.bar_chart(pd.Series(metrics["theme_counts"]))
        else:
            st.info("No validated SIP-relevant classifications yet; do not infer prevalence.")
        st.warning(
            "Collected sample counts do not represent Groww's investors, "
            "retention or real population prevalence. Human review is required."
        )
        st.download_button(
            "Download sample-coverage metadata",
            json.dumps(metrics, indent=2),
            file_name="discovery_coverage.json",
            mime="application/json",
        )

with gold:
    st.subheader("Human evaluation · Gold labels")
    st.write(
        "Manually label around 20 distinct source excerpts **independently of AI labels**, "
        "then compare SIP relevance, theme and behavior. Include corrections in the Evidence Log."
    )
    if not st.session_state.records:
        st.info("Import source records in the Collect tab first.")
    else:
        records = st.session_state.records
        options = {
            r["record_id"]: f"{r['record_id']} · {r['source']} · {r['text'][:80]}"
            for r in records
        }
        rid = st.selectbox("Source excerpt to label", list(options), format_func=lambda k: options[k])
        selected = next(r for r in records if r["record_id"] == rid)
        st.write("**Original excerpt:**", selected["text"])
        st.write("**Source link:**", selected["source_url"])
        previous = st.session_state.gold.get(rid, {})
        with st.form("human_label"):
            relevance = st.selectbox(
                "SIP relevance", RELEVANCE,
                index=RELEVANCE.index(previous.get("relevance", "uncertain")),
            )
            theme = st.selectbox(
                "Primary theme", THEMES,
                index=THEMES.index(previous.get("theme", "other")),
            )
            behavior = st.selectbox(
                "Observed SIP behavior", BEHAVIORS,
                index=BEHAVIORS.index(previous.get("sip_behavior", "unknown")),
            )
            note = st.text_area("Reason or correction", value=previous.get("note", ""))
            submitted = st.form_submit_button("Save manual label")
        if submitted:
            st.session_state.gold[rid] = {
                "record_id": rid,
                "relevance": relevance,
                "theme": theme,
                "sip_behavior": behavior,
                "note": note,
            }
            st.success("Saved for this session. Download the labels for persistence.")

        human_rows = list(st.session_state.gold.values())
        st.metric("Manually labelled excerpts", len(human_rows))
        if human_rows:
            st.download_button(
                "Download human labels CSV",
                to_csv_bytes(human_rows),
                file_name="discovery_human_gold.csv",
                mime="text/csv",
            )
            valid_ai = [
                x for x in st.session_state.analysis
                if x.get("analysis_status") == "classified"
            ]
            comparison = eval_gold(human_rows, valid_ai)
            st.write("**Human versus AI exact-match evaluation**")
            st.json(comparison)
            model_by_id = {x["record_id"]: x for x in st.session_state.analysis}
            source_by_id = {x["record_id"]: x for x in st.session_state.records}
            joined = []
            for human in human_rows:
                original = source_by_id.get(human["record_id"], {})
                ai = model_by_id.get(human["record_id"], {})
                joined.append({
                    "record_id": human["record_id"],
                    "source_url": original.get("source_url", ""),
                    "source_date": original.get("source_date", ""),
                    "human_relevance": human["relevance"],
                    "ai_relevance": ai.get("relevance", "MISSING"),
                    "human_theme": human["theme"],
                    "ai_theme": ai.get("theme", "MISSING"),
                    "human_behavior": human["sip_behavior"],
                    "ai_behavior": ai.get("sip_behavior", "MISSING"),
                    "review_note": human.get("note", ""),
                    "ai_status": ai.get("analysis_status", "MISSING"),
                })
            st.download_button(
                "Download joined evaluation CSV",
                to_csv_bytes(joined),
                file_name="discovery_evaluation_joined.csv",
                mime="text/csv",
            )
            if len(human_rows) < 20:
                st.warning("Small/interim gold set. Do not report this as a complete 20-item evaluation.")

st.divider()
st.caption(
    "Academic prototype · One AI provider: OpenRouter · No financial advice · "
    "No auto-scraping · Session data is temporary; download results before closing."
)
