import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from workflow import run_workflow, run_critic, run_analyst, run_orchestrator, run_researcher

def test_sample_run_has_all_sections_and_max_two_competitors():
    s = run_workflow("Analyze the food delivery market in Nepal.", use_sample=True)
    assert s.final.summary and s.final.key_observations and s.final.sources_and_missing
    assert len(s.final.competitors) <= 2
    assert s.findings.label.startswith("SAMPLE")

def test_critic_requests_revision_when_failed_source_is_missing():
    plan = run_orchestrator("Analyze Foo", use_sample=False)
    findings = run_researcher(plan)          # no internet in test -> a failed source
    findings.sources[0].status = "failed"
    draft = run_analyst(plan, findings)
    draft.sources_and_missing = []           # pretend the analyst forgot it
    assert run_critic(draft, findings).approved is False

def test_sample_mode_falls_back_to_live_for_unknown_topic():
    s = run_workflow("Analyze Tesla", use_sample=True)
    assert s.findings.label.startswith("Live")
    assert any("No sample data" in g for g in s.findings.gaps)

def test_never_more_than_one_revision():
    s = run_workflow("Analyze Foo", use_sample=False)
    assert s.revisions_used <= 1

if __name__ == "__main__":
    test_sample_run_has_all_sections_and_max_two_competitors()
    test_critic_requests_revision_when_failed_source_is_missing()
    test_sample_mode_falls_back_to_live_for_unknown_topic()
    test_never_more_than_one_revision()
    print("All tests passed")