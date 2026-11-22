"""Regenerate sample_output.md from a real run of the workflow (sample mode)."""
from workflow import brief_to_markdown, run_workflow

state = run_workflow("Analyze the food delivery market in Nepal.", mode="sample")
with open("sample_output.md", "w", encoding="utf-8") as f:
    f.write(brief_to_markdown(state))
print("sample_output.md written")
