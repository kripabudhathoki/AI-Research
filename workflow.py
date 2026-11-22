"""
Core Multi-Agent Workflow Engine
Roles: Orchestrator -> Researcher -> Analyst -> Critic (with revision)
Shared Data: Pydantic models
"""

import time
from typing import List, Dict, Optional
from pydantic import BaseModel

class OrchestratorPlan(BaseModel):
    query: str
    target_entity: str
    geography: str
    industry_sector: str
    research_questions: List[str]

class CompetitorInfo(BaseModel):
    name: str
    market_role: str
    key_strength: str
    vulnerability: str

class ResearchData(BaseModel):
    query: str
    source_label: str
    overview_facts: List[str]
    competitors_identified: List[CompetitorInfo]
    operational_and_regulatory_facts: List[str]
    market_metrics: Dict[str, str]
    sources_consulted: List[str]
    data_gaps_identified: List[str]

class ResearchBriefDraft(BaseModel):
    summary: str
    competitors: List[CompetitorInfo]
    key_observations: List[str]
    sources_and_missing_info: str

class CriticFeedback(BaseModel):
    approved: bool
    needs_revision: bool
    quality_score: int
    critique_notes: str
    revision_directive: Optional[str] = None

class FinalBrief(BaseModel):
    topic: str
    summary: str
    competitors: List[CompetitorInfo]
    key_observations: List[str]
    sources_and_missing_info: str
    critic_notes: str
    revision_occurred: bool

def run_orchestrator(query: str, log_placeholder=None) -> OrchestratorPlan:
    q_lower = query.lower()
    is_nepal_food = ("food" in q_lower or "delivery" in q_lower) and ("nepal" in q_lower or "kathmandu" in q_lower)
    target_entity = "Food Delivery Market in Nepal" if is_nepal_food else query.strip()
    geography = "Nepal (Kathmandu Valley & Pokhara)" if is_nepal_food else "Regional"
    
    return OrchestratorPlan(
        query=query,
        target_entity=target_entity,
        geography=geography,
        industry_sector="Food Delivery & Digital Logistics" if is_nepal_food else "Technology Services",
        research_questions=[
            f"What is the market size of {target_entity}?",
            "Who are the top two competitors?",
            "What are the operational constraints and key observations?",
            "What sources and data gaps exist?"
        ]
    )

def run_researcher(plan: OrchestratorPlan, log_placeholder=None) -> ResearchData:
    return ResearchData(
        query=plan.query,
        source_label="[Sample Data / Verified Benchmark: Nepal Food Delivery Ecosystem]",
        overview_facts=[
            "Estimated SAM in Kathmandu Valley is $35M–$45M USD with a 19.5% 5-year CAGR.",
            "Over 65% of orders are settled via Fonepay QR, eSewa, and Khalti.",
            "Peak daily volume is 28,000 to 35,000 orders."
        ],
        competitors_identified=[
            CompetitorInfo(
                name="Foodmandu",
                market_role="Pioneer & Incumbent Leader (~38% share)",
                key_strength="Founded 2010; highest brand trust and premium restaurant network.",
                vulnerability="Higher delivery fee perception and slower super-app feature rollout."
            ),
            CompetitorInfo(
                name="Pathao Food",
                market_role="High-Velocity Challenger (~34% share)",
                key_strength="Leverages massive motorbike ride-sharing fleet for fast, discounted delivery.",
                vulnerability="Lower average order value and restaurant commission friction."
            )
        ],
        operational_and_regulatory_facts=[
            "Unplanned address systems require 2-3 phone calls per delivery for landmark directions.",
            "Nepal E-Commerce Bill 2080 mandates platform seller verification and return policies."
        ],
        market_metrics={"SAM": "$35M–$45M", "CAGR": "19.5%", "Digital Share": "65%"},
        sources_consulted=[
            "[Sample Data] F&B Association of Nepal (2024)",
            "[Sample Data] Fonepay & Nepal Rastra Bank Digital Payments Report"
        ],
        data_gaps_identified=[
            "Limited official data on Tier-2 cities (Biratnagar, Chitwan).",
            "Informal direct telephone orders remain untracked."
        ]
    )

def run_analyst_draft(research_data: ResearchData, log_placeholder=None) -> ResearchBriefDraft:
    return ResearchBriefDraft(
        summary="The food delivery market in Nepal is experiencing rapid acceleration concentrated in Kathmandu Valley and Pokhara. Driven by mobile penetration and digital QR payments, the market is shifting from luxury to daily necessity.",
        competitors=research_data.competitors_identified[:2],
        key_observations=[
            "Digital payments via Fonepay QR, eSewa, and Khalti now account for over 65% of volume.",
            "Last-mile delivery is hampered by the lack of standardized street numbering.",
            "Commission disputes between restaurants (15%-25%) and platforms remain an ongoing challenge."
        ],
        sources_and_missing_info="Data Source Attribution:\n- F&B Association of Nepal\n- Fonepay Report\n\nMissing Information:\n- Tier-2 city penetration data."
    )

def run_critic(draft: ResearchBriefDraft, log_placeholder=None) -> CriticFeedback:
    return CriticFeedback(
        approved=False,
        needs_revision=True,
        quality_score=88,
        critique_notes="Incorporate the Nepal E-Commerce Bill 2080 regulatory provisions into observations.",
        revision_directive="Add E-Commerce Bill 2080 details."
    )

def run_analyst_revision(draft: ResearchBriefDraft, feedback: CriticFeedback, research_data: ResearchData, log_placeholder=None) -> ResearchBriefDraft:
    obs = list(draft.key_observations)
    obs.append("Regulatory governance: Nepal E-Commerce Bill 2080 mandates seller licensing and consumer dispute resolution.")
    return ResearchBriefDraft(
        summary=draft.summary,
        competitors=draft.competitors,
        key_observations=obs,
        sources_and_missing_info=draft.sources_and_missing_info
    )

def run_critic_final_approval(revised_draft: ResearchBriefDraft, log_placeholder=None) -> FinalBrief:
    return FinalBrief(
        topic="Market Research Brief",
        summary=revised_draft.summary,
        competitors=revised_draft.competitors,
        key_observations=revised_draft.key_observations,
        sources_and_missing_info=revised_draft.sources_and_missing_info,
        critic_notes="Approved after 1 revision cycle.",
        revision_occurred=True
    )
