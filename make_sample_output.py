"""Generate sample_output.md by running the workflow on the assignment example."""
from datetime import date
from workflow import run_workflow

QUERY = "Analyze the food delivery market in Nepal."
state = run_workflow(QUERY, use_sample=True)
f, d = state.findings, state.final

lines = [
    f"# Sample Output",
    f"",
    f"**Query:** {QUERY}",
    f"**Data source:** {f.label}",
    f"**Critic revisions used:** {state.revisions_used} of 1",
    f"**Date generated:** {date.today()}",
    f"",
    f"## Summary",
    f"",
    d.summary,
    f"",
    f"## Competitors (up to 2)",
    f"",
]
for c in d.competitors:
    lines.append(f"- **{c.name}**: {c.description}")
if not d.competitors:
    lines.append("- No competitors identified.")
lines += ["", "## Key observations", ""]
for o in d.key_observations:
    lines.append(f"- {o}")
lines += ["", "## Sources and missing information", ""]
for s in d.sources_and_missing:
    lines.append(f"- {s}")

with open("sample_output.md", "w") as fh:
    fh.write("\n".join(lines) + "\n")
print("Written sample_output.md")
