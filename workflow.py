"""Four-role research workflow: Orchestrator -> Researcher -> Analyst -> Critic.

Every role is a plain function. Roles talk to each other only through the
Pydantic models below, so the data passed between them is easy to inspect.
"""
import json
import re
import urllib.parse
import urllib.request
from typing import Callable, List, Optional

from pydantic import BaseModel, Field


# ---------- Shared data (structured, passed between roles) ----------
class OrchestratorPlan(BaseModel):
    query: str
    topic: str                      # cleaned search term, e.g. "food delivery Nepal"
    use_sample: bool
    steps: List[str]


class Source(BaseModel):
    title: str
    url: str
    status: str                     # "fetched" | "failed" | "sample"
    note: str = ""


class Competitor(BaseModel):
    name: str
    description: str


class ResearchFindings(BaseModel):
    label: str                      # says clearly where the data came from
    facts: List[str]
    competitors: List[Competitor] = Field(default_factory=list)
    sources: List[Source]
    gaps: List[str] = Field(default_factory=list)


class BriefDraft(BaseModel):
    summary: str
    competitors: List[Competitor] = Field(max_length=2)   # assignment: up to two
    key_observations: List[str]
    sources_and_missing: List[str]


class CriticFeedback(BaseModel):
    approved: bool
    issues: List[str] = Field(default_factory=list)
    revision_request: Optional[str] = None


class RunState(BaseModel):
    plan: OrchestratorPlan
    findings: ResearchFindings
    draft_v1: BriefDraft
    feedback: CriticFeedback
    final: BriefDraft
    revisions_used: int


# ---------- Clearly labelled sample data (offline mode) ----------
SAMPLE_LABEL = "SAMPLE DATA - illustrative only, not verified or live"

def _sample_findings(topic: str) -> Optional[ResearchFindings]:
    t = topic.lower()
    if "food" in t and "nepal" in t:
        return ResearchFindings(
            label=SAMPLE_LABEL,
            facts=[
                "Food delivery in Nepal is concentrated in Kathmandu Valley and a few other cities.",
                "Mobile wallets and QR payments are widely used for online orders.",
                "Unstructured street addressing makes last-mile delivery harder.",
                "Platforms compete on delivery fees, discounts and restaurant coverage.",
            ],
            competitors=[
                Competitor(name="Foodmandu", description="Early local food-delivery platform."),
                Competitor(name="Pathao Food", description="Food delivery inside the Pathao app."),
            ],
            sources=[Source(title="Built-in sample dataset", url="(none)", status="sample",
                            note="Written by the app author as an example")],
            gaps=["No real market-size or market-share figures are included in the sample."],
        )
    return None   # no sample data for this topic


# ---------- Roles ----------
def run_orchestrator(query: str, use_sample: bool) -> OrchestratorPlan:
    topic = re.sub(r"^(please\s+)?(analy[sz]e|research|tell me about)\s+(the\s+)?", "",
                   query.strip().rstrip(".?!"), flags=re.I)
    topic = re.sub(r"\bmarket\b\s*(in|of)?", "", topic, flags=re.I).strip() or query.strip()
    return OrchestratorPlan(
        query=query, topic=topic, use_sample=use_sample,
        steps=["Researcher", "Analyst", "Critic", "Analyst (one revision if requested)"],
    )


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchBriefStudentApp/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _live_findings(plan: OrchestratorPlan, note: str = "") -> ResearchFindings:
    facts, sources, gaps, seen = [], [], [], set()
    terms = [plan.topic] + ([plan.query] if plan.query != plan.topic else [])
    try:
        hits = []
        for term in terms:                      # try the cleaned topic, then the raw query
            q = urllib.parse.quote(term)
            hits = _get_json("https://en.wikipedia.org/w/api.php?action=query&list=search"
                             f"&srsearch={q}&srlimit=3&format=json")["query"]["search"]
            if hits:
                break
        for hit in hits:
            title = hit["title"]
            if title in seen:
                continue
            seen.add(title)
            slug = urllib.parse.quote(title.replace(" ", "_"))
            url = "https://en.wikipedia.org/wiki/" + slug
            try:
                summ = _get_json("https://en.wikipedia.org/api/rest_v1/page/summary/" + slug)
                if summ.get("extract"):
                    facts.append(summ["extract"])
                    sources.append(Source(title=title, url=url, status="fetched"))
                else:
                    sources.append(Source(title=title, url=url, status="failed", note="empty page"))
            except Exception as e:
                sources.append(Source(title=title, url=url, status="failed", note=str(e)[:80]))
        if not hits:
            gaps.append("Wikipedia returned no results for this topic.")
    except Exception as e:
        sources.append(Source(title="Wikipedia search", url="https://en.wikipedia.org",
                              status="failed", note=str(e)[:80]))
    if note:
        gaps.append(note)
    gaps.append("Competitors, market size and market share were not found automatically; "
                "check company reports or news before relying on this brief.")
    return ResearchFindings(label="Live web search (Wikipedia)", facts=facts,
                            sources=sources, gaps=gaps)


