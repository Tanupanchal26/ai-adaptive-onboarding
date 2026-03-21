"""
Evaluation harness: measures skill-gap detection accuracy against O*NET ground truth.
Run: python eval/skill_gap_eval.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from semantic_engine import semantic_skill_match

TEST_CASES = [
    {
        "resume_skills": ["scikit-learn", "pandas", "numpy"],
        "jd_skills": ["Machine Learning", "Data Analysis", "Python"],
        "expected_gaps": [],
        "description": "Synonym detection: scikit-learn == Machine Learning",
    },
    {
        "resume_skills": ["JS", "React", "HTML"],
        "jd_skills": ["JavaScript", "Frontend Development", "CSS"],
        "expected_gaps": ["CSS"],
        "description": "Abbreviation: JS == JavaScript",
    },
    {
        "resume_skills": ["People Management", "Budgeting"],
        "jd_skills": ["Leadership", "Finance", "Strategy"],
        "expected_gaps": ["Strategy"],
        "description": "Paraphrase: People Management == Leadership",
    },
]


def compute_skill_gaps(resume_skills: list, jd_skills: list) -> list:
    return semantic_skill_match(resume_skills, jd_skills).gaps


def run_eval(test_cases):
    correct = 0
    for tc in test_cases:
        gaps = compute_skill_gaps(tc["resume_skills"], tc["jd_skills"])
        if set(gaps) == set(tc["expected_gaps"]):
            correct += 1
            print(f"✅ PASS: {tc['description']}")
        else:
            print(f"❌ FAIL: {tc['description']} | got {gaps} expected {tc['expected_gaps']}")
    print(f"\nAccuracy: {correct}/{len(test_cases)} = {round(correct / len(test_cases) * 100)}%")


if __name__ == "__main__":
    run_eval(TEST_CASES)
