#!/usr/bin/env python3
"""
Translate paper abstracts to Korean in chunks.
Progress is saved incrementally to allow tracking.
"""

import csv
import json
import os
import sys
from pathlib import Path

# Add anthropic for Claude API
try:
    import anthropic
except ImportError:
    print("Installing anthropic package...")
    os.system("pip install anthropic")
    import anthropic


CHUNK_SIZE = 20  # Process 20 papers at a time
INPUT_CSV = (
    Path(__file__).parent.parent.parent
    / "references/survey/scene_graph_papers_abstract.csv"
)
OUTPUT_CSV = (
    Path(__file__).parent.parent.parent
    / "references/survey/scene_graph_papers_abs_kor.csv"
)
PROGRESS_FILE = Path(__file__).parent / "translation_progress.json"


def load_progress():
    """Load translation progress."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"last_completed_no": 0, "total_translated": 0}


def save_progress(progress):
    """Save translation progress."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def translate_chunk(abstracts, api_key):
    """Translate a chunk of abstracts using Claude API."""
    client = anthropic.Anthropic(api_key=api_key)

    # Prepare prompt
    papers_text = "\n\n".join(
        [f"Paper {paper['no']}:\n{paper['abstract']}" for paper in abstracts]
    )

    prompt = f"""다음 논문 초록들을 한국어로 번역해주세요. 학술적이고 자연스러운 한국어를 사용하고, 기술 용어는 적절히 처리해주세요.

번역 가이드라인:
- 모델명, 고유명사는 영어 그대로 유지 (예: CLIP, ResNet, Transformer)
- 기술 용어는 자연스럽게 번역 (예: scene graph → 장면 그래프, object detection → 객체 탐지)
- 형식적이고 학술적인 문체 사용
- 의미와 뉘앙스를 정확히 전달

JSON 형식으로 응답해주세요:
{{
  "translations": [
    {{"no": 번호, "abstract_kor": "번역된 초록"}},
    ...
  ]
}}

초록들:
{papers_text}"""

    message = client.messages.create(
        model="claude-sonnet-4",
        max_tokens=16000,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse response
    response_text = message.content[0].text

    # Extract JSON from response
    import re

    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group())
        return result["translations"]
    else:
        raise ValueError("Failed to parse translation response")


def main():
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Load progress
    progress = load_progress()
    start_no = progress["last_completed_no"] + 1

    print(f"Loading papers from {INPUT_CSV}")
    print(f"Resuming from paper #{start_no}")

    # Read input CSV
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_papers = list(reader)

    total_papers = len(all_papers)
    papers_to_translate = [p for p in all_papers if int(p["no"]) >= start_no]

    print(f"Total papers: {total_papers}")
    print(f"Papers to translate: {len(papers_to_translate)}")

    # Initialize output file if starting fresh
    if start_no == 1:
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "no",
                    "date_yymm",
                    "title",
                    "authors",
                    "abstract",
                    "abstract_kor",
                ],
            )
            writer.writeheader()

    # Process in chunks
    for i in range(0, len(papers_to_translate), CHUNK_SIZE):
        chunk = papers_to_translate[i : i + CHUNK_SIZE]
        chunk_nos = [int(p["no"]) for p in chunk]

        print(
            f"\nTranslating papers {chunk_nos[0]} to {chunk_nos[-1]} ({len(chunk)} papers)..."
        )

        try:
            # Translate chunk
            translations = translate_chunk(chunk, api_key)

            # Create a mapping of no -> translation
            trans_map = {t["no"]: t["abstract_kor"] for t in translations}

            # Write to CSV
            with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "no",
                        "date_yymm",
                        "title",
                        "authors",
                        "abstract",
                        "abstract_kor",
                    ],
                )
                for paper in chunk:
                    paper["abstract_kor"] = trans_map.get(int(paper["no"]), "")
                    writer.writerow(paper)

            # Update progress
            progress["last_completed_no"] = chunk_nos[-1]
            progress["total_translated"] = progress["last_completed_no"]
            save_progress(progress)

            print(
                f"✓ Completed: {progress['total_translated']}/{total_papers} papers ({progress['total_translated'] / total_papers * 100:.1f}%)"
            )

        except Exception as e:
            print(f"Error translating chunk: {e}")
            print(
                f"Progress saved. Restart script to continue from paper #{progress['last_completed_no'] + 1}"
            )
            sys.exit(1)

    print(f"\n✓ Translation complete! Output saved to {OUTPUT_CSV}")
    print(f"Total papers translated: {progress['total_translated']}")


if __name__ == "__main__":
    main()
