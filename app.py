import html
import json
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from pdf_export import brief_to_pdf
from workflow import run_workflow

st.set_page_config(page_title="Research Brief", page_icon="🔎", layout="wide")

# ---------------------------------------------------------------- styling
st.markdown("""<style>
.block-container{max-width:1080px;padding-top:.8rem;padding-bottom:3rem;}
#MainMenu,footer{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"],[data-testid="stAppDeployButton"],.stAppDeployButton{display:none !important;}
.nav{display:flex;align-items:center;justify-content:space-between;padding:.6rem .2rem 1rem;}
.logo{display:flex;align-items:center;gap:.6rem;font-weight:800;font-size:1.15rem;}
.logo i{font-style:normal;background:linear-gradient(135deg,#4f46e5,#06b6d4);color:#fff;
  width:2.1rem;height:2.1rem;border-radius:10px;display:inline-flex;align-items:center;justify-content:center;}
.navtag{font-size:.8rem;opacity:.75;border:1px solid rgba(127,127,127,.35);padding:.2rem .7rem;border-radius:999px;}
.hero{position:relative;overflow:hidden;text-align:center;color:#fff;border-radius:24px;padding:2.6rem 1.5rem 2.2rem;
  background:radial-gradient(circle at 15% 20%,rgba(255,255,255,.18),transparent 40%),
  linear-gradient(135deg,#4338ca 0%,#7c3aed 55%,#0891b2 100%);margin-bottom:1.1rem;}
.hero h1{color:#fff;font-size:2.4rem;margin:0 0 .5rem;line-height:1.15;}
.hero p{margin:0 auto;max-width:640px;opacity:.93;font-size:1.05rem;}
.hero .tags{margin-top:1.1rem;display:flex;gap:.5rem;justify-content:center;flex-wrap:wrap;}
.hero .tags span{background:rgba(255,255,255,.18);padding:.25rem .8rem;border-radius:999px;font-size:.8rem;}
div[data-baseweb="input"]{border-radius:14px !important;}
div[data-baseweb="input"] input{font-size:1.05rem;padding:.65rem .8rem;}
.stButton>button{border-radius:12px;font-weight:600;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#4f46e5,#7c3aed);border:0;color:#fff;}
.try{font-size:.85rem;opacity:.7;margin:.1rem 0 .2rem;}
.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem;margin:.9rem 0 1.1rem;}
.step{border-radius:16px;padding:.85rem 1rem;border:1px solid rgba(127,127,127,.28);background:rgba(127,127,127,.06);}
.step .n{display:inline-flex;width:1.5rem;height:1.5rem;border-radius:50%;align-items:center;justify-content:center;
  font-size:.78rem;font-weight:700;background:rgba(127,127,127,.25);margin-right:.45rem;}
.step b{font-size:.95rem;} .step span.d{display:block;font-size:.8rem;opacity:.78;margin-top:.25rem;}
.step.running{border-color:#6366f1;background:rgba(99,102,241,.12);box-shadow:0 0 0 3px rgba(99,102,241,.15);}
.step.running .n{background:#6366f1;color:#fff;animation:pulse 1s infinite;}
.step.done{border-color:#22c55e;background:rgba(34,197,94,.10);} .step.done .n{background:#22c55e;color:#fff;}
.step.rev{border-color:#f59e0b;background:rgba(245,158,11,.12);} .step.rev .n{background:#f59e0b;color:#fff;}
@keyframes pulse{50%{transform:scale(1.18);}}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem;margin:.4rem 0 .3rem;}
.kpi{border-radius:16px;padding:.9rem 1rem;border:1px solid rgba(127,127,127,.28);background:rgba(127,127,127,.06);}
.kpi .v{font-size:1.55rem;font-weight:800;line-height:1.1;} .kpi .l{font-size:.8rem;opacity:.75;margin-top:.15rem;}
.card{background:rgba(127,127,127,.07);border:1px solid rgba(127,127,127,.25);border-radius:16px;
  padding:1rem 1.2rem;margin-bottom:.8rem;line-height:1.55;}
.card.accent{border-left:5px solid #6366f1;} .card.amber{border-left:5px solid #f59e0b;background:rgba(245,158,11,.08);}
.card h4{margin:0 0 .35rem;font-size:1.02rem;}
.comp{display:flex;gap:.9rem;align-items:flex-start;}
.av{flex:0 0 2.7rem;height:2.7rem;border-radius:14px;background:linear-gradient(135deg,#4f46e5,#06b6d4);color:#fff;
  font-weight:800;font-size:1.2rem;display:flex;align-items:center;justify-content:center;}
.obs{display:flex;gap:.8rem;align-items:flex-start;}
.num{flex:0 0 1.7rem;height:1.7rem;border-radius:50%;background:rgba(99,102,241,.18);color:#6366f1;font-weight:700;
  font-size:.85rem;display:flex;align-items:center;justify-content:center;margin-top:.1rem;}
.pill{display:inline-block;padding:.12rem .7rem;border-radius:999px;font-size:.78rem;font-weight:600;margin-right:.4rem;}
.ok{background:#dcfce7;color:#166534;} .warn{background:#fef3c7;color:#92400e;}
.bad{background:#fee2e2;color:#991b1b;} .info{background:#e0e7ff;color:#3730a3;}
.sec{font-size:1.05rem;font-weight:700;margin:1.1rem 0 .5rem;}
.empty{text-align:center;opacity:.7;padding:1.2rem;border:1px dashed rgba(127,127,127,.4);border-radius:16px;}
@media(max-width:760px){.steps,.kpis{grid-template-columns:1fr 1fr;}.hero h1{font-size:1.7rem;}}
</style>""", unsafe_allow_html=True)

