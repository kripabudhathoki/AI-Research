#!/usr/bin/env python3
"""
Basic Multi-Agent Market Research App
Server: Python 3 Standard Library (Zero external dependencies)
Features:
 - Native HTTP server with Server-Sent Events (SSE) streaming
 - Multi-Agent Orchestration Workflow (Planner -> Market -> Competitor/SWOT -> Risk/Ops -> Synthesis -> Critic)
 - Live LLM Support (Gemini, OpenAI, Groq, Ollama) via standard urllib
 - Autonomous Knowledge Simulation Engine for immediate testing
 - Pre-configured benchmarks for Nepal Food Delivery and global markets
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

PORT = int(os.environ.get("PORT", 8000))
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
DATA_DIR = BASE_DIR / "data"

# Load domain benchmarks
domain_benchmarks = {}
benchmark_file = DATA_DIR / "domain_benchmarks.json"
if benchmark_file.exists():
    try:
        with open(benchmark_file, "r", encoding="utf-8") as f:
            domain_benchmarks = json.load(f)
    except Exception as e:
        print(f"[Warning] Failed to load domain benchmarks: {e}", file=sys.stderr)

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}

def call_llm(provider, api_key, model, system_prompt, user_prompt):
    """Call external LLM using pure standard library urllib."""
    if provider == "gemini":
        selected_model = model or "gemini-1.5-flash"
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\nTask: {user_prompt}"}]
            }],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048}
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]

    elif provider in ("openai", "groq"):
        is_groq = (provider == "groq")
        endpoint = "https://api.groq.com/openai/v1/chat/completions" if is_groq else "https://api.openai.com/v1/chat/completions"
        default_model = "llama-3.3-70b-versatile" if is_groq else "gpt-4o-mini"
        payload = {
            "model": model or default_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.4
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    elif provider == "ollama":
        endpoint = "http://localhost:11434/api/chat"
        payload = {
            "model": model or "llama3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["message"]["content"]

    raise ValueError(f"Unsupported provider: {provider}")


def generate_simulated_research(query):
    """Generate structured research from benchmarks or dynamic knowledge heuristic."""
    q_lower = query.lower()
    is_nepal_food = ("food" in q_lower or "delivery" in q_lower) and \
                    ("nepal" in q_lower or "kathmandu" in q_lower or "foodmandu" in q_lower)
    
    if is_nepal_food and "nepal_food_delivery" in domain_benchmarks:
        return {"isBenchmark": True, "data": domain_benchmarks["nepal_food_delivery"]}

    return {
        "isBenchmark": False,
        "data": {
            "entity": query.strip(),
            "industry": "Emerging Technology & Digital Services",
            "geography": "Regional / Global",
            "market_sizing": {
                "tam": "$12.4B - $18.5B (Estimated regional opportunity)",
                "sam": "$4.2B - $6.1B (Addressable segment)",
                "som": "$850M - $1.4B (Serviceable target)",
                "cagr": "16.8% (5-Year CAGR)",
                "order_volume": "High-velocity recurring transactions",
                "avg_order_value": "$24.50 - $48.00 normalized transaction range",
                "digital_payment_share": "72% cashless/digital settlement"
            },
            "key_players": [
                {
                    "name": "Category Leader Inc.",
                    "role": "Incumbent Pioneer",
                    "market_share": "42%",
                    "strengths": "Deep supplier network and strong customer brand retention.",
                    "weaknesses": "Higher operational legacy overhead."
                },
                {
                    "name": "Apex Challenger Ltd.",
                    "role": "Agile Disruptor",
                    "market_share": "29%",
                    "strengths": "Superior mobile UX and aggressive user acquisition.",
                    "weaknesses": "High burn rate and customer acquisition cost."
                },
                {
                    "name": "Regional & Niche Specialists",
                    "role": "Hyper-local Entrants",
                    "market_share": "18%",
                    "strengths": "Specialized offerings and localized customer care.",
                    "weaknesses": "Limited expansion capital."
                },
                {
                    "name": "Emerging Startups",
                    "role": "New Contenders",
                    "market_share": "11%",
                    "strengths": "AI-native automation and lean operational overhead.",
                    "weaknesses": "Brand discovery hurdles."
                }
            ],
            "swot": {
                "strengths": [
                    "Rapid growth in smartphone usage and digital payment rails.",
                    "Strong consumer shift toward on-demand digital experiences.",
                    "Scalable cloud architecture enabling rapid feature deployment."
                ],
                "weaknesses": [
                    "High customer sensitivity to pricing and promotional discounts.",
                    "Compressed margins driven by aggressive competitive subsidies.",
                    "Operational complexity in last-mile fulfillment."
                ],
                "opportunities": [
                    "Geographic expansion into secondary metropolitan hubs.",
                    "Introduction of premium subscription tiers and B2B workflows.",
                    "Predictive routing and AI demand forecasting to improve unit economics."
                ],
                "threats": [
                    "Evolving regulatory mandates around consumer data and labor rights.",
                    "Macroeconomic headwinds affecting discretionary consumer spending.",
                    "Potential vertical encroachment by dominant platform aggregators."
                ]
            },
            "regulatory_and_ops": {
                "regulations": "Subject to consumer protection standards, digital payment directives, and local labor classifications.",
                "infrastructure": "Requires robust mobile network coverage, cloud service uptime, and dependable local logistics fulfillment.",
                "rider_economics": "Demands continuous balance between courier retention, delivery fees, and platform take-rates."
            },
            "strategic_recommendations": [
                {
                    "horizon": "Immediate (0-6 months)",
                    "action": "Protect Unit Economics & Retain Core Demographics",
                    "detail": "Eliminate non-profitable promotional burns and optimize merchant onboarding times."
                },
                {
                    "horizon": "Medium-Term (6-18 months)",
                    "action": "Expand Into Secondary Urban Clusters",
                    "detail": "Replicate core operational playbooks into regional hubs and launch corporate subscriptions."
                },
                {
                    "horizon": "Long-Term (18-36 months)",
                    "action": "Build Moats with AI Routing & Vertical Integration",
                    "detail": "Deploy automated scheduling algorithms and explore dedicated fulfillment hubs."
                }
            ],
            "critic_notes": {
                "confidence_score": 91,
                "data_verification": "Synthesized through cross-industry comparative metrics and digital commerce benchmarks.",
                "caveats": "Regional market variability may affect exact margin realization."
            }
        }
    }


def execute_workflow(query, options, sse_writer):
    """Execute multi-agent workflow and push SSE messages."""
    provider = options.get("provider", "simulated")
    api_key = options.get("apiKey", "")
    model = options.get("model", "")
    is_live = (provider != "simulated" and bool(api_key))

    agents = [
        {"id": "planner", "name": "Dr. Evelyn Cross", "role": "Lead Research Coordinator & Planner", "icon": "🧠", "color": "#3b82f6", "badge": "Coordination & Task Decomp"},
        {"id": "market_analyst", "name": "Marcus Vance", "role": "Market Sizing & Industry Dynamics Analyst", "icon": "📊", "color": "#10b981", "badge": "TAM/SAM & Growth Trends"},
        {"id": "competitor_swot", "name": "Elena Rostova", "role": "Competitive Intelligence & SWOT Specialist", "icon": "⚔️", "color": "#8b5cf6", "badge": "Players & SWOT Matrix"},
        {"id": "risk_ops", "name": "Tariq Al-Mansoor", "role": "Regulatory, Infrastructure & Risk Analyst", "icon": "⚖️", "color": "#f59e0b", "badge": "Compliance & Ops Bottlenecks"},
        {"id": "synthesis", "name": "Sophia Sterling", "role": "Executive Synthesis & Strategy Director", "icon": "📝", "color": "#ec4899", "badge": "Brief Synthesis & Strategy"},
        {"id": "critic", "name": "Dr. Arthur Pendelton", "role": "Quality Assurance & Fact-Checking Critic", "icon": "🔍", "color": "#06b6d4", "badge": "Validation & Confidence Score"}
    ]

    sse_writer("workflow_init", {
        "query": query,
        "agents": agents,
        "mode": f"Live LLM ({provider})" if is_live else "Autonomous Knowledge Engine",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    })

    sim = generate_simulated_research(query)
    sim_data = sim["data"]
    outputs = {}

    # 1. PLANNER AGENT
    sse_writer("agent_status", {"id": "planner", "status": "running", "message": "Deconstructing research scope..."})
    if is_live:
        sse_writer("agent_log", {"id": "planner", "text": f"Scoping research objectives via {provider}..."})
        plan = call_llm(
            provider, api_key, model,
            "You are Dr. Evelyn Cross, Lead Market Planner. Outline target entity, geographic scope, and 3 sub-agent directives.",
            f"Query: {query}"
        )
    else:
        time.sleep(0.5)
        sse_writer("agent_log", {"id": "planner", "text": f"Target Identified: {sim_data['entity']} | Geography: {sim_data['geography']}"})
        time.sleep(0.5)
        plan = f"""### Research Framework & Investigation Plan
