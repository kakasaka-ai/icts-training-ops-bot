"""CLI for the CSV-only attendance Phase 1 dry-run."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Sequence

from training_ops.attendance import (
    CsvFormatError,
    InputPaths,
    parse_target_date,
    run_dry_run,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate attendance candidates from local fixture CSV files only."
    )
    parser.add_argument("--date", required=True, help="target date (YYYY-MM-DD)")
    parser.add_argument(
        "--punch-records",
        type=Path,
        default=Path("tests/fixtures/punch_records.csv"),
    )
    parser.add_argument(
        "--training-classes",
        type=Path,
        default=Path("tests/fixtures/training_classes.csv"),
    )
    parser.add_argument(
        "--participants",
        type=Path,
        default=Path("tests/fixtures/participants.csv"),
    )
    parser.add_argument(
        "--slack-absence-posts",
        type=Path,
        default=Path("tests/fixtures/slack_absence_posts.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_dry_run(
            parse_target_date(args.date),
            InputPaths(
                punch_records=args.punch_records,
                training_classes=args.training_classes,
                participants=args.participants,
                slack_absence_posts=args.slack_absence_posts,
            ),
            args.output_dir,
            operator=os.environ.get("TRAINING_OPS_OPERATOR", "local"),
        )
    except (CsvFormatError, OSError, ValueError) as exc:
        parser.error(str(exc))

    print(f"Markdown report: {result.markdown_path}")
    print(f"Candidate CSV: {result.csv_path}")
    print(
        f"Candidates: {len(result.candidates)} "
        f"(dry-run; external connections: 0; run_id: {result.run_id})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