esc = html.escape
AUTO = "Auto (Nepal directory, then web)"
LIVE = "Live web search only"
EXAMPLES = [("Foodmandu", "Foodmandu", AUTO),
            ("Food delivery in Nepal", "Analyze the food delivery market in Nepal.", AUTO),
            ("eSewa", "eSewa", AUTO), ("Tesla", "Tesla", LIVE)]
ROLES = [("Orchestrator", "Plans the run"), ("Researcher", "Finds sources"),
         ("Analyst", "Writes the brief"), ("Critic", "Reviews quality")]
HISTORY_FILE = Path(__file__).resolve().parent / "history.json"

st.session_state.setdefault("query", "")
st.session_state.setdefault("mode", AUTO)


# ---------------------------------------------------------------- history (saved in history.json)
def load_history():
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(items):
    try:
        HISTORY_FILE.write_text(json.dumps(items[:10], indent=1), encoding="utf-8")
    except Exception:
        pass   # history is a convenience; never break the app


def add_history(query, mode, source):
    items = [h for h in load_history() if h["query"].lower() != query.lower()]
    items.insert(0, {"query": query, "mode": mode, "source": source,
                     "time": datetime.now().strftime("%d %b, %H:%M")})
    save_history(items)


def pick(q, mode):
    st.session_state.query, st.session_state.mode, st.session_state.autorun = q, mode, True


def clear_history():
    save_history([])


# ---------------------------------------------------------------- html helpers
def steps_html(status, notes=None):
    notes = notes or {}
    out = []
    for i, (name, desc) in enumerate(ROLES):
        cls = status[i]
        mark = "✓" if cls in ("done", "rev") else str(i + 1)
        out.append(f'<div class="step {cls}"><span class="n">{mark}</span><b>{name}</b>'
                   f'<span class="d">{esc(notes.get(name, desc))}</span></div>')
    return '<div class="steps">' + "".join(out) + "</div>"


def to_markdown(state):
    d, f = state.final, state.findings
    out = [f"# Research Brief: {state.plan.topic}", f"*Data source: {f.label}*", "",
           "## Summary", d.summary, "", "## Competitors (up to 2)"]
    out += [f"- **{c.name}**: {c.description}" for c in d.competitors] or ["- None identified"]
    out += ["", "## Key observations"] + [f"- {o}" for o in d.key_observations]
    out += ["", "## Sources and missing information"] + [f"- {x}" for x in d.sources_and_missing]
    return "\n".join(out)


# ---------------------------------------------------------------- header
st.markdown('<div class="nav"><div class="logo"><i>🔎</i>Research Brief</div>'
            '<span class="navtag">Multi-agent market research</span></div>', unsafe_allow_html=True)
