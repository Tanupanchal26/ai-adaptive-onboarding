import networkx as nx
from gap_logic import load_catalog
from semantic_engine import optimize_courses

# Prerequisite graph: edge A → B means "learn A before B"
_PREREQ_EDGES = [
    # Technical
    ("Python",           "Machine Learning"),
    ("Python",           "Data Analysis"),
    ("SQL",              "Data Analysis"),
    ("Statistics",       "Machine Learning"),
    ("JavaScript",       "React"),
    ("JavaScript",       "Node.js"),
    ("HTML",             "JavaScript"),
    ("CSS",              "JavaScript"),
    ("Docker",           "Kubernetes"),
    ("Git",              "Agile"),
    ("Data Analysis",    "Tableau"),
    ("Data Analysis",    "Power BI"),
    ("Python",           "Deep Learning"),
    ("Machine Learning", "Deep Learning"),
    ("AWS",              "Kubernetes"),
    # Non-technical
    ("Communication",    "Public Speaking"),
    ("Communication",    "Leadership"),
    ("Sales",            "Negotiation"),
    ("Sales",            "CRM"),
    ("Marketing",        "SEO"),
    ("Marketing",        "Content Marketing"),
    ("Marketing",        "Brand Management"),
    ("Excel",            "Financial Analysis"),
    ("Leadership",       "Strategy"),
    ("Leadership",       "Coaching"),
    ("Project Management", "Strategy"),
]


def _build_prereq_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_edges_from(_PREREQ_EDGES)
    return G


def _order_by_prerequisites(gaps: set) -> list:
    """Return gaps sorted by prerequisite dependencies via topological sort."""
    G = _build_prereq_graph()
    # Keep only nodes relevant to the current gaps
    subgraph_nodes = set(gaps)
    for skill in gaps:
        if skill in G:
            subgraph_nodes.update(nx.ancestors(G, skill))
    sub = G.subgraph(subgraph_nodes)
    topo = list(nx.topological_sort(sub))
    # Return only the actual gaps in topo order; append any not in graph at end
    ordered = [s for s in topo if s in gaps]
    ordered += [s for s in gaps if s not in ordered]
    return ordered


def build_learning_path(gaps: set) -> list:
    """
    Dependency-aware, efficiency-ranked learning pathway.

    Pipeline
    --------
    1. optimize_courses() runs greedy set-cover — returns the minimal
       non-redundant course set, each covering only *new* gaps.
    2. Topo-sort the selected courses so prerequisites come first:
       the course whose earliest-prerequisite gap has the lowest topo rank
       is placed first.
    3. Attach full catalog metadata and build the final pathway list.
    """
    if not gaps:
        return []

    ordered_gaps = _order_by_prerequisites(gaps)
    topo_rank    = {s: i for i, s in enumerate(ordered_gaps)}

    df       = load_catalog()
    catalog  = df.to_dict("records")
    id_map   = {row["title"]: row for _, row in df.iterrows()}

    # Greedy set-cover — already minimal and scored
    selected = optimize_courses(catalog, list(gaps))

    # Apply topo ordering: sort by the earliest prereq rank among covered gaps
    selected.sort(key=lambda x: (
        min((topo_rank.get(s, 99) for s in x["covers"]), default=99),
        -x["score"],
    ))

    seen_ids = set()
    pathway  = []
    for item in selected:
        row = id_map.get(item["name"])
        if row is None:
            continue
        rid = row["id"]
        if rid in seen_ids:
            continue
        seen_ids.add(rid)
        gaps_closed   = item["covers"]
        efficiency    = item["score"]
        hours         = row["duration"]
        diff          = row["difficulty"].title()
        # Rich decision-logic explanation
        why_parts = [
            f"Closes {len(gaps_closed)} gap(s): {', '.join(gaps_closed)}",
            f"Efficiency: {efficiency:.2f} gaps/hr",
            f"Selected because it maximizes skill coverage per hour invested",
        ]
        if len(gaps_closed) > 1:
            why_parts.append(f"Bundles {len(gaps_closed)} required skills into {hours}h — avoids separate courses")
        pathway.append({
            "id":         rid,
            "title":      row["title"],
            "duration":   hours,
            "difficulty": row["difficulty"],
            "skills":     row["skills"],
            "prereq":     row.get("prereq", []),
            "covers":     gaps_closed,
            "score":      efficiency,
            "why":        "  ·  ".join(why_parts[:2]),
            "why_detail": why_parts,
        })

    return pathway


