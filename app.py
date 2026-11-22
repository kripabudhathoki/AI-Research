import streamlit as st
from workflow import run_workflow

st.set_page_config(page_title="Research Brief", layout="wide")
st.title("Multi-Agent Market Research Brief")

query = st.text_input("Company or industry",
                      value="Analyze the food delivery market in Nepal.")
use_sample = st.checkbox("Use clearly labelled sample data (no internet needed)", value=True)

if st.button("Start research", type="primary") and query.strip():
    with st.status("Running agents...", expanded=True) as status:
        state = run_workflow(query, use_sample, on_step=lambda m: st.write(m))
        status.update(label="Done", state="complete")
    st.session_state["state"] = state

state = st.session_state.get("state")
if state:
    f, d = state.findings, state.final
    st.caption(f"Data source: {f.label} | Critic revisions used: {state.revisions_used} of 1")
    st.header("Summary");            st.write(d.summary)
    st.header("Competitors (up to 2)")
    for c in d.competitors:
        st.markdown(f"**{c.name}**: {c.description}")
    if not d.competitors:
        st.write("No competitors identified.")
    st.header("Key observations")
    for o in d.key_observations:
        st.markdown(f"- {o}")
    st.header("Sources and missing information")
    for s in d.sources_and_missing:
        st.markdown(f"- {s}")
    with st.expander("Data passed between roles"):
        st.json(state.model_dump())