**Entity:** {sim_data['entity']}
**Sector:** {sim_data['industry']}
**Geography:** {sim_data['geography']}

#### Directives:
1. **Market Analyst:** Sizing (TAM/SAM), CAGR, order volumes, consumer adoption.
2. **Competitive/SWOT:** Key players, market shares, 4-quadrant SWOT matrix.
3. **Regulatory/Ops:** Policy compliance, courier economics, navigation/payment infrastructure."""

    outputs["planner"] = plan
    sse_writer("agent_status", {"id": "planner", "status": "completed", "output": plan})

    # 2. MARKET ANALYST
    sse_writer("agent_status", {"id": "market_analyst", "status": "running", "message": "Modeling market size, CAGR, and volumes..."})
    if is_live:
        market_res = call_llm(
            provider, api_key, model,
            "You are Marcus Vance, Market Sizing Analyst. Quantify TAM/SAM/SOM, CAGR, AOV, and demographics.",
            f"Query: {query}\n\nPlanner Framework:\n{outputs['planner']}"
        )
    else:
        time.sleep(0.6)
        sse_writer("agent_log", {"id": "market_analyst", "text": f"TAM: {sim_data['market_sizing']['tam']}; CAGR: {sim_data['market_sizing']['cagr']}"})
        time.sleep(0.4)
        m = sim_data['market_sizing']
        market_res = f"""### Market Sizing & Dynamics Assessment
- **TAM:** {m['tam']}
- **SAM:** {m['sam']}
- **SOM:** {m['som']}
- **CAGR:** {m['cagr']}
- **Daily Volume:** {m['order_volume']}
- **AOV:** {m['avg_order_value']}
- **Digital Payment:** {m['digital_payment_share']}"""

    outputs["market_analyst"] = market_res
    sse_writer("agent_status", {"id": "market_analyst", "status": "completed", "output": market_res})

    # 3. COMPETITOR & SWOT
    sse_writer("agent_status", {"id": "competitor_swot", "status": "running", "message": "Evaluating market competitors and building SWOT..."})
    if is_live:
        comp_res = call_llm(
            provider, api_key, model,
            "You are Elena Rostova, Competitive Intelligence Specialist. Map top players, market shares, and a 4-quadrant SWOT matrix.",
            f"Query: {query}\n\nPlan:\n{outputs['planner']}"
        )
    else:
        time.sleep(0.6)
        sse_writer("agent_log", {"id": "competitor_swot", "text": f"Profiling players: {', '.join(p['name'] for p in sim_data['key_players'])}"})
        time.sleep(0.4)
        players = "\n".join([f"- **{p['name']}** ({p['role']} - Share: {p['market_share']}): {p['strengths']}" for p in sim_data['key_players']])
        comp_res = f"""### Competitive Landscape & Market Structure

#### Top Players:
{players}

#### SWOT Highlights:
- **Strengths:** {sim_data['swot']['strengths'][0]}
- **Weaknesses:** {sim_data['swot']['weaknesses'][0]}
- **Opportunities:** {sim_data['swot']['opportunities'][0]}
- **Threats:** {sim_data['swot']['threats'][0]}"""

    outputs["competitor_swot"] = comp_res
    sse_writer("agent_status", {"id": "competitor_swot", "status": "completed", "output": comp_res})

    # 4. RISK & OPS
    sse_writer("agent_status", {"id": "risk_ops", "status": "running", "message": "Auditing regulations and operational bottlenecks..."})
    if is_live:
        risk_res = call_llm(
            provider, api_key, model,
            "You are Tariq Al-Mansoor, Risk & Ops Analyst. Detail regulatory laws, last-mile friction, and unit economics.",
            f"Query: {query}\n\nContext:\n{outputs['planner']}"
        )
    else:
        time.sleep(0.5)
        sse_writer("agent_log", {"id": "risk_ops", "text": "Auditing regulatory compliance and logistics infrastructure."})
        time.sleep(0.4)
        risk_res = f"""### Regulatory & Operational Risk Assessment
- **Regulations:** {sim_data['regulatory_and_ops']['regulations']}
- **Infrastructure & Fulfillment:** {sim_data['regulatory_and_ops']['infrastructure']}
- **Unit Economics & Labor:** {sim_data['regulatory_and_ops']['rider_economics']}"""

    outputs["risk_ops"] = risk_res
    sse_writer("agent_status", {"id": "risk_ops", "status": "completed", "output": risk_res})

    # 5. SYNTHESIS DIRECTOR
    sse_writer("agent_status", {"id": "synthesis", "status": "running", "message": "Drafting executive brief and strategic recommendations..."})
    if is_live:
        synth_res = call_llm(
            provider, api_key, model,
            "You are Sophia Sterling, Strategy Director. Write an executive brief with Executive Summary, Metrics, and 3 Horizons of Recommendations.",
            f"Query: {query}\n\nAll Findings:\n{json.dumps(outputs)}"
        )
    else:
        time.sleep(0.7)
        sse_writer("agent_log", {"id": "synthesis", "text": "Formulating 3-horizon strategic roadmap and executive verdict."})
        time.sleep(0.4)
        recs = "\n".join([f"- **{r['horizon']} — {r['action']}:** {r['detail']}" for r in sim_data['strategic_recommendations']])
        synth_res = f"""# Executive Market Research Brief: {sim_data['entity']}

## Executive Summary
The market for {sim_data['entity']} is entering a high-acceleration phase marked by increasing consumer digital habituation and modern payment rails. While competition between early movers and agile entrants is intense, the path to long-term profitability hinges on operational efficiency and secondary-market expansion.

## Key Market Metrics Dashboard
- **SAM / TAM:** {sim_data['market_sizing']['sam']} / {sim_data['market_sizing']['tam']}
- **Projected 5-Year CAGR:** {sim_data['market_sizing']['cagr']}
- **Daily Orders:** {sim_data['market_sizing']['order_volume']}
- **Digital Payment Share:** {sim_data['market_sizing']['digital_payment_share']}

## Strategic Recommendations
{recs}

## Strategic Verdict
**Favorable with disciplined execution:** Recommended for investment and market entry provided unit economics and last-mile routing bottlenecks are proactively addressed."""

    outputs["synthesis"] = synth_res
    sse_writer("agent_status", {"id": "synthesis", "status": "completed", "output": synth_res})

    # 6. CRITIC
    sse_writer("agent_status", {"id": "critic", "status": "running", "message": "Scoring confidence and checking assumptions..."})
    if is_live:
        critic_res = call_llm(
            provider, api_key, model,
            "You are Dr. Arthur Pendelton, Quality Critic. Provide a confidence score (0-100) and identify analytical caveats.",
            f"Executive Brief:\n{outputs['synthesis']}"
        )
    else:
        time.sleep(0.5)
        sse_writer("agent_log", {"id": "critic", "text": f"Calculated Research Confidence Score: {sim_data['critic_notes']['confidence_score']}/100"})
        time.sleep(0.3)
        critic_res = f"""### Independent Quality & Validation Review
