"""Streamlit UI for the multi-agent market research app."""
import html
import json
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

from workflow import brief_to_markdown, run_workflow, suggestions

try:
    from pdf_export import make_pdf
except Exception:  # fpdf2 missing -> PDF button hidden, app still works
    make_pdf = None

st.set_page_config(page_title="Nepal Market Research Agent", page_icon="🔎", layout="wide")

HISTORY_FILE = Path(__file__).parent / "history.json"
EXAMPLES = ["Food delivery in Nepal", "Foodmandu", "Nepal Telecom", "Banking in Nepal", "Tesla"]
MODES = {"Auto (directory, then live web)": "auto", "Sample directory only": "sample", "Live web only": "live"}

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1100px;}
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}
[data-testid="stToolbar"], [data-testid="stAppDeployButton"] {display: none !important;}
div[data-baseweb="input"] {border-radius: 12px !important;}
div[data-baseweb="input"] input {font-size: 1rem; padding: 0.6rem 0.8rem;}
.stButton > button {border-radius: 12px !important; font-weight: 600;}
.hero {background: linear-gradient(135deg,#4f46e5 0%,#7c3aed 55%,#db2777 100%); color:#fff;
       border-radius:20px; padding:34px 36px; margin-bottom:18px;}
.hero h1 {margin:0 0 6px 0; font-size:2.1rem; color:#fff;}
.hero p {margin:0; opacity:.92; font-size:1.05rem;}
.card {border:1px solid rgba(128,128,128,.28); border-radius:14px; padding:14px 16px; margin-bottom:10px;
       background: rgba(128,128,128,.07);}
.summary {border-left:5px solid #4f46e5; background:rgba(79,70,229,.10); border-radius:10px;
          padding:16px 18px; font-size:1.05rem; line-height:1.55;}
.comp {display:flex; align-items:center; gap:12px;}
.avatar {width:42px; height:42px; border-radius:50%; background:#4f46e5; color:#fff; font-weight:700;
         display:flex; align-items:center; justify-content:center; flex:none;}
.obs {display:flex; gap:12px; align-items:flex-start;}
.num {width:26px; height:26px; border-radius:50%; background:rgba(79,70,229,.18); color:#4f46e5; font-weight:700;
      display:flex; align-items:center; justify-content:center; flex:none; font-size:.85rem;}
.steps {display:flex; gap:8px; flex-wrap:wrap; margin:10px 0 16px 0;}
.step {flex:1; min-width:150px; border-radius:12px; padding:10px 12px; font-size:.9rem;
       background:rgba(34,197,94,.14); border:1px solid rgba(34,197,94,.45);}
.step.warn {background:rgba(245,158,11,.16); border-color:rgba(245,158,11,.55);}
.step b {display:block;}
.tag {display:inline-block; padding:2px 10px; border-radius:999px; font-size:.78rem; font-weight:600;
      background:rgba(245,158,11,.2); border:1px solid rgba(245,158,11,.6);}
.tag.live {background:rgba(34,197,94,.18); border-color:rgba(34,197,94,.6);}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ history
def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(items):
    try:
        HISTORY_FILE.write_text(json.dumps(items[:10], indent=1), encoding="utf-8")
    except Exception:
        pass


def add_history(query, source):
    items = [i for i in load_history() if i.get("query") != query]
    items.insert(0, {"query": query, "source": source, "time": datetime.now().strftime("%d %b %H:%M")})
    save_history(items)


def set_query(q):
    st.session_state.query = q
    st.session_state.pending = True


def clear_history():
    save_history([])


for key, default in {"query": "", "result": None, "pending": False}.items():
    st.session_state.setdefault(key, default)

# ------------------------------------------------------------------ header & search area
st.markdown(
    '<div class="hero"><h1>Nepal Market Research Agent</h1>'
    "<p>Enter any company or industry. Four AI roles research, write, review and "
    "deliver a short brief.</p></div>", unsafe_allow_html=True)

c_in, c_btn = st.columns([5, 1.3])
with c_in:
    st.text_input("Company or industry", key="query", label_visibility="collapsed",
                  placeholder="Type a company or industry, e.g. Foodmandu, Nepal Telecom, banking in Nepal")
with c_btn:
    clicked = st.button("Start research", type="primary", use_container_width=True)

mode_label = st.radio("Search mode", list(MODES), horizontal=True, label_visibility="collapsed")
st.caption("Try an example:")
for col, ex in zip(st.columns(len(EXAMPLES)), EXAMPLES):
    col.button(ex, key=f"ex_{ex}", on_click=set_query, args=(ex,), use_container_width=True)

if clicked or st.session_state.pending:
    st.session_state.pending = False
    q = st.session_state.query.strip()
    if not q:
        st.warning("Please type a company or industry first.")
    else:
        try:
            with st.spinner("Agents are working: Orchestrator, Researcher, Analyst, Critic..."):
                st.session_state.result = run_workflow(q, MODES[mode_label])
            add_history(q, st.session_state.result.findings.data_source)
        except Exception as exc:
            st.error(f"Something went wrong: {exc}")

result = st.session_state.result

# ------------------------------------------------------------------ sidebar history
with st.sidebar:
    st.subheader("Recent searches")
    hist = load_history()
    if not hist:
        st.caption("Your searches will appear here.")
    for i, item in enumerate(hist):
        st.button(item["query"], key=f"h_{i}", on_click=set_query, args=(item["query"],), use_container_width=True)
        st.caption(f'{item["source"].title()} | {item["time"]}')
    if hist:
        st.button("Clear history", on_click=clear_history)


# ------------------------------------------------------------------ results
def esc(text):
    return html.escape(str(text))


def render(state):
    b, f = state.final_brief, state.findings
    live = "LIVE" in b.data_source
    st.markdown(f"## {esc(b.topic)}  "
                f'<span class="tag {"live" if live else ""}">{esc(b.data_source)}</span>', unsafe_allow_html=True)

    revised = state.revisions_used > 0
    crit = f"Revision {state.revisions_used} of 1 applied" if revised else "Approved, no revision"
    steps = [("Orchestrator", "Plan ready", False), ("Researcher", b.data_source.title(), False),
             ("Analyst", "Draft written", False), ("Critic", crit, revised)]
    st.markdown('<div class="steps">' + "".join(
        f'<div class="step {"warn" if w else ""}"><b>{n}</b>{esc(t)}</div>' for n, t, w in steps) + "</div>",
        unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Data source", b.data_source.title())
    c2.metric("Competitors", len(b.competitors))
    c3.metric("Revisions used", f"{state.revisions_used} of 1")
    c4.metric("Sources", len(b.sources))

    if f.data_source == "NO DATA FOUND":
        st.error(b.summary)
        for m in b.missing:
            st.write("- " + m)
        st.info("Closest names in the sample directory: " + ", ".join(suggestions(f.topic)))
    tab1, tab2, tab3 = st.tabs(["Brief", "Sources & gaps", "Data passed between roles"])
    with tab1:
        if f.data_source != "NO DATA FOUND":
            st.markdown(f'<div class="summary">{esc(b.summary)}</div>', unsafe_allow_html=True)
            st.markdown("#### Competitors (up to 2)")
            if b.competitors:
                cols = st.columns(2) if len(b.competitors) < 2 else st.columns(len(b.competitors))
                for col, c in zip(cols, b.competitors):
                    col.markdown(f'<div class="card comp"><div class="avatar">{esc(c[:2].upper())}</div>'
                                 f"<b>{esc(c)}</b></div>", unsafe_allow_html=True)
            else:
                st.caption("No competitors identified.")
            st.markdown("#### Key observations")
            for n, o in enumerate(b.observations, 1):
                st.markdown(f'<div class="card obs"><div class="num">{n}</div><div>{esc(o)}</div></div>',
                            unsafe_allow_html=True)
    with tab2:
        st.markdown("#### Sources")
        for s in b.sources or ["None"]:
            st.markdown("- " + s)
        st.markdown("#### Missing information")
        for m in b.missing:
            st.warning(m)
    with tab3:
        for title, obj in [("Orchestrator plan", state.plan), ("Researcher findings", state.findings),
                           ("Analyst draft", state.draft), ("Critic feedback", state.feedback),
                           ("Final brief", state.final_brief)]:
            with st.expander(title):
                st.json(obj.model_dump())
        st.caption("Run log: " + " -> ".join(state.log))

    slug = re.sub(r"[^a-z0-9]+", "-", b.topic.lower()).strip("-") or "brief"
    d1, d2, _ = st.columns([1, 1, 3])
    d1.download_button("Download brief (PDF)", data=_pdf(state), file_name=f"{slug}.pdf",
                       mime="application/pdf", disabled=make_pdf is None) if make_pdf else \
        d1.caption("Install fpdf2 for PDF export")
    d2.download_button("Download brief (Markdown)", data=brief_to_markdown(state),
                       file_name=f"{slug}.md", mime="text/markdown")


def _pdf(state):
    try:
        return make_pdf(state)
    except Exception:
        return b""


if result is not None:
    render(result)