def build_bonus_courses(gaps: set, candidate_skills: set, experience_years: int) -> list:
    bonus = []
    gaps_lower   = {g.lower() for g in gaps}
    skills_lower = {s.lower() for s in candidate_skills}
    seen_titles  = set()

    def add(title, duration, reason):
        if title not in seen_titles:
            seen_titles.add(title)
            bonus.append({"title": title, "duration": duration, "reason": reason})

    # ── Technical bonuses ──────────────────────────────────────────────────────────────
    if ("react" in gaps_lower or "javascript" in gaps_lower) and "typescript" not in skills_lower:
        add("TypeScript for Developers", 6,
            "Most React/JS roles require TypeScript — adds 20–40% more interview calls")
    if ("javascript" in skills_lower or "react" in skills_lower) and \
       "next.js" not in skills_lower and experience_years >= 2:
        add("Next.js App Router & SSR", 10,
            "High-demand full-stack framework — opens senior full-stack opportunities")
    if experience_years < 3 and "testing" not in skills_lower and \
       ("javascript" in skills_lower or "react" in skills_lower or "javascript" in gaps_lower):
        add("Testing with Jest & Cypress", 8,
            "Testing skills required for mid+ level roles")
    if "dsa" not in skills_lower and "problem solving" not in skills_lower and experience_years < 5 and \
       any(t in skills_lower | gaps_lower for t in ("python", "java", "javascript")):
        add("Data Structures & Algorithms", 12,
            "Required for product company & FAANG interviews")
    if experience_years >= 3 and "aws" not in skills_lower and "cloud" not in skills_lower and \
       any(t in skills_lower for t in ("python", "docker", "backend", "node.js")):
        add("AWS Cloud Practitioner", 8,
            "Cloud skills add significant compensation at senior levels")
    if ("docker" in skills_lower or "devops" in skills_lower) and \
       "kubernetes" not in skills_lower and experience_years >= 4:
        add("Kubernetes & Cloud Native", 10,
            "K8s is standard for production deployments")
    if experience_years >= 3 and "system design" not in skills_lower and \
       any(t in skills_lower for t in ("python", "java", "backend", "aws")):
        add("System Design & Architecture", 10,
            "Mandatory for senior/staff engineer interviews")

    # ── Non-technical bonuses ──────────────────────────────────────────────────────────
    is_sales_role    = any(t in skills_lower | gaps_lower for t in ("sales", "crm", "negotiation", "salesforce"))
    is_mkt_role      = any(t in skills_lower | gaps_lower for t in ("marketing", "seo", "content marketing", "brand management"))
    is_people_role   = any(t in skills_lower | gaps_lower for t in ("leadership", "hr", "coaching", "recruitment"))

    if is_sales_role and "crm" not in skills_lower:
        add("CRM & Salesforce Basics", 6,
            "CRM proficiency is expected in 80%+ of sales roles — boosts close rates")
    if is_sales_role and "negotiation" not in skills_lower:
        add("Sales & Negotiation", 4,
            "Structured negotiation frameworks directly improve deal conversion")
    if is_mkt_role and "seo" not in skills_lower:
        add("SEO & Content Marketing", 5,
            "SEO is a core digital marketing skill — expected in most marketing manager JDs")
    if is_mkt_role and "tableau" not in skills_lower and "power bi" not in skills_lower:
        add("Tableau for Data Viz", 6,
            "Data-driven marketing decisions require visualization tools")
    if is_people_role and "strategy" not in skills_lower and experience_years >= 3:
        add("Executive Leadership & Strategy", 8,
            "Strategy skills differentiate managers from individual contributors")
    if (is_sales_role or is_mkt_role) and "excel" not in skills_lower:
        add("Excel for Business", 4,
            "Excel is the baseline tool for sales reporting and marketing analytics")

    return bonus[:4]


def estimate_time(pathway: list) -> dict:
    """Return total, static baseline, saved hours, and efficiency %."""
    total        = sum(c["duration"] for c in pathway)
    static       = round(total * 1.67)
    saved        = static - total
    efficiency   = round((saved / static) * 100) if static else 0
    return {"total": total, "static": static, "saved": saved, "efficiency": efficiency}


def generate_ai_insight(
    from_role: str,
    to_role: str,
    matched: set,
    gaps: set,
    pathway: list,
    total_hours: int,
    hours_saved: int,
    readiness: int,
) -> dict:
    """
    Generate human-readable strengths / weaknesses / optimized-path narrative.
    Tries GPT-4o-mini first, falls back to LLaMA 3.2, then returns a
    deterministic template so the UI never breaks.
    """
    prompt = (
        f"You are an enterprise onboarding intelligence system. "
        f"A candidate is transitioning from '{from_role}' to '{to_role}'.\n"
        f"Matched skills: {', '.join(sorted(matched)) or 'none'}.\n"
        f"Skill gaps: {', '.join(sorted(gaps)) or 'none'}.\n"
        f"Optimized learning path ({total_hours}h, saves {hours_saved}h): "
        f"{', '.join(c['title'] for c in pathway)}.\n"
        f"Role readiness score: {readiness}%.\n\n"
        f"Return ONLY a JSON object with exactly three keys:\n"
        f'  "strengths": one sentence about what the candidate already does well,\n'
        f'  "weaknesses": one sentence about the most critical gaps to address,\n'
        f'  "path_insight": one sentence explaining why this specific learning path is optimal.\n'
        f"No markdown, no extra keys."
    )

    # ── Try GPT-4o-mini ───────────────────────────────────────────────────────
    try:
        from parser import _get_openai_key
        from openai import OpenAI
        import json
        key = _get_openai_key()
        if key:
            client = OpenAI(api_key=key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=200,
            )
            return json.loads(resp.choices[0].message.content)
    except Exception:
        pass

    # ── Try LLaMA 3.2 ─────────────────────────────────────────────────────────
    try:
        import json, urllib.request
        payload = json.dumps({"model": "llama3.2", "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = json.loads(r.read()).get("response", "")
        return json.loads(raw)
    except Exception:
        pass

    # ── Deterministic fallback ────────────────────────────────────────────────
    top_gap = sorted(gaps)[0] if gaps else "key skills"
    top_course = pathway[0]["title"] if pathway else "the recommended course"
    return {
        "strengths": (
            f"Strong foundation in {', '.join(sorted(matched)[:3]) or 'core competencies'} "
            f"provides a solid base for the {to_role} transition."
        ),
        "weaknesses": (
            f"Critical gap in {top_gap} is the highest-priority area to address "
            f"before taking on {to_role} responsibilities."
        ),
        "path_insight": (
            f"Starting with '{top_course}' maximizes efficiency by closing the most "
            f"impactful gaps first, cutting onboarding time by {hours_saved}h."
        ),
    }