hero_slot = st.empty()
if st.session_state.get("state") is None:
    hero_slot.markdown('<div class="hero"><h1>Research any company or industry</h1>'
            '<p>Four AI roles work in sequence: they plan, search, write and review a short, sourced brief for you.</p>'
            '<div class="tags"><span>Orchestrator</span><span>Researcher</span><span>Analyst</span>'
            '<span>Critic</span></div></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- input
i1, i2 = st.columns([5, 1.3])
i1.text_input("Company or industry", key="query", label_visibility="collapsed",
              placeholder="Type a company or industry, e.g. Foodmandu, eSewa, Nabil Bank")
run = i2.button("🔍 Research", type="primary", use_container_width=True)
st.radio("Research mode", [AUTO, LIVE], key="mode", horizontal=True, label_visibility="collapsed",
         help="Auto looks in a labelled Nepal company directory first, then searches Wikipedia.")
st.markdown('<div class="try">Try an example</div>', unsafe_allow_html=True)
for col, (label, q, mode) in zip(st.columns(len(EXAMPLES)), EXAMPLES):
    col.button(label, key=f"ex_{label}", on_click=pick, args=(q, mode), use_container_width=True)

autorun = st.session_state.pop("autorun", False)
if run and not st.session_state.query.strip():
    st.warning("Please type a company or industry first.")

steps_slot = st.empty()
state = st.session_state.get("state")

if (run or autorun) and st.session_state.query.strip():
    hero_slot.empty()
    status = ["idle"] * 4
    steps_slot.markdown(steps_html(status), unsafe_allow_html=True)

    def on_step(msg):
        role = msg.split(":")[0].split(" ")[0]
        i = [r[0] for r in ROLES].index(role)
        for j in range(i):
            status[j] = "done"
        status[i] = "running"
        steps_slot.markdown(steps_html(status), unsafe_allow_html=True)
        time.sleep(0.4)

    with st.spinner("Agents are working..."):
        state = run_workflow(st.session_state.query, st.session_state.mode == AUTO, on_step=on_step)
    st.session_state["state"] = state
    add_history(st.session_state.query.strip(), st.session_state.mode,
                "Directory" if state.findings.label.startswith("SAMPLE") else "Live web")

# ---------------------------------------------------------------- results
if state is None:
    steps_slot.markdown(steps_html(["idle"] * 4), unsafe_allow_html=True)
    st.markdown('<div class="empty">Your brief will appear here. Type a company above, or click an example.</div>',
                unsafe_allow_html=True)
else:
    f, d = state.findings, state.final
    read = [s for s in f.sources if s.status in ("fetched", "sample")]
    rev = state.revisions_used
    st_status = ["done", "done", "rev" if rev else "done", "rev" if rev else "done"]
    steps_slot.markdown(steps_html(st_status, {
        "Researcher": f"{len(read)} source(s) read",
        "Analyst": "Draft + 1 revision" if rev else "Wrote the brief",
        "Critic": "Requested a revision" if rev else "Approved the draft"}), unsafe_allow_html=True)

    st.markdown(f"### {esc(state.plan.topic.title())}")
    is_sample = f.label.startswith("SAMPLE")
    st.markdown(f'<div class="kpis">'
                f'<div class="kpi"><div class="v">{len(read)} / {len(f.sources)}</div><div class="l">Sources read</div></div>'
                f'<div class="kpi"><div class="v">{len(d.competitors)}</div><div class="l">Competitors found</div></div>'
                f'<div class="kpi"><div class="v">{rev} / 1</div><div class="l">Critic revisions</div></div>'
                f'<div class="kpi"><div class="v">{"Directory" if is_sample else "Live web"}</div>'
                f'<div class="l">Data source</div></div></div>', unsafe_allow_html=True)
    if not read:
        st.warning("No sources could be read. Check your internet connection, or try one of the examples.")

    tab1, tab2, tab3 = st.tabs(["📄 Brief", "🔗 Sources & gaps", "🧩 Data passed between roles"])
    with tab1:
        st.markdown(f'<span class="pill {"warn" if is_sample else "ok"}">{esc(f.label)}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="sec">Summary</div><div class="card accent">{esc(d.summary)}</div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="sec">Competitors (up to 2)</div>', unsafe_allow_html=True)
        if d.competitors:
            for col, c in zip(st.columns(len(d.competitors)), d.competitors):
                col.markdown(f'<div class="card comp"><div class="av">{esc(c.name[:1].upper())}</div>'
                             f'<div><h4>{esc(c.name)}</h4>{esc(c.description)}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">No competitors were identified for this topic.</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec">Key observations</div>', unsafe_allow_html=True)
        for n, o in enumerate(d.key_observations, 1):
            st.markdown(f'<div class="card obs"><div class="num">{n}</div><div>{esc(o)}</div></div>',
                        unsafe_allow_html=True)
        st.markdown('<div class="sec">Sources and missing information</div>', unsafe_allow_html=True)
        st.markdown('<div class="card amber">' + "<br>".join("• " + esc(x) for x in d.sources_and_missing) + "</div>",
                    unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        b1.download_button("⬇ Download brief (PDF)", brief_to_pdf(state), file_name="research_brief.pdf",
                           mime="application/pdf", type="primary", use_container_width=True)
        b2.download_button("⬇ Download brief (Markdown)", to_markdown(state), file_name="research_brief.md",
                           mime="text/markdown", use_container_width=True)
    with tab2:
        for s in f.sources:
            cls = {"fetched": "ok", "sample": "warn", "failed": "bad"}.get(s.status, "info")
            link = (f'<a href="{esc(s.url)}" target="_blank">{esc(s.title)}</a>'
                    if s.url.startswith("http") else esc(s.title))
            st.markdown(f'<div class="card"><span class="pill {cls}">{esc(s.status)}</span>{link}'
                        f'<br><small>{esc(s.note)}</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="sec">Missing information</div>', unsafe_allow_html=True)
        st.markdown('<div class="card amber">' + "<br>".join("• " + esc(g) for g in f.gaps) + "</div>",
                    unsafe_allow_html=True)
    with tab3:
        st.caption("Each role receives and returns structured Pydantic data. This is the full run state.")
        st.json(state.model_dump())

# ---------------------------------------------------------------- sidebar: history (drawn last so it is up to date)
with st.sidebar:
    st.markdown("### 🕘 Recent searches")
    history = load_history()
    if not history:
        st.caption("Your searches will appear here.")
    for n, h in enumerate(history):
        st.button(f'{h["query"][:30]}', key=f"h{n}", on_click=pick, args=(h["query"], h["mode"]),
                  use_container_width=True, help=f'{h["source"]} | {h["time"]}')
        st.caption(f'{h["source"]} · {h["time"]}')
    if history:
        st.button("Clear history", on_click=clear_history, use_container_width=True)
    st.divider()
    st.caption("History is saved on this computer in history.json.")