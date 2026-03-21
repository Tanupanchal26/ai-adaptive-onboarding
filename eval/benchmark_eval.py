"""
Benchmark: Keyword vs Semantic skill-gap detection across 60 pairs (6 domains).
Output: eval/benchmark_results.json

Run: python eval/benchmark_eval.py
"""

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

DATASET_PATH = Path(__file__).parent / "benchmark_dataset.json"
OUTPUT_PATH  = Path(__file__).parent / "benchmark_results.json"
THRESHOLD    = 0.65


# ── Matching methods ──────────────────────────────────────────────────────────

def keyword_gaps(candidate: list, jd: list) -> set:
    cand_lower = {s.lower() for s in candidate}
    return {s for s in jd if s.lower() not in cand_lower}


def semantic_gaps(candidate: list, jd: list) -> set:
    from gap_logic import compute_gaps
    result = compute_gaps(set(candidate), set(jd), threshold=THRESHOLD)
    return result["gaps"]


# ── Per-pair metrics ──────────────────────────────────────────────────────────

def compute_metrics(predicted: set, ground_truth: set, jd_skills: list) -> dict:
    """
    TP = gaps correctly predicted
    FP = predicted as gap but not a real gap (false alarm)
    FN = real gap missed by predictor
    """
    tp = predicted & ground_truth
    fp = predicted - ground_truth
    fn = ground_truth - predicted

    precision = len(tp) / max(len(tp) + len(fp), 1)
    recall    = len(tp) / max(len(tp) + len(fn), 1)
    f1        = (2 * precision * recall / max(precision + recall, 1e-9))

    return {
        "true_positives":  sorted(tp),
        "false_positives": sorted(fp),
        "false_negatives": sorted(fn),
        "precision": round(precision, 4),
        "recall":    round(recall, 4),
        "f1":        round(f1, 4),
    }


# ── Aggregate metrics ─────────────────────────────────────────────────────────

def aggregate(pairs_results: list, method: str) -> dict:
    p_vals = [r[method]["metrics"]["precision"] for r in pairs_results]
    r_vals = [r[method]["metrics"]["recall"]    for r in pairs_results]
    f_vals = [r[method]["metrics"]["f1"]        for r in pairs_results]
    n = len(pairs_results)
    return {
        "avg_precision": round(sum(p_vals) / n, 4),
        "avg_recall":    round(sum(r_vals) / n, 4),
        "avg_f1":        round(sum(f_vals) / n, 4),
    }


def domain_aggregate(pairs_results: list, method: str) -> dict:
    from collections import defaultdict
    buckets = defaultdict(list)
    for r in pairs_results:
        buckets[r["domain"]].append(r)
    return {d: aggregate(v, method) for d, v in buckets.items()}


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    pairs_results = []
    errors = []

    for pair in dataset["pairs"]:
        pid        = pair["id"]
        candidate  = pair["candidate"]["skills"]
        jd         = pair["job"]["skills"]
        gt_gaps    = set(pair["ground_truth_gaps"])

        # keyword
        kw_pred    = keyword_gaps(candidate, jd)
        kw_metrics = compute_metrics(kw_pred, gt_gaps, jd)

        # semantic (may fail if sentence-transformers unavailable)
        try:
            sem_pred    = semantic_gaps(candidate, jd)
            sem_metrics = compute_metrics(sem_pred, gt_gaps, jd)
            sem_error   = None
        except Exception as e:
            sem_pred    = set()
            sem_metrics = {"true_positives": [], "false_positives": [], "false_negatives": sorted(gt_gaps),
                           "precision": 0.0, "recall": 0.0, "f1": 0.0}
            sem_error   = str(e)
            errors.append({"id": pid, "error": sem_error})

        pairs_results.append({
            "id":     pid,
            "domain": pair["domain"],
            "candidate_skills":  candidate,
            "jd_skills":         jd,
            "ground_truth_gaps": sorted(gt_gaps),
            "keyword": {
                "predicted_gaps": sorted(kw_pred),
                "metrics":        kw_metrics,
            },
            "semantic": {
                "predicted_gaps": sorted(sem_pred),
                "metrics":        sem_metrics,
                **({"error": sem_error} if sem_error else {}),
            },
        })

    output = {
        "meta": {
            **dataset["meta"],
            "semantic_threshold": THRESHOLD,
        },
        "overall": {
            "keyword":  aggregate(pairs_results, "keyword"),
            "semantic": aggregate(pairs_results, "semantic"),
        },
        "by_domain": {
            "keyword":  domain_aggregate(pairs_results, "keyword"),
            "semantic": domain_aggregate(pairs_results, "semantic"),
        },
        "pairs": pairs_results,
        **({"errors": errors} if errors else {}),
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    # ── Console summary ───────────────────────────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  SkillBridge Benchmark — {len(pairs_results)} pairs, {len(dataset['meta']['domains'])} domains")
    print(f"{'='*55}")
    print(f"{'Method':<12} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print(f"{'-'*55}")
    for method in ("keyword", "semantic"):
        m = output["overall"][method]
        print(f"{method:<12} {m['avg_precision']:>10.4f} {m['avg_recall']:>10.4f} {m['avg_f1']:>10.4f}")
    print(f"\nBy domain:")
    domains = dataset["meta"]["domains"]
    for domain in domains:
        kw  = output["by_domain"]["keyword"].get(domain, {})
        sem = output["by_domain"]["semantic"].get(domain, {})
        print(f"  {domain:<22} keyword F1={kw.get('avg_f1', 0):.4f}  semantic F1={sem.get('avg_f1', 0):.4f}")
    if errors:
        print(f"\n[WARN] {len(errors)} semantic errors (fallback used) — install sentence-transformers for full results")
    print(f"\n[OK] Results saved -> {OUTPUT_PATH}\n")


if __name__ == "__main__":
    run()