def run_researcher(plan: OrchestratorPlan) -> ResearchFindings:
    if plan.use_sample:
        sample = _sample_findings(plan.topic)
        if sample:
            return sample
        return _live_findings(plan, "No sample data exists for this topic, so live search was used instead.")
    return _live_findings(plan)


def run_analyst(plan: OrchestratorPlan, findings: ResearchFindings,
                feedback: Optional[CriticFeedback] = None) -> BriefDraft:
    facts = findings.facts
    summary = (" ".join(facts[:2]) if facts else
               f"No usable information was found about {plan.topic}.")
    observations = facts[2:6] if len(facts) > 2 else facts[:]
    missing = [f"Source: {s.title} ({s.status})" for s in findings.sources if s.status != "failed"]
    missing += [f"Missing: {g}" for g in findings.gaps]
    if feedback and feedback.revision_request:       # the revision pass
        for s in findings.sources:
            if s.status == "failed":
                missing.append(f"Could not read: {s.title} ({s.note or 'failed'})")
        if not observations:
            observations = ["Not enough information was found to make observations."]
    return BriefDraft(summary=summary, competitors=findings.competitors[:2],
                      key_observations=observations, sources_and_missing=missing)


def run_critic(draft: BriefDraft, findings: ResearchFindings) -> CriticFeedback:
    issues = []
    text = " ".join(draft.sources_and_missing)
    for s in findings.sources:
        if s.status == "failed" and s.title not in text:
            issues.append(f"Failed source '{s.title}' is not listed under missing information.")
    if not draft.key_observations:
        issues.append("There are no key observations.")
    if findings.label.startswith("SAMPLE") and "sample" not in text.lower():
        issues.append("Sample data is not labelled in the sources section.")
    if issues:
        return CriticFeedback(approved=False, issues=issues, revision_request="; ".join(issues))
    return CriticFeedback(approved=True)


# ---------- Orchestrator: runs the whole sequence ----------
def run_workflow(query: str, use_sample: bool,
                 on_step: Callable[[str], None] = lambda msg: None) -> RunState:
    on_step("Orchestrator: planning the research")
    plan = run_orchestrator(query, use_sample)
    on_step("Researcher: collecting information")
    findings = run_researcher(plan)
    on_step("Analyst: writing the first draft")
    draft_v1 = run_analyst(plan, findings)
    on_step("Critic: reviewing the draft")
    feedback = run_critic(draft_v1, findings)
    final, revisions = draft_v1, 0
    if not feedback.approved:                         # at most ONE revision
        on_step("Analyst: revising after Critic feedback")
        final, revisions = run_analyst(plan, findings, feedback), 1
    return RunState(plan=plan, findings=findings, draft_v1=draft_v1,
                    feedback=feedback, final=final, revisions_used=revisions)