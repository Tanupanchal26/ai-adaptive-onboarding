import networkx as nx
from gap_logic import load_catalog
from semantic_engine import optimize_courses

# Prerequisite graph: edge A → B means "learn A before B"
_PREREQ_EDGES = [
    ("Python",      "Machine Learning"),
    ("Python",      "Data Analysis"),
    ("SQL",         "Data Analysis"),
    ("Statistics",  "Machine Learning"),
    ("JavaScript",  "React"),
    ("JavaScript",  "Node.js"),
    ("HTML",        "JavaScript"),
    ("CSS",         "JavaScript"),
    ("Docker",      "Kubernetes"),
    ("Git",         "Agile"),
    ("Data Analysis", "Tableau"),
    ("Data Analysis", "Power BI"),
    ("Python",      "Deep Learning"),
    ("Machine Learning", "Deep Learning"),
    ("AWS",         "Kubernetes"),
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

    Pipeline:
    1. Score all catalog courses via optimize_courses (score = covered_gaps / duration)
    2. Sort by score DESC, topo-order as tiebreak
    3. Deduplicate by course id
    4. Return structured list with 'covers' and 'score' on every item
    """
    if not gaps:
        return []

    ordered_gaps = _order_by_prerequisites(gaps)
    topo_rank    = {s: i for i, s in enumerate(ordered_gaps)}

    # Load catalog as list-of-dicts for optimize_courses
    df = load_catalog()
    catalog = df.to_dict("records")

    # Score and sort via shared engine
    scored = optimize_courses(catalog, list(gaps))

    # Topo tiebreak: courses covering earlier-prerequisite gaps rank higher
    scored.sort(key=lambda x: (
        -x["score"],
        min((topo_rank.get(s, 99) for s in x["covers"]), default=99)
    ))

    # Build id → full row lookup for metadata
    id_lookup = {row["id"]: row for _, row in df.iterrows()}

    seen_ids = set()
    pathway  = []
    for item in scored:
        # match back to catalog row by name
        row = next(
            (r for r in id_lookup.values() if r["title"] == item["name"]),
            None
        )
        if row is None:
            continue
        rid = row["id"]
        if rid in seen_ids:
            continue
        seen_ids.add(rid)
        pathway.append({
            "id":         rid,
            "title":      row["title"],
            "duration":   row["duration"],
            "difficulty": row["difficulty"],
            "skills":     row["skills"],
            "prereq":     row.get("prereq", []),
            "covers":     item["covers"],
            "score":      item["score"],
            "why":        f"Covers {len(item['covers'])} gap(s): {', '.join(item['covers'])}  ·  efficiency {item['score']:.2f} gaps/hr",
        })

    return pathway


def build_bonus_courses(gaps: set, candidate_skills: set, experience_years: int) -> list:
    """
    Suggest high-value bonus courses based on:
    - What gaps exist (career-adjacent skills)
    - Experience level (junior vs senior recommendations)
    Returns list of bonus dicts with title, duration, reason.
    """
    bonus = []
    gaps_lower    = {g.lower() for g in gaps}
    skills_lower  = {s.lower() for s in candidate_skills}
    seen_titles   = set()

    def add(title, duration, reason):
        if title not in seen_titles:
            seen_titles.add(title)
            bonus.append({"title": title, "duration": duration, "reason": reason})

    # Frontend gap → suggest TypeScript (most React/JS jobs require it)
    if ("react" in gaps_lower or "javascript" in gaps_lower) and "typescript" not in skills_lower:
        add("TypeScript for Developers", 6,
            "Most React/JS roles in 2025 require TypeScript — adds 20–40% more interview calls")

    # Has JS/React but no Next.js and 2+ years experience
    if ("javascript" in skills_lower or "react" in skills_lower) and \
       "next.js" not in skills_lower and experience_years >= 2:
        add("Next.js App Router & SSR", 10,
            "High-demand full-stack framework — opens ₹15–35+ LPA opportunities")

    # Junior dev without testing skills
    if experience_years < 3 and "testing" not in skills_lower and \
       ("javascript" in skills_lower or "react" in skills_lower or "javascript" in gaps_lower):
        add("Testing with Jest & Cypress", 8,
            "Testing = senior roles & better packages — most companies require it for mid+ level")

    # Any dev role without DSA
    if "dsa" not in skills_lower and "problem solving" not in skills_lower and \
       experience_years < 5:
        add("Data Structures & Algorithms", 12,
            "Required for FAANG & product company interviews regardless of stack")

    # Backend gap or Node.js missing for full-stack roles
    if ("backend" in gaps_lower or "node.js" in gaps_lower or "rest api" in gaps_lower) and \
       "node.js" not in skills_lower:
        add("REST APIs & Node.js", 7,
            "Full-stack capability — doubles job options vs pure frontend")

    # Cloud gap for senior engineers
    if experience_years >= 3 and "aws" not in skills_lower and "cloud" not in skills_lower:
        add("AWS Cloud Practitioner", 8,
            "Cloud skills add ₹3–8 LPA to compensation at senior levels")

    # Docker without Kubernetes for 4+ years experience
    if ("docker" in skills_lower or "devops" in skills_lower) and \
       "kubernetes" not in skills_lower and experience_years >= 4:
        add("Kubernetes & Cloud Native", 10,
            "K8s is the standard for production deployments — required for DevOps/SRE roles")

    # System design for senior candidates
    if experience_years >= 3 and "system design" not in skills_lower:
        add("System Design & Architecture", 10,
            "System design rounds are mandatory for senior/staff engineer interviews")

    return bonus[:4]  # cap at 4 bonus courses to avoid overwhelming


def estimate_time(pathway: list) -> dict:
    """Return total, static baseline, saved hours, and efficiency %."""
    total        = sum(c["duration"] for c in pathway)
    static       = round(total * 1.67)
    saved        = static - total
    efficiency   = round((saved / static) * 100) if static else 0
    return {"total": total, "static": static, "saved": saved, "efficiency": efficiency}
