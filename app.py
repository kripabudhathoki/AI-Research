"""
Research Brief — Multi-Agent Market Research Web Application
Workflow: 4 Sequential Roles (Orchestrator -> Researcher -> Analyst -> Critic [with revision loop])
UI Design: Exact clean layout from prototype with real advanced research capabilities
"""

from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Research Brief",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>R</text></svg>",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit's default headers, footers and margins to display the full design system
st.markdown("""
<style>
#MainMenu { visibility: hidden !important; display: none !important; }
footer { visibility: hidden !important; display: none !important; }
header { visibility: hidden !important; display: none !important; }
.stDeployButton { display: none !important; }
.main, .main .block-container, section.main, [data-testid="stAppViewBlockContainer"], [data-testid="stMainBlockContainer"], .block-container {
    padding: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
}
[data-testid="stCustomComponentV1"], div[data-testid="stCustomComponentV1"] > iframe, .element-container {
    width: 100% !important;
    max-width: 100% !important;
}
iframe {
    width: 100% !important;
    min-height: 100vh !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# Read the HTML application template
html_path = Path(__file__).resolve().parent / "public" / "index.html"
if html_path.exists():
    with open(html_path, "r", encoding="utf-8") as f:
        app_html = f.read()
else:
    app_html = "<h1>Error: HTML template not found</h1>"

components.html(app_html, height=1000, scrolling=True)