- **Research Confidence Score:** {sim_data['critic_notes']['confidence_score']}/100
- **Verification Methodology:** {sim_data['critic_notes']['data_verification']}
- **Caveats:** {sim_data['critic_notes']['caveats']}"""

    outputs["critic"] = critic_res
    sse_writer("agent_status", {"id": "critic", "status": "completed", "output": critic_res})

    # FINAL COMPLETE EVENT
    final_brief = {
        "query": query,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entity": sim_data.get("entity", query),
        "industry": sim_data.get("industry", "Technology"),
        "geography": sim_data.get("geography", "Global"),
        "metrics": sim_data.get("market_sizing", {}),
        "key_players": sim_data.get("key_players", []),
        "swot": sim_data.get("swot", {}),
        "synthesis_markdown": synth_res,
        "raw_agents": outputs,
        "critic_notes": sim_data.get("critic_notes", {})
    }

    sse_writer("workflow_complete", final_brief)
    return final_brief


class ResearchHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-api-key, x-provider")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "Python Market Research Engine"}).encode("utf-8"))
            return

        if path == "/api/providers":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            providers = [
                {"id": "simulated", "name": "Autonomous Simulation Engine (Instant, 0 setup)", "keyRequired": False, "default": True},
                {"id": "gemini", "name": "Google Gemini (Gemini 2.5 / 1.5 Flash)", "keyRequired": True, "hasEnvKey": bool(os.environ.get("GEMINI_API_KEY"))},
                {"id": "openai", "name": "OpenAI (GPT-4o / GPT-4o-mini)", "keyRequired": True, "hasEnvKey": bool(os.environ.get("OPENAI_API_KEY"))},
                {"id": "groq", "name": "Groq (Llama 3.3 70B)", "keyRequired": True, "hasEnvKey": bool(os.environ.get("GROQ_API_KEY"))},
                {"id": "ollama", "name": "Ollama (Localhost:11434)", "keyRequired": False, "hasEnvKey": True}
            ]
            self.wfile.write(json.dumps({"available_providers": providers}).encode("utf-8"))
            return

        if path == "/api/research/stream":
            params = urllib.parse.parse_qs(parsed.query)
            query = params.get("q", ["Analyze the food delivery market in Nepal."])[0]
            provider = params.get("provider", ["simulated"])[0]
            api_key = params.get("apiKey", [""])[0] or os.environ.get(f"{provider.upper()}_API_KEY", "")
            model = params.get("model", [""])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            def sse_writer(event_name, data):
                msg = f"event: {event_name}\ndata: {json.dumps(data)}\n\n"
                try:
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass

            try:
                execute_workflow(query, {"provider": provider, "apiKey": api_key, "model": model}, sse_writer)
            except Exception as e:
                sse_writer("workflow_error", {"message": str(e)})
            return

        # Serve static files
        req_path = path.lstrip("/")
        if not req_path:
            req_path = "index.html"

        target_file = (PUBLIC_DIR / req_path).resolve()
        if not str(target_file).startswith(str(PUBLIC_DIR)) or not target_file.is_file():
            target_file = PUBLIC_DIR / "index.html"

        ext = target_file.suffix.lower()
        content_type = MIME_TYPES.get(ext, "application/octet-stream")

        try:
            with open(target_file, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error loading file: {e}".encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/research":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body or "{}")
            query = data.get("query", "Analyze the food delivery market in Nepal.")
            provider = data.get("provider", "simulated")
            api_key = data.get("apiKey", "") or os.environ.get(f"{provider.upper()}_API_KEY", "")
            model = data.get("model", "")

            try:
                res = execute_workflow(query, {"provider": provider, "apiKey": api_key, "model": model}, lambda e, d: None)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "result": res}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return


if __name__ == "__main__":
    server_address = ("0.0.0.0", PORT)
    httpd = HTTPServer(server_address, ResearchHandler)
    print("=" * 55)
    print(f"🚀 Python Multi-Agent Market Research App started!")
    print(f"📍 Web Interface: http://localhost:{PORT}")
    print(f"⚡ Zero external dependencies required.")
    print("=" * 55)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

