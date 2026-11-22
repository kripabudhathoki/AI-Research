# Multi-Agent Market Research Brief

A Streamlit app that accepts a company or industry query and generates a short
research brief through a four-role sequential agent workflow. All agent handoffs
use typed Pydantic models.

## The four roles

| Role | What it does |
|------|-------------|
| Orchestrator | Cleans the query into a search topic and sets the plan |
| Researcher | Returns clearly-labelled sample data or live Wikipedia search results |
| Analyst | Writes the first brief draft from findings; revises once if Critic requests |
| Critic | Checks completeness; requests at most one revision if issues are found |

## Shared Pydantic models (passed between roles)

- `OrchestratorPlan` — query, cleaned topic, use_sample flag, ordered steps
- `ResearchFindings` — data-source label, facts, competitors, sources, gaps
- `BriefDraft` — summary, up to 2 competitors, key observations, sources and missing info
- `CriticFeedback` — approved flag, list of issues, optional revision request
- `RunState` — all of the above plus revisions_used (0 or 1)

## The four brief sections

1. Summary of the topic
2. Up to two competitors (if relevant)
3. Key observations
4. Sources and missing information

## How to run

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

## Sample data vs live search

Tick **"Use clearly labelled sample data"** (default) to run offline.
The sample covers the Nepal food delivery example; for any other topic in sample mode
the app falls back to a live Wikipedia search automatically. Untick to always use live search.
Run `python make_sample_output.py` to regenerate `sample_output.md` from the workflow.

## Tests

```bash
python tests/test_workflow.py
```

## Limitations

- Analyst and Critic are rule-based, not LLM-powered.
- Live search uses only the public Wikipedia API; it may return no results for
  local or niche topics.
- Market size, market share, and financial data are not fetched automatically.
