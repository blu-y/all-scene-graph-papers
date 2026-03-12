#!/usr/bin/env python3
"""Generate a commit message from manual classification boundaries."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

DEFAULT_CSV_PATH = Path(__file__).resolve().parents[1] / "csvs" / "scene_graph_papers_minimal.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate commit message from manual ranges in source column."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"Path to CSV file (default: {DEFAULT_CSV_PATH})",
    )
    return parser.parse_args()


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_manual_numbers(rows: list[dict[str, str]]) -> list[int]:
    numbers: list[int] = []
    for row in rows:
        if row.get("source", "").strip() != "manual":
            continue
        no_value = (row.get("no") or "").strip()
        if no_value.isdigit():
            numbers.append(int(no_value))
    return sorted(set(numbers))


def continuous_runs(sorted_numbers: list[int]) -> list[tuple[int, int]]:
    if not sorted_numbers:
        return []

    runs: list[tuple[int, int]] = []
    start = sorted_numbers[0]
    end = sorted_numbers[0]

    for number in sorted_numbers[1:]:
        if number == end + 1:
            end = number
            continue
        runs.append((start, end))
        start = end = number

    runs.append((start, end))
    return runs


def format_runs_for_commit(
    runs: list[tuple[int, int]], global_min: int, global_max: int
) -> str:
    parts: list[str] = []
    for idx, (start, end) in enumerate(runs):
        left = "" if idx == 0 and start == global_min else str(start)
        right = "" if idx == len(runs) - 1 and end == global_max else str(end)
        if left and right and left == right:
            parts.append(left)
        else:
            parts.append(f"{left}~{right}")
    return ", ".join(parts)


def main() -> None:
    args = parse_args()
    rows = load_rows(args.csv)
    all_numbers = sorted(
        {
            int((row.get("no") or "").strip())
            for row in rows
            if (row.get("no") or "").strip().isdigit()
        }
    )
    if not all_numbers:
        raise SystemExit("No valid `no` values found.")

    manual_numbers = load_manual_numbers(rows)
    runs = continuous_runs(manual_numbers)
    if not runs:
        raise SystemExit("No manual rows found in source column.")

    marker = format_runs_for_commit(runs, all_numbers[0], all_numbers[-1])
    print(f"classified: {marker}")


if __name__ == "__main__":
    main()
