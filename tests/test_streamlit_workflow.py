#!/usr/bin/env python3
"""Automated Unit & Pipeline Test for Streamlit Multi-Agent App."""

import sys
from pathlib import Path

# Add workspace to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from workflow import (
    run_orchestrator,
    run_researcher,
    run_analyst_draft,
    run_critic,
    run_analyst_revision,
    run_critic_final_approval,
    OrchestratorPlan,
    ResearchData,
    ResearchBriefDraft,
    CriticFeedback,
    FinalBrief
)

class DummyPlaceholder:
    def container(self):
        return self
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def empty(self):
        pass

def test_pipeline():
    print("--- Running Streamlit Multi-Agent Workflow Unit Tests ---")
    query = "Analyze the food delivery market in Nepal."
    dummy = DummyPlaceholder()

    # Step 1: Orchestrator
    plan = run_orchestrator(query, dummy)
    assert isinstance(plan, OrchestratorPlan)
    assert plan.target_entity == "Food Delivery Market in Nepal"
    print("✅ [Role 1] OrchestratorPlan verified:", plan.target_entity)

    # Step 2: Researcher
    data = run_researcher(plan, dummy)
    assert isinstance(data, ResearchData)
    assert "[Sample Data" in data.source_label
    assert len(data.competitors_identified) <= 2
    print(f"✅ [Role 2] ResearchData verified ({data.source_label}): {len(data.competitors_identified)} competitors")

    # Step 3: Analyst (Draft 1)
    draft1 = run_analyst_draft(data, dummy)
    assert isinstance(draft1, ResearchBriefDraft)
    assert len(draft1.competitors) <= 2
    assert len(draft1.key_observations) >= 3
    assert "Data Source Attribution" in draft1.sources_and_missing_info
    print("✅ [Role 3] Analyst Draft #1 verified.")

    # Step 4: Critic (Review & Revision Request)
    critic_res = run_critic(draft1, dummy)
    assert isinstance(critic_res, CriticFeedback)
    assert critic_res.needs_revision is True
    assert critic_res.revision_directive is not None
    print(f"✅ [Role 4] Critic Feedback verified: Requested revision -> '{critic_res.revision_directive}'")

    # Step 5: Analyst Revision
    draft2 = run_analyst_revision(draft1, critic_res, data, dummy)
    assert isinstance(draft2, ResearchBriefDraft)
    assert "E-Commerce Bill" in "\n".join(draft2.key_observations)
    print("✅ [Role 3 (Revision Loop)] Analyst successfully applied revision directive.")

    # Step 6: Final Critic Approval
    final = run_critic_final_approval(draft2, dummy)
    assert isinstance(final, FinalBrief)
    assert len(final.competitors) <= 2
    assert final.revision_occurred is True
    print("✅ [Role 4 (Approval)] FinalBrief generated and verified!")
    print("\n🎉 ALL STREAMLIT AGENT WORKFLOW TESTS PASSED!\n")

if __name__ == "__main__":
    test_pipeline()

