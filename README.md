# Nepal Market Research Agent

A Streamlit app that takes a company or industry (for example "Foodmandu" or "Analyze the food delivery
market in Nepal") and produces a short research brief using four roles that run in sequence.

## The four roles
| Role | Job |
|---|---|
| Orchestrator | Receives the query, cleans the topic, creates the plan |
| Researcher | Looks the topic up in the sample directory and/or live web search |
| Analyst | Writes the brief from the findings |
| Critic | Reviews the brief and requests at most one revision |

Data is passed between roles as Pydantic models (`workflow.py`): `OrchestratorPlan`, `ResearchFindings`,
`BriefDraft`, `CriticFeedback`, `RunState`. The app shows them in the "Data passed between roles" tab.

## The brief
Summary, up to two competitors, key observations, and sources with missing information.
Download it as PDF or Markdown. Recent searches are kept in the sidebar (saved locally in `history.json`,
not committed).

## Data sources (always labelled)
- **Sample directory**: `data/nepal_companies.json` has about 40 Nepali companies and sectors written from
  general knowledge. It is labelled SAMPLE DATA and must be verified. Edit the file to add companies.
- **Live web search**: Wikipedia, with DuckDuckGo as a fallback. No API key is needed. If the network is
  blocked, the brief says so instead of showing an empty page.
- **Modes**: Auto (directory first, then live), Sample only, Live only. If nothing is found, the app says so
  and never invents data.

## Run locally
```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Open http://localhost:8501. Copy `.env.example` to `.env` only if you add an API-based model later.

## Tests and sample output
```
python tests/test_workflow.py
python make_sample_output.py     # regenerates sample_output.md from a real run
```

## Limitations
The Analyst and Critic are rule-based (no language model). Live search covers what Wikipedia and
DuckDuckGo know, so small Nepali companies may not be found; add them to the sample directory.
