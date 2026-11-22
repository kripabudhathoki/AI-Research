"""Multi-agent market research workflow: Orchestrator -> Researcher -> Analyst -> Critic.

All roles pass typed Pydantic models. No API key is needed:
  * "sample"  mode reads the labelled starter directory in data/nepal_companies.json
  * "live"    mode searches Wikipedia (and DuckDuckGo as a fallback)
  * "auto"    mode tries the directory first, then live search
"""
import difflib
import json
import re
import urllib.parse
import urllib.request
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

DATA_FILE = Path(__file__).parent / "data" / "nepal_companies.json"
SAMPLE_LABEL = "SAMPLE DATA"
LIVE_LABEL = "LIVE WEB SEARCH"
NONE_LABEL = "NO DATA FOUND"
USER_AGENT = "AI-Research-StudentApp/1.0 (educational project; python-urllib)"
MAX_REVISIONS = 1

STOP = {"analyze", "analyse", "analysis", "research", "the", "a", "an", "of", "on", "about",
        "market", "industry", "sector", "in", "for", "and", "brief", "company", "companies",
        "pvt", "ltd", "limited", "private", "tell", "me", "what", "is", "nepali", "please"}


# ----------------------------------------------------------------- shared data models
class OrchestratorPlan(BaseModel):
    query: str
    topic: str
    mode: str
    steps: List[str] = Field(default_factory=list)


class Source(BaseModel):
    title: str
    url: str = ""
    kind: str = "web"  # "sample" or "web"


class ResearchFindings(BaseModel):
    topic: str
    data_source: str = NONE_LABEL
    matched_name: str = ""
    summary_text: str = ""
    facts: List[str] = Field(default_factory=list)
    competitors: List[str] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class BriefDraft(BaseModel):
    topic: str
    data_source: str
    summary: str
    competitors: List[str] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    revision: int = 0


class CriticFeedback(BaseModel):
    approved: bool
    revision_requested: bool = False
    codes: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)


class RunState(BaseModel):
    query: str
    plan: Optional[OrchestratorPlan] = None
    findings: Optional[ResearchFindings] = None
    draft: Optional[BriefDraft] = None
    feedback: Optional[CriticFeedback] = None
    final_feedback: Optional[CriticFeedback] = None
    final_brief: Optional[BriefDraft] = None
    revisions_used: int = 0
    run_date: str = ""
    log: List[str] = Field(default_factory=list)


