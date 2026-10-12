"""Classify uncategorized papers with the fine-tuned laya model and mark them as source=laya.

Two-stage: predict the category, then take the subcategory answer for that category
(questions.json holds one `sub:<category>` question per category).
"""
import csv
import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MINIMAL_CSV = BASE_DIR / "csvs" / "scene_graph_papers_minimal.csv"
ABSTRACT_CSV = BASE_DIR / "csvs" / "scene_graph_papers_abstract.csv"

MODEL_REPO = "Blu-y/laya-scene-graph-papers"
MODEL_REVISION = "6cde8628d2671186167d6509bca0b57f124e3d96"


def main():
    with open(MINIMAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    with open(ABSTRACT_CSV, "r", encoding="utf-8") as f:
        abstracts = {r["no"]: r for r in csv.DictReader(f)}

    targets = [r for r in rows if r["source"] == "uncategorized" and r["no"] in abstracts]
    print(f"Found {len(targets)} uncategorized papers.")
    if not targets:
        return

    import laya
    from huggingface_hub import hf_hub_download

    agent = laya.load(MODEL_REPO, revision=MODEL_REVISION, device="cpu")
    with open(hf_hub_download(MODEL_REPO, "questions.json", revision=MODEL_REVISION), encoding="utf-8") as f:
        questions = json.load(f)

    states = []
    for r in targets:
        a = abstracts[r["no"]]
        states.append(f"Title: {a['title']}\nAbstract: {a['abstract'].removeprefix('[Withdrawn] ')}")
    results = agent.predict_batch(states, questions, batch_size=8, max_len=768, head_max_len=256)

    for r, res in zip(targets, results):
        cat = res["answers"]["category"]["choice"]
        sub = res["answers"]["sub:" + cat]["choice"]
        r["category"], r["subcategory"], r["source"] = cat, sub, "laya"
        print(f"#{r['no']}: {cat} > {sub}")

    with open(MINIMAL_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    subprocess.run(["python3", str(BASE_DIR / "scripts" / "generate_classified_mds.py")], check=True)


if __name__ == "__main__":
    main()
