from gap_logic import load_catalog


def build_learning_path(gaps: set) -> list:
    """
    For each gap skill, find matching courses from catalog.
    Deduplicate, sort beginner → intermediate → advanced.
    Returns ordered list with 'why' explanation per course.
    """
    if not gaps:
        return []

    df = load_catalog().sort_values("difficulty_rank")
    gap_lower = {s.lower(): s for s in gaps}
    seen_ids = set()
    pathway = []

    for _, course in df.iterrows():
        course_skills_lower = {s.lower() for s in course["skills"]}
        covering = [gap_lower[s] for s in course_skills_lower if s in gap_lower]

        if covering and course["id"] not in seen_ids:
            seen_ids.add(course["id"])
            pathway.append({
                "id":         course["id"],
                "title":      course["title"],
                "duration":   course["duration"],
                "difficulty": course["difficulty"],
                "skills":     course["skills"],
                "prereq":     course.get("prereq", []),
                "why":        f"Covers your gap: {', '.join(covering)}"
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