# ----------------------------------------------------------------- text helpers
def _norm(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return " ".join(w for w in words if w not in STOP)


def _sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def clean_topic(query: str) -> str:
    q = re.sub(r"\s+", " ", query).strip().strip("?.! ")
    q = re.sub(r"^(please\s+)?(analy[sz]e|research|tell me about|what is|brief on|market research on)\s+", "", q, flags=re.I)
    q = re.sub(r"^the\s+", "", q, flags=re.I)
    return q.strip() or query.strip()


# ----------------------------------------------------------------- sample directory
@lru_cache(maxsize=1)
def load_directory() -> list:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def _score(q: str, key: str) -> float:
    if not q or not key:
        return 0.0
    if q == key:
        return 1.0
    qt, kt = set(q.split()), set(key.split())
    if (kt <= qt or qt <= kt) and len(min(q, key, key=len)) >= 4:
        return 0.9
    return difflib.SequenceMatcher(None, q, key).ratio()


def _entry_score(q: str, entry: dict) -> float:
    keys = [entry["name"]] + entry.get("aliases", [])
    return max(_score(q, _norm(k)) for k in keys)


def _keyword_match(topic: str):
    """Fallback: match words such as 'coffee', 'wallet' or 'hydro' against names, aliases and summaries."""
    toks = [t for t in _norm(topic).split() if len(t) >= 4 and t not in ("nepal", "nepali")]
    if not toks:
        return None
    best, best_hits = None, 0
    for entry in load_directory():
        hay = (entry["name"] + " " + " ".join(entry.get("aliases", [])) + " " + entry["summary"]).lower()
        hits = sum(1 for t in toks if t in hay)
        if hits > best_hits:
            best, best_hits = entry, hits
    return best if best_hits >= (len(toks) + 1) // 2 else None


def find_in_directory(topic: str, threshold: float = 0.78):
    q = _norm(topic)
    if not q or q == "nepal":
        return None, 0.0
    best, best_score = None, 0.0
    for entry in load_directory():
        s = _entry_score(q, entry)
        if s > best_score:
            best, best_score = entry, s
    if best_score >= threshold:
        return best, best_score
    kw = _keyword_match(topic)
    return (kw, 0.5) if kw else (None, best_score)


def suggestions(topic: str, n: int = 4) -> List[str]:
    q = _norm(topic)
    ranked = sorted(load_directory(), key=lambda e: _entry_score(q, e), reverse=True)
    return [e["name"] for e in ranked[:n]]


# ----------------------------------------------------------------- live search
def _http_json(url: str, timeout: int = 12) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        import requests  # installed with Streamlit; uses certifi, avoids SSL errors on macOS/Windows
    except ImportError:
        requests = None
    if requests is not None:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _wikipedia(query: str) -> List[dict]:
    params = {"action": "query", "generator": "search", "gsrsearch": query, "gsrlimit": "3",
              "prop": "extracts|info", "inprop": "url", "exintro": "1", "explaintext": "1",
              "exlimit": "max", "format": "json", "redirects": "1"}
    data = _http_json("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params))
    pages = (data.get("query") or {}).get("pages") or {}
    ordered = sorted(pages.values(), key=lambda p: p.get("index", 99))
    return [{"title": p.get("title", ""), "url": p.get("fullurl", ""), "extract": p.get("extract", "")}
            for p in ordered if p.get("extract")]


def _duckduckgo(query: str) -> Optional[dict]:
    params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
    data = _http_json("https://api.duckduckgo.com/?" + urllib.parse.urlencode(params))
    text = data.get("AbstractText") or ""
    if not text:
        return None
    return {"title": data.get("Heading") or query, "url": data.get("AbstractURL", ""), "extract": text}


def _relevant(page: dict, topic: str) -> bool:
    tokens = [t for t in _norm(topic).split() if t != "nepal" and len(t) > 2] or _norm(topic).split()
    hay = (page["title"] + " " + page["extract"][:500]).lower()
    return any(t in hay for t in tokens)


def _live_search(topic: str):
    errors, pages = [], []
    queries = [topic] + ([topic + " Nepal"] if "nepal" not in topic.lower() else [])
    for q in queries:
        try:
            pages = [p for p in _wikipedia(q) if _relevant(p, topic)]
        except Exception as exc:  # network down, blocked, timeout...
            errors.append(f"Wikipedia search failed ({type(exc).__name__}: {exc})")
            break
        if pages:
            break
    if not pages:
        try:
            dd = _duckduckgo(topic)
            if dd and _relevant(dd, topic):
                pages = [dd]
        except Exception as exc:
            errors.append(f"DuckDuckGo search failed ({type(exc).__name__}: {exc})")
    if not pages:
        return None, errors
    main = pages[0]
    facts = _sentences(main["extract"])[:8]
    for p in pages[1:3]:
        first = _sentences(p["extract"])[:1]
        if first:
            facts.append(f"{p['title']}: {first[0]}")
    return ResearchFindings(
        topic=topic, data_source=LIVE_LABEL, matched_name=main["title"],
        summary_text=" ".join(facts[:2]), facts=facts, competitors=[],
        sources=[Source(title=p["title"], url=p["url"], kind="web") for p in pages[:3]],
        errors=errors), errors


# ----------------------------------------------------------------- the four roles
def run_orchestrator(query: str, mode: str) -> OrchestratorPlan:
    if not query or not query.strip():
        raise ValueError("Please enter a company or industry.")
    if mode not in ("auto", "sample", "live"):
        mode = "auto"
    return OrchestratorPlan(
        query=query.strip(), topic=clean_topic(query), mode=mode,
        steps=["Researcher gathers findings", "Analyst writes the brief",
               "Critic reviews (max 1 revision)"])


def run_researcher(plan: OrchestratorPlan) -> ResearchFindings:
    errors: List[str] = []
    if plan.mode in ("auto", "sample"):
        entry, _ = find_in_directory(plan.topic)
        if entry:
            return ResearchFindings(
                topic=plan.topic, data_source=SAMPLE_LABEL, matched_name=entry["name"],
                summary_text=entry["summary"], facts=list(entry["observations"]),
                competitors=list(entry.get("competitors", [])),
                sources=[Source(title="Starter directory (data/nepal_companies.json) - sample data, "
                                      "not a live source", kind="sample")])
        if plan.mode == "sample":
            errors.append(f"'{plan.topic}' is not in the sample directory.")
    if plan.mode in ("auto", "live"):
        found, errs = _live_search(plan.topic)
        errors += errs
        if found:
            return found
        if not errs:
            errors.append(f"Live search returned nothing relevant for '{plan.topic}'.")
    return ResearchFindings(topic=plan.topic, data_source=NONE_LABEL, errors=errors)


def _source_lines(findings: ResearchFindings) -> List[str]:
    return [f"{s.title} - {s.url}" if s.url else s.title for s in findings.sources]


def run_analyst_draft(findings: ResearchFindings) -> BriefDraft:
    if findings.data_source == NONE_LABEL:
        return BriefDraft(
            topic=findings.topic, data_source=NONE_LABEL,
            summary=f"No information was found for '{findings.topic}'.",
            missing=list(findings.errors) + [
                "Try another spelling, a more specific name, or a company from the sample directory."])
    if findings.data_source == SAMPLE_LABEL:
        return BriefDraft(
            topic=findings.matched_name or findings.topic, data_source=SAMPLE_LABEL,
            summary=findings.summary_text, competitors=findings.competitors[:2],
            observations=findings.facts[:4], sources=_source_lines(findings),
            missing=["No live sources were consulted; facts are general knowledge and unverified.",
                     "No financial figures (revenue, profit, market share) are included."])
    return BriefDraft(
        topic=findings.matched_name or findings.topic, data_source=LIVE_LABEL,
        summary=" ".join(findings.facts[:2]), competitors=findings.competitors[:2],
        observations=findings.facts[2:6], sources=_source_lines(findings),
        missing=["Financial figures (revenue, profit, market share) are not in the sources."])


def run_critic(draft: BriefDraft, findings: ResearchFindings, allow_revision: bool = True) -> CriticFeedback:
    codes, issues = [], []
    has_data = findings.data_source != NONE_LABEL
    if has_data and len(draft.summary) < 40 and findings.facts:
        codes.append("summary_short"); issues.append("Summary is too short; use more of the findings.")
    if len(draft.competitors) > 2:
        codes.append("too_many_competitors"); issues.append("More than two competitors listed.")
    if has_data and not draft.competitors and not any("competitor" in m.lower() for m in draft.missing):
        codes.append("competitor_gap"); issues.append("No competitors listed and the gap is not disclosed.")
    wants_revision = bool(codes) and allow_revision
    return CriticFeedback(approved=not codes, revision_requested=wants_revision, codes=codes, issues=issues)


def run_analyst_revision(draft: BriefDraft, feedback: CriticFeedback, findings: ResearchFindings) -> BriefDraft:
    new = draft.model_copy(deep=True) if hasattr(draft, "model_copy") else draft
    new.revision = draft.revision + 1
    if "summary_short" in feedback.codes:
        new.summary = " ".join(findings.facts[:3]) or new.summary
    if "too_many_competitors" in feedback.codes:
        new.competitors = new.competitors[:2]
    if "competitor_gap" in feedback.codes:
        new.missing = new.missing + ["Competitors could not be identified from the available sources."]
    return new


def run_workflow(query: str, mode: str = "auto") -> RunState:
    state = RunState(query=query, run_date=date.today().isoformat())
    state.plan = run_orchestrator(query, mode)
    state.log.append(f"Orchestrator: topic='{state.plan.topic}', mode={state.plan.mode}")
    state.findings = run_researcher(state.plan)
    state.log.append(f"Researcher: {state.findings.data_source}, {len(state.findings.facts)} facts")
    state.draft = run_analyst_draft(state.findings)
    state.log.append("Analyst: first draft written")
    state.feedback = run_critic(state.draft, state.findings, allow_revision=True)
    state.log.append("Critic: " + ("approved" if state.feedback.approved else "; ".join(state.feedback.issues)))
    state.final_brief = state.draft
    if state.feedback.revision_requested and state.revisions_used < MAX_REVISIONS:
        state.final_brief = run_analyst_revision(state.draft, state.feedback, state.findings)
        state.revisions_used += 1
        state.final_feedback = run_critic(state.final_brief, state.findings, allow_revision=False)
        state.log.append("Analyst: revision applied (1 of 1)")
    return state


def brief_to_markdown(state: RunState) -> str:
    b = state.final_brief
    lines = [f"# Research Brief: {b.topic}", "",
             f"- Query: {state.query}", f"- Data source: {b.data_source}",
             f"- Revisions used: {state.revisions_used} of {MAX_REVISIONS}", f"- Date: {state.run_date}", "",
             "## Summary", b.summary, "", "## Competitors (up to 2)"]
    lines += [f"- {c}" for c in b.competitors] or ["- None identified"]
    lines += ["", "## Key observations"]
    lines += [f"{i}. {o}" for i, o in enumerate(b.observations, 1)] or ["- None available"]
    lines += ["", "## Sources and missing information", "**Sources**"]
    lines += [f"- {s}" for s in b.sources] or ["- None"]
    lines += ["", "**Missing information**"] + [f"- {m}" for m in b.missing]
    return "\n".join(lines) + "\n"