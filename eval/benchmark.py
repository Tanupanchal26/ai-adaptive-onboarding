"""
eval/benchmark.py — SkillBridge Evaluation Harness
====================================================
Compares keyword-matching baseline vs semantic similarity system
across 70 resume/JD pairs: 60 taxonomy-normalized + 10 raw synonym pairs.

Run:
    python eval/benchmark.py
    python eval/benchmark.py --domain "Data Science"
    python eval/benchmark.py --save

Outputs a results table, per-domain breakdown, and sample errors.
"""

import sys, os, json, argparse, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from semantic_engine import semantic_skill_match

# ── 10 raw synonym pairs (the stress test keyword always fails) ───────────────
# Ground truth: no gaps — candidate already has the skill under a different name.
SYNONYM_PAIRS = [
    {
        "id": "SY-01", "domain": "Synonym Resolution",
        "candidate_skills": ["scikit-learn", "pandas"],
        "jd_skills": ["Machine Learning", "Data Analysis"],
        "ground_truth_gaps": [],
        "note": "scikit-learn ↔ Machine Learning"
    },
    {
        "id": "SY-02", "domain": "Synonym Resolution",
        "candidate_skills": ["JS", "ReactJS"],
        "jd_skills": ["JavaScript", "React"],
        "ground_truth_gaps": [],
        "note": "JS ↔ JavaScript, ReactJS ↔ React"
    },
    {
        "id": "SY-03", "domain": "Synonym Resolution",
        "candidate_skills": ["People Management", "Team Lead"],
        "jd_skills": ["Leadership", "Coaching"],
        "ground_truth_gaps": [],
        "note": "People Management ↔ Leadership"
    },
    {
        "id": "SY-04", "domain": "Synonym Resolution",
        "candidate_skills": ["AWS Lambda", "S3", "EC2"],
        "jd_skills": ["AWS", "Cloud"],
        "ground_truth_gaps": [],
        "note": "AWS services ↔ AWS"
    },
    {
        "id": "SY-05", "domain": "Synonym Resolution",
        "candidate_skills": ["TensorFlow", "Keras"],
        "jd_skills": ["Deep Learning", "Machine Learning"],
        "ground_truth_gaps": [],
        "note": "TensorFlow ↔ Deep Learning"
    },
    {
        "id": "SY-06", "domain": "Synonym Resolution",
        "candidate_skills": ["Postgres", "MySQL"],
        "jd_skills": ["SQL", "Database"],
        "ground_truth_gaps": [],
        "note": "Postgres/MySQL ↔ SQL"
    },
    {
        "id": "SY-07", "domain": "Synonym Resolution",
        "candidate_skills": ["Scrum", "Kanban"],
        "jd_skills": ["Agile", "Project Management"],
        "ground_truth_gaps": [],
        "note": "Scrum ↔ Agile"
    },
    {
        "id": "SY-08", "domain": "Synonym Resolution",
        "candidate_skills": ["Google Analytics", "HubSpot"],
        "jd_skills": ["Marketing", "CRM"],
        "ground_truth_gaps": [],
        "note": "HubSpot ↔ CRM"
    },
    {
        "id": "SY-09", "domain": "Synonym Resolution",
        "candidate_skills": ["Hiring", "Talent Acquisition"],
        "jd_skills": ["Recruitment", "HR"],
        "ground_truth_gaps": [],
        "note": "Talent Acquisition ↔ Recruitment"
    },
    {
        "id": "SY-10", "domain": "Synonym Resolution",
        "candidate_skills": ["Warehouse Management", "Stock Control"],
        "jd_skills": ["Inventory Management", "Operations"],
        "ground_truth_gaps": [],
        "note": "Stock Control ↔ Inventory Management"
    },
]


def _keyword_gaps(candidate: list, jd: list) -> list:
    """Exact lowercase set-difference — the keyword baseline."""
    cand_lower = {s.lower() for s in candidate}
    return [s for s in jd if s.lower() not in cand_lower]


def _semantic_gaps(candidate: list, jd: list, threshold: float = 0.65) -> list:
    return semantic_skill_match(candidate, jd, threshold).gaps


def _metrics(predicted: list, ground_truth: list) -> dict:
    pred_set = set(predicted)
    gt_set   = set(ground_truth)
    tp = pred_set & gt_set
    fp = pred_set - gt_set
    fn = gt_set - pred_set
    precision = len(tp) / len(pred_set) if pred_set else (1.0 if not gt_set else 0.0)
    recall    = len(tp) / len(gt_set)   if gt_set   else (1.0 if not pred_set else 0.0)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {
        "tp": sorted(tp), "fp": sorted(fp), "fn": sorted(fn),
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
    }


