import html
import streamlit as st
from workflow import run_workflow

st.set_page_config(page_title="Research Brief", page_icon="🔎", layout="wide")

st.markdown("""<style>
.block-container{max-width:1100px;padding-top:1.5rem;}
#MainMenu,footer{visibility:hidden;}
.hero{background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 55%,#06b6d4 100%);color:#fff;
  padding:2.2rem 2rem;border-radius:20px;margin-bottom:1.2rem;}
.hero h1{margin:0 0 .4rem;font-size:2.1rem;color:#fff;}
.hero p{margin:0;opacity:.93;font-size:1.05rem;}
.card{background:rgba(127,127,127,.08);border:1px solid rgba(127,127,127,.25);
  border-radius:16px;padding:1.1rem 1.3rem;margin-bottom:.9rem;}
.card h4{margin:0 0 .4rem;}
.pill{display:inline-block;padding:.12rem .7rem;border-radius:999px;font-size:.78rem;
  font-weight:600;margin-right:.4rem;}
.ok{background:#dcfce7;color:#166534;} .warn{background:#fef3c7;color:#92400e;}
.bad{background:#fee2e2;color:#991b1b;} .info{background:#e0e7ff;color:#3730a3;}
.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem;margin:.4rem 0 1.2rem;}
.step{border-radius:14px;padding:.8rem 1rem;border:1px solid rgba(127,127,127,.25);
  background:rgba(127,127,127,.06);}
.step b{display:block;} .step span{font-size:.82rem;opacity:.8;}
.step.done{border-color:#22c55e;background:rgba(34,197,94,.10);}
.step.rev{border-color:#f59e0b;background:rgba(245,158,11,.12);}
@media(max-width:700px){.steps{grid-template-columns:1fr 1fr;}}
</style>""", unsafe_allow_html=True)

esc = html.escape
EXAMPLES = [("Food delivery in Nepal", "Analyze the food delivery market in Nepal.", "Sample data"),
            ("Tesla", "Tesla", "Live web search"),
            ("Khalti", "Khalti", "Live web search")]

st.session_state.setdefault("query", "Analyze the food delivery market in Nepal.")
st.session_state.setdefault("mode", "Sample data")

def pick_example(q, mode):
    st.session_state.query, st.session_state.mode, st.session_state.autorun = q, mode, True

def to_markdown(state):
    d, f = state.final, state.findings
    out = [f"# Research Brief: {state.plan.topic}", f"*Data source: {f.label}*", "",
           "## Summary", d.summary, "", "## Competitors (up to 2)"]
    out += [f"- **{c.name}**: {c.description}" for c in d.competitors] or ["- None identified"]
    out += ["", "## Key observations"] + [f"- {o}" for o in d.key_observations]
    out += ["", "## Sources and missing information"] + [f"- {x}" for x in d.sources_and_missing]
    return "\n".join(out)

# ---------- Header and input ----------
st.markdown("""<div class="hero"><h1>🔎 Multi-Agent Research Brief</h1>
<p>Enter a company or industry. Four AI roles (Orchestrator, Researcher, Analyst and Critic)
work in sequence and produce a short, sourced brief.</p></div>""", unsafe_allow_html=True)

c1, c2 = st.columns([3, 2])
c1.text_input("Company or industry", key="query", placeholder="e.g. Analyze the food delivery market in Nepal")
c2.radio("Research mode", ["Live web search", "Sample data"], key="mode", horizontal=True,
         help="Sample data works offline and is clearly labelled. Live search uses Wikipedia.")
b1, b2 = st.columns([1, 3])
run = b1.button("Start research", type="primary", use_container_width=True)
with b2:
    st.caption("Try an example:")
    cols = st.columns(len(EXAMPLES))
    for col, (label, q, mode) in zip(cols, EXAMPLES):
        col.button(label, key=f"ex_{label}", on_click=pick_example, args=(q, mode),
                   use_container_width=True)

if (run or st.session_state.pop("autorun", False)) and st.session_state.query.strip():
    with st.status("Agents are working...", expanded=True) as status:
        st.session_state["state"] = run_workflow(
            st.session_state.query, st.session_state.mode == "Sample data",
            on_step=lambda m: st.write("✅ " + m))
        status.update(label="Research complete", state="complete", expanded=False)

# ---------- Results ----------
state = st.session_state.get("state")
if state:
    f, d, fb = state.findings, state.final, state.feedback
    read = [s for s in f.sources if s.status in ("fetched", "sample")]
    st.markdown(f"### {esc(state.plan.topic.title())}")
    m = st.columns(4)
    m[0].metric("Sources read", f"{len(read)} of {len(f.sources)}")
    m[1].metric("Competitors found", len(d.competitors))
    m[2].metric("Critic revisions", f"{state.revisions_used} of 1")
    m[3].metric("Data", "Sample" if f.label.startswith("SAMPLE") else "Live")

    rev = state.revisions_used
    steps = [("Orchestrator", "Planned the research", ""),
             ("Researcher", f"{len(read)} source(s) read", ""),
             ("Analyst", "Draft + 1 revision" if rev else "Wrote the brief", "rev" if rev else ""),
             ("Critic", "Requested a revision" if rev else "Approved the draft", "rev" if rev else "")]
    st.markdown('<div class="steps">' + "".join(
        f'<div class="step done {c}"><b>✔ {n}</b><span>{esc(s)}</span></div>'
        for n, s, c in steps) + '</div>', unsafe_allow_html=True)

    if not read:
        st.warning("No sources could be read. Check your internet connection, try a different "
                   "name, or switch to Sample data.")

    tab1, tab2, tab3 = st.tabs(["📄 Brief", "🔗 Sources & gaps", "🧩 Data passed between roles"])
    with tab1:
        st.markdown(f'<span class="pill {"warn" if f.label.startswith("SAMPLE") else "ok"}">'
                    f'{esc(f.label)}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="card"><h4>Summary</h4>{esc(d.summary)}</div>', unsafe_allow_html=True)
        st.markdown("#### Competitors (up to 2)")
        if d.competitors:
            for col, c in zip(st.columns(len(d.competitors)), d.competitors):
                col.markdown(f'<div class="card"><h4>{esc(c.name)}</h4>{esc(c.description)}</div>',
                             unsafe_allow_html=True)
        else:
            st.info("No competitors were identified for this topic.")
        st.markdown("#### Key observations")
        for o in d.key_observations:
            st.markdown(f'<div class="card">{esc(o)}</div>', unsafe_allow_html=True)
        st.download_button("⬇ Download brief (.md)", to_markdown(state),
                           file_name="research_brief.md", mime="text/markdown")
    with tab2:
        for s in f.sources:
            cls = {"fetched": "ok", "sample": "warn", "failed": "bad"}.get(s.status, "info")
            link = f'<a href="{esc(s.url)}" target="_blank">{esc(s.title)}</a>' if s.url.startswith("http") else esc(s.title)
            st.markdown(f'<div class="card"><span class="pill {cls}">{esc(s.status)}</span>{link}'
                        f'<br><small>{esc(s.note)}</small></div>', unsafe_allow_html=True)
        st.markdown("#### Missing information")
        for x in d.sources_and_missing:
            st.markdown(f"- {x}")
    with tab3:
        st.caption("Each role receives and returns structured Pydantic data. This is the full run state.")
        st.json(state.model_dump())