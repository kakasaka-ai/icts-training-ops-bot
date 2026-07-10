from __future__ import annotations

import csv
import json
import logging
import os
import socket
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from training_ops.attendance import (
    ABSENT_WITH_NOTICE,
    ATTENDANCE_CANDIDATE,
    CANDIDATE_CSV_FIELDS,
    DUPLICATE_PUNCH,
    EXCLUDED,
    NAME_MISMATCH,
    UNAUTHORIZED_ABSENCE_CANDIDATE,
    VENUE_MISMATCH,
    CsvFormatError,
    InputPaths,
    run_dry_run,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
INPUT_PATHS = InputPaths(
    punch_records=FIXTURES / "punch_records.csv",
    training_classes=FIXTURES / "training_classes.csv",
    participants=FIXTURES / "participants.csv",
    slack_absence_posts=FIXTURES / "slack_absence_posts.csv",
)


def _by_participant(result):
    return {item.participant_id: item for item in result.candidates}


def test_all_phase_one_classifications(tmp_path: Path) -> None:
    result = run_dry_run(
        date(2026, 7, 9),
        INPUT_PATHS,
        tmp_path,
        run_id="test-run",
    )
    candidates = _by_participant(result)

    assert candidates["P001"].classification == ATTENDANCE_CANDIDATE
    assert candidates["P002"].classification == VENUE_MISMATCH
    assert candidates["P003"].classification == ABSENT_WITH_NOTICE
    assert candidates["P004"].classification == DUPLICATE_PUNCH
    assert candidates["P005"].classification == EXCLUDED
    assert candidates["P006"].classification == EXCLUDED
    assert candidates["P007"].classification == UNAUTHORIZED_ABSENCE_CANDIDATE
    assert candidates["P008"].classification == NAME_MISMATCH
    assert candidates["P009"].classification == EXCLUDED

    assert candidates["P001"].review_required is False
    assert candidates["P003"].review_required is False
    review_ids = ("P002", "P004", "P005", "P006", "P007", "P008", "P009")
    for participant_id in review_ids:
        assert candidates[participant_id].review_required is True

    assert result.warnings == ("unmatched punch: PU005",)


def test_requested_date_generates_expected_outputs(tmp_path: Path) -> None:
    result = run_dry_run(
        date(2026, 7, 10),
        INPUT_PATHS,
        tmp_path,
        run_id="test-run",
    )
    candidates = _by_participant(result)

    assert candidates["P010"].classification == ATTENDANCE_CANDIDATE
    assert candidates["P011"].classification == UNAUTHORIZED_ABSENCE_CANDIDATE
    assert candidates["P011"].review_required is True
    assert candidates["P012"].classification == ABSENT_WITH_NOTICE
    assert result.markdown_path.name == "attendance_dry_run_2026-07-10.md"
    assert result.csv_path.name == "attendance_candidates_2026-07-10.csv"


def test_report_has_required_sections_and_safety_notice(tmp_path: Path) -> None:
    result = run_dry_run(
        date(2026, 7, 9),
        INPUT_PATHS,
        tmp_path,
        run_id="test-run",
    )
    report = result.markdown_path.read_text(encoding="utf-8")

    for heading in (
        "## Summary counts",
        "## Attendance registration candidates",
        "## Absences with Slack notice",
        "## Unauthorized absence candidates",
        "## Review-required records",
        "## Excluded records",
        "## Errors and warnings",
    ):
        assert heading in report
    assert "DRY-RUN only" in report
    assert (
        "no Salesforce, RaySheet, Slack, Google Sheets, LINE, or ICTS AI connection"
        in report
    )
    assert "The current Salesforce attendance value is not present" in report
    assert "PU001" in report
    assert "SL001" in report
    assert "warning: unmatched punch: PU005" in report


def test_candidate_csv_uses_specified_columns(tmp_path: Path) -> None:
    result = run_dry_run(
        date(2026, 7, 10),
        INPUT_PATHS,
        tmp_path,
        run_id="test-run",
    )
    with result.csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert tuple(reader.fieldnames or ()) == CANDIDATE_CSV_FIELDS
    assert len(rows) == 3
    unauthorized = next(row for row in rows if row["participant_id"] == "P011")
    assert unauthorized["review_required"] == "true"


def test_run_emits_structured_completion_log(tmp_path: Path, caplog) -> None:
    with caplog.at_level(logging.INFO, logger="training_ops.attendance"):
        run_dry_run(
            date(2026, 7, 10),
            INPUT_PATHS,
            tmp_path,
            operator="test-operator",
            run_id="test-run",
        )

    messages = [json.loads(record.message) for record in caplog.records]
    completed = next(
        item for item in messages if item["event"] == "attendance_dry_run_completed"
    )
    assert completed["run_id"] == "test-run"
    assert completed["operator"] == "test-operator"
    assert completed["mode"] == "dry-run"
    assert completed["approved_by"] is None
    assert completed["execution_result"] == "completed"
    assert completed["errors"] == []


def test_dry_run_does_not_open_network_connections(
    tmp_path: Path, monkeypatch
) -> None:
    def fail_connection(*args, **kwargs):
        raise AssertionError("external network access is prohibited in Phase 1")

    monkeypatch.setattr(socket, "create_connection", fail_connection)
    monkeypatch.setattr(socket.socket, "connect", fail_connection)

    result = run_dry_run(
        date(2026, 7, 10),
        INPUT_PATHS,
        tmp_path,
        run_id="test-run",
    )
    assert len(result.candidates) == 3


def test_cli_module_generates_reports(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "training_ops.jobs.attendance_dry_run",
            "--date",
            "2026-07-10",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "external connections: 0" in completed.stdout
    assert '"event": "attendance_dry_run_completed"' in completed.stderr
    assert (tmp_path / "attendance_dry_run_2026-07-10.md").exists()
    assert (tmp_path / "attendance_candidates_2026-07-10.csv").exists()


def test_missing_required_column_has_clear_error(tmp_path: Path) -> None:
    broken_participants = tmp_path / "participants.csv"
    broken_participants.write_text(
        "participant_id,class_id,student_name,status\n"
        "P001,CLASS001,Sample Student,active\n",
        encoding="utf-8",
    )

    with pytest.raises(CsvFormatError, match="missing required columns"):
        run_dry_run(
            date(2026, 7, 10),
            InputPaths(
                punch_records=INPUT_PATHS.punch_records,
                training_classes=INPUT_PATHS.training_classes,
                participants=broken_participants,
                slack_absence_posts=INPUT_PATHS.slack_absence_posts,
            ),
            tmp_path / "reports",
            run_id="test-run",
        )