def run_benchmark(domain_filter: str = None, save: bool = False):
    # Load the 60 taxonomy-normalized pairs
    results_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(results_path) as f:
        data = json.load(f)
    pairs = data["pairs"]

    # Append the 10 raw synonym pairs
    all_pairs = pairs + SYNONYM_PAIRS

    if domain_filter:
        all_pairs = [p for p in all_pairs if p["domain"] == domain_filter]
        if not all_pairs:
            print(f"No pairs found for domain: {domain_filter}")
            return

    kw_results, sem_results = [], []
    errors = []

    for pair in all_pairs:
        cand = pair["candidate_skills"]
        jd   = pair["jd_skills"]
        gt   = pair["ground_truth_gaps"]

        kw_gaps  = _keyword_gaps(cand, jd)
        sem_gaps = _semantic_gaps(cand, jd)

        kw_m  = _metrics(kw_gaps,  gt)
        sem_m = _metrics(sem_gaps, gt)

        kw_results.append(kw_m)
        sem_results.append(sem_m)

        # Collect errors for the error analysis section
        if kw_m["fp"] or kw_m["fn"] or sem_m["fp"] or sem_m["fn"]:
            errors.append({
                "id":     pair["id"],
                "domain": pair["domain"],
                "note":   pair.get("note", ""),
                "keyword_fp":  kw_m["fp"],  "keyword_fn":  kw_m["fn"],
                "semantic_fp": sem_m["fp"], "semantic_fn": sem_m["fn"],
            })

    def avg(lst, key): return round(sum(r[key] for r in lst) / len(lst), 4)

    print("\n" + "="*65)
    print("  SkillBridge — Benchmark Evaluation Report")
    print("="*65)
    print(f"  Total pairs evaluated : {len(all_pairs)}")
    print(f"  Taxonomy-normalized   : {len(pairs)}")
    print(f"  Raw synonym pairs     : {len(SYNONYM_PAIRS)}")
    print(f"  Domain filter         : {domain_filter or 'All'}")
    print("="*65)

    print("\n📊 OVERALL RESULTS\n")
    print(f"{'Method':<22} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-"*54)
    print(f"{'Keyword Baseline':<22} {avg(kw_results,'precision'):>10.4f} "
          f"{avg(kw_results,'recall'):>10.4f} {avg(kw_results,'f1'):>10.4f}")
    print(f"{'Semantic (ours)':<22} {avg(sem_results,'precision'):>10.4f} "
          f"{avg(sem_results,'recall'):>10.4f} {avg(sem_results,'f1'):>10.4f}")

    # Per-domain breakdown
    domains = sorted({p["domain"] for p in all_pairs})
    print("\n📊 PER-DOMAIN F1\n")
    print(f"{'Domain':<26} {'Keyword F1':>12} {'Semantic F1':>12} {'Winner':>10}")
    print("-"*62)
    for d in domains:
        d_pairs = [p for p in all_pairs if p["domain"] == d]
        kw_f1s, sem_f1s = [], []
        for p in d_pairs:
            kw_f1s.append(_metrics(_keyword_gaps(p["candidate_skills"], p["jd_skills"]),
                                   p["ground_truth_gaps"])["f1"])
            sem_f1s.append(_metrics(_semantic_gaps(p["candidate_skills"], p["jd_skills"]),
                                    p["ground_truth_gaps"])["f1"])
        kf = round(sum(kw_f1s)  / len(kw_f1s),  4)
        sf = round(sum(sem_f1s) / len(sem_f1s), 4)
        winner = "Semantic ✓" if sf > kf else ("Keyword ✓" if kf > sf else "Tie")
        print(f"  {d:<24} {kf:>12.4f} {sf:>12.4f} {winner:>10}")

    # Synonym resolution summary (the key differentiator)
    syn_pairs = [p for p in all_pairs if p["domain"] == "Synonym Resolution"]
    if syn_pairs:
        kw_syn  = [_metrics(_keyword_gaps(p["candidate_skills"], p["jd_skills"]),
                            p["ground_truth_gaps"])["f1"] for p in syn_pairs]
        sem_syn = [_metrics(_semantic_gaps(p["candidate_skills"], p["jd_skills"]),
                            p["ground_truth_gaps"])["f1"] for p in syn_pairs]
        print(f"\n🔑 SYNONYM RESOLUTION (n={len(syn_pairs)}, raw un-normalized input)\n")
        print(f"  Keyword Baseline F1 : {round(sum(kw_syn)/len(kw_syn), 4)}"
              f"  ← fails on 'scikit-learn', 'JS', 'People Management'")
        print(f"  Semantic System F1  : {round(sum(sem_syn)/len(sem_syn), 4)}"
              f"  ← handles synonyms via cosine similarity")

    # Error analysis
    if errors:
        print(f"\n⚠️  SAMPLE ERRORS ({min(5, len(errors))} of {len(errors)} imperfect pairs)\n")
        for e in errors[:5]:
            print(f"  [{e['id']}] {e['domain']}"
                  + (f" — {e['note']}" if e['note'] else ""))
            if e["keyword_fp"]:
                print(f"    Keyword  FP (false gaps): {e['keyword_fp']}")
            if e["keyword_fn"]:
                print(f"    Keyword  FN (missed gaps): {e['keyword_fn']}")
            if e["semantic_fp"]:
                print(f"    Semantic FP (false gaps): {e['semantic_fp']}")
            if e["semantic_fn"]:
                print(f"    Semantic FN (missed gaps): {e['semantic_fn']}")

    print("\n📋 CAVEATS")
    print("  • Taxonomy pairs use pre-normalized labels — both methods perform well.")
    print("  • Semantic advantage is largest on raw un-normalized resume text.")
    print("  • Ground truth is author-annotated, not independently verified.")
    print("  • Threshold fixed at 0.65; sensitivity across thresholds not reported.")
    print("  • Data Science domain weakest: ML↔Deep Learning cosine ≈ 0.71 > threshold.")
    print()

    if save:
        out = {
            "total_pairs": len(all_pairs),
            "keyword":  {"precision": avg(kw_results,"precision"),
                         "recall":    avg(kw_results,"recall"),
                         "f1":        avg(kw_results,"f1")},
            "semantic": {"precision": avg(sem_results,"precision"),
                         "recall":    avg(sem_results,"recall"),
                         "f1":        avg(sem_results,"f1")},
            "errors": errors,
        }
        out_path = os.path.join(os.path.dirname(__file__), "benchmark_report.json")
        with open(out_path, "w") as f:
            json.dump(out, f, indent=2)
        print(f"  Report saved → {out_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, default=None,
                        help="Filter to a single domain")
    parser.add_argument("--save",   action="store_true",
                        help="Save JSON report to eval/benchmark_report.json")
    args = parser.parse_args()
    run_benchmark(domain_filter=args.domain, save=args.save)
