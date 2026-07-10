"""CSV-only attendance classification for Phase 1.

Salesforce fixture data is the source of truth. Punch and Slack fixture data is
used only as evidence. This module has no external API clients and never writes
to Salesforce, Slack, Google Sheets, LINE, or ICTS AI.
"""

from __future__ import annotations

import csv
import json
import logging
import unicodedata
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence


LOGGER = logging.getLogger(__name__)

ATTENDANCE_CANDIDATE = "attendance_candidate"
ABSENT_WITH_NOTICE = "absent_with_notice"
UNAUTHORIZED_ABSENCE_CANDIDATE = "unauthorized_absence_candidate"
VENUE_MISMATCH = "venue_mismatch"
NAME_MISMATCH = "name_mismatch"
DUPLICATE_PUNCH = "duplicate_punch"
EXCLUDED = "excluded"

CLASSIFICATION_ORDER = (
    ATTENDANCE_CANDIDATE,
    ABSENT_WITH_NOTICE,
    UNAUTHORIZED_ABSENCE_CANDIDATE,
    VENUE_MISMATCH,
    NAME_MISMATCH,
    DUPLICATE_PUNCH,
    EXCLUDED,
)

REVIEW_REQUIRED_CLASSIFICATIONS = frozenset(
    {
        UNAUTHORIZED_ABSENCE_CANDIDATE,
        VENUE_MISMATCH,
        NAME_MISMATCH,
        DUPLICATE_PUNCH,
        EXCLUDED,
    }
)

EXCLUDED_STATUSES = frozenset(
    {
        "withdrawn",
        "retired",
        "graduated_optional",
        "離脱",
        "退職",
        "卒業任意参加",
    }
)

CANDIDATE_CSV_FIELDS = (
    "target_date",
    "class_id",
    "participant_id",
    "salesforce_student_id",
    "employee_id",
    "student_name",
    "classification",
    "punch_id",
    "punched_at",
    "punch_venue",
    "scheduled_venue",
    "slack_absence_post_id",
    "confidence",
    "review_required",
    "reason",
)


class CsvFormatError(ValueError):
    """Raised when a fixture does not satisfy the Phase 1 CSV contract."""


@dataclass(frozen=True)
class InputPaths:
    punch_records: Path
    training_classes: Path
    participants: Path
    slack_absence_posts: Path

    def as_log_dict(self) -> dict[str, str]:
        return {
            "punch_records": str(self.punch_records),
            "training_classes": str(self.training_classes),
            "participants": str(self.participants),
            "slack_absence_posts": str(self.slack_absence_posts),
        }


@dataclass(frozen=True)
class TrainingClass:
    class_id: str
    class_name: str
    training_date: date
    venue: str
    salesforce_class_id: str
    status: str


@dataclass(frozen=True)
class Participant:
    participant_id: str
    class_id: str
    salesforce_student_id: str
    employee_id: str
    email: str
    student_name: str
    status: str


@dataclass(frozen=True)
class PunchRecord:
    punch_id: str
    punched_at: datetime
    student_name: str
    employee_id: str
    email: str
    venue: str


@dataclass(frozen=True)
class SlackAbsencePost:
    post_id: str
    posted_at: datetime
    class_id: str
    student_name: str
    employee_id: str
    message: str


@dataclass(frozen=True)
class AttendanceCandidate:
    target_date: date
    class_id: str
    participant_id: str
    salesforce_student_id: str
    employee_id: str
    student_name: str
    classification: str
    scheduled_venue: str
    confidence: str
    review_required: bool
    reason: str
    punches: tuple[PunchRecord, ...] = ()
    slack_posts: tuple[SlackAbsencePost, ...] = ()

    def to_csv_row(self) -> dict[str, str]:
        return {
            "target_date": self.target_date.isoformat(),
            "class_id": self.class_id,
            "participant_id": self.participant_id,
            "salesforce_student_id": self.salesforce_student_id,
            "employee_id": self.employee_id,
            "student_name": self.student_name,
            "classification": self.classification,
            "punch_id": ";".join(item.punch_id for item in self.punches),
            "punched_at": ";".join(item.punched_at.isoformat() for item in self.punches),
            "punch_venue": ";".join(item.venue for item in self.punches),
            "scheduled_venue": self.scheduled_venue,
            "slack_absence_post_id": ";".join(
                item.post_id for item in self.slack_posts
            ),
            "confidence": self.confidence,
            "review_required": str(self.review_required).lower(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class EvaluationResult:
    candidates: tuple[AttendanceCandidate, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class DryRunResult:
    run_id: str
    target_date: date
    candidates: tuple[AttendanceCandidate, ...]
    warnings: tuple[str, ...]
    markdown_path: Path
    csv_path: Path


def parse_target_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"date must use YYYY-MM-DD format: {raw!r}") from exc


def _read_rows(path: Path, required_fields: Iterable[str]) -> list[dict[str, str]]:
    required = set(required_fields)
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except FileNotFoundError as exc:
        raise CsvFormatError(f"input CSV not found: {path}") from exc

    with handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or ())
        missing = sorted(required - headers)
        if missing:
            raise CsvFormatError(
                f"{path}: missing required columns: {', '.join(missing)}"
            )
        return [
            {key: (value or "").strip() for key, value in row.items() if key}
            for row in reader
            if any((value or "").strip() for value in row.values())
        ]


def _required(row: Mapping[str, str], field: str, path: Path, line: int) -> str:
    value = row.get(field, "").strip()
    if not value:
        raise CsvFormatError(f"{path}:{line}: {field} is required")
    return value


def _parse_date(raw: str, path: Path, line: int, field: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise CsvFormatError(
            f"{path}:{line}: {field} must use YYYY-MM-DD format: {raw!r}"
        ) from exc


def _parse_datetime(raw: str, path: Path, line: int, field: str) -> datetime:
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CsvFormatError(
            f"{path}:{line}: {field} must use ISO 8601 format: {raw!r}"
        ) from exc


def load_training_classes(path: Path) -> list[TrainingClass]:
    rows = _read_rows(
        path,
        {
            "class_id",
            "class_name",
            "training_date",
            "venue",
            "salesforce_class_id",
            "status",
        },
    )
    classes: list[TrainingClass] = []
    seen: set[str] = set()
    for line, row in enumerate(rows, start=2):
        class_id = _required(row, "class_id", path, line)
        if class_id in seen:
            raise CsvFormatError(f"{path}:{line}: duplicate class_id: {class_id}")
        seen.add(class_id)
        classes.append(
            TrainingClass(
                class_id=class_id,
                class_name=_required(row, "class_name", path, line),
                training_date=_parse_date(
                    _required(row, "training_date", path, line),
                    path,
                    line,
                    "training_date",
                ),
                venue=_required(row, "venue", path, line),
                salesforce_class_id=_required(
                    row, "salesforce_class_id", path, line
                ),
                status=_required(row, "status", path, line),
            )
        )
    return classes


def load_participants(path: Path) -> list[Participant]:
    rows = _read_rows(
        path,
        {
            "participant_id",
            "class_id",
            "salesforce_student_id",
            "employee_id",
            "email",
            "student_name",
            "status",
        },
    )
    participants: list[Participant] = []
    seen: set[tuple[str, str]] = set()
    for line, row in enumerate(rows, start=2):
        participant_id = _required(row, "participant_id", path, line)
        class_id = _required(row, "class_id", path, line)
        key = (class_id, participant_id)
        if key in seen:
            raise CsvFormatError(
                f"{path}:{line}: duplicate class_id/participant_id pair: {key}"
            )
        seen.add(key)
        participants.append(
            Participant(
                participant_id=participant_id,
                class_id=class_id,
                salesforce_student_id=_required(
                    row, "salesforce_student_id", path, line
                ),
                employee_id=_required(row, "employee_id", path, line),
                email=_required(row, "email", path, line),
                student_name=_required(row, "student_name", path, line),
                status=_required(row, "status", path, line),
            )
        )
    return participants


def load_punch_records(path: Path) -> list[PunchRecord]:
    rows = _read_rows(
        path,
        {"punch_id", "punched_at", "student_name", "employee_id", "email", "venue"},
    )
    punches: list[PunchRecord] = []
    seen: set[str] = set()
    for line, row in enumerate(rows, start=2):
        punch_id = _required(row, "punch_id", path, line)
        if punch_id in seen:
            raise CsvFormatError(f"{path}:{line}: duplicate punch_id: {punch_id}")
        seen.add(punch_id)
        student_name = row.get("student_name", "").strip()
        employee_id = row.get("employee_id", "").strip()
        email = row.get("email", "").strip()
        if not any((student_name, employee_id, email)):
            raise CsvFormatError(
                f"{path}:{line}: student_name, employee_id, or email is required"
            )
        punches.append(
            PunchRecord(
                punch_id=punch_id,
                punched_at=_parse_datetime(
                    _required(row, "punched_at", path, line),
                    path,
                    line,
                    "punched_at",
                ),
                student_name=student_name,
                employee_id=employee_id,
                email=email,
                venue=_required(row, "venue", path, line),
            )
        )
    return punches


def load_slack_absence_posts(path: Path) -> list[SlackAbsencePost]:
    rows = _read_rows(
        path,
        {"post_id", "posted_at", "class_id", "student_name", "employee_id", "message"},
    )
    posts: list[SlackAbsencePost] = []
    seen: set[str] = set()
    for line, row in enumerate(rows, start=2):
        post_id = _required(row, "post_id", path, line)
        if post_id in seen:
            raise CsvFormatError(f"{path}:{line}: duplicate post_id: {post_id}")
        seen.add(post_id)
        student_name = row.get("student_name", "").strip()
        employee_id = row.get("employee_id", "").strip()
        if not student_name and not employee_id:
            raise CsvFormatError(
                f"{path}:{line}: student_name or employee_id is required"
            )
        posts.append(
            SlackAbsencePost(
                post_id=post_id,
                posted_at=_parse_datetime(
                    _required(row, "posted_at", path, line),
                    path,
                    line,
                    "posted_at",
                ),
                class_id=_required(row, "class_id", path, line),
                student_name=student_name,
                employee_id=employee_id,
                message=_required(row, "message", path, line),
            )
        )
    return posts


def _normalized(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def _normalized_name(value: str) -> str:
    return "".join(_normalized(value).split())


NORMALIZED_EXCLUDED_STATUSES = frozenset(
    _normalized(status) for status in EXCLUDED_STATUSES
)


def _stable_match(punch: PunchRecord, participant: Participant) -> str | None:
    # Salesforce student ID would be preferred, but the current punch CSV does
    # not contain it. Employee ID therefore precedes email for stable matching.
    if punch.employee_id and punch.employee_id == participant.employee_id:
        return "employee_id"
    if punch.email and _normalized(punch.email) == _normalized(participant.email):
        return "email"
    return None


def _candidate(
    training_class: TrainingClass,
    participant: Participant,
    classification: str,
    confidence: str,
    reason: str,
    *,
    punches: Sequence[PunchRecord] = (),
    slack_posts: Sequence[SlackAbsencePost] = (),
) -> AttendanceCandidate:
    return AttendanceCandidate(
        target_date=training_class.training_date,
        class_id=training_class.class_id,
        participant_id=participant.participant_id,
        salesforce_student_id=participant.salesforce_student_id,
        employee_id=participant.employee_id,
        student_name=participant.student_name,
        classification=classification,
        scheduled_venue=training_class.venue,
        confidence=confidence,
        review_required=classification in REVIEW_REQUIRED_CLASSIFICATIONS,
        reason=reason,
        punches=tuple(punches),
        slack_posts=tuple(slack_posts),
    )


def classify_participant(
    training_class: TrainingClass,
    participant: Participant,
    punches: Sequence[PunchRecord],
    slack_posts: Sequence[SlackAbsencePost],
) -> AttendanceCandidate:
    """Classify one Salesforce roster row using Phase 1 evidence."""

    date_punches = [
        punch
        for punch in punches
        if punch.punched_at.date() == training_class.training_date
    ]
    exact_punches = [
        punch for punch in date_punches if _stable_match(punch, participant)
    ]
    name_punches = [
        punch
        for punch in date_punches
        if not _stable_match(punch, participant)
        and _normalized_name(punch.student_name)
        == _normalized_name(participant.student_name)
    ]
    exact_posts = [
        post
        for post in slack_posts
        if post.class_id == training_class.class_id
        and post.employee_id
        and post.employee_id == participant.employee_id
    ]
    name_posts = [
        post
        for post in slack_posts
        if post.class_id == training_class.class_id
        and post.employee_id != participant.employee_id
        and _normalized_name(post.student_name)
        == _normalized_name(participant.student_name)
    ]

    if _normalized(participant.status) in NORMALIZED_EXCLUDED_STATUSES:
        return _candidate(
            training_class,
            participant,
            EXCLUDED,
            "high",
            f"Salesforce participant status is {participant.status}",
            punches=exact_punches or name_punches,
            slack_posts=exact_posts or name_posts,
        )

    if len(exact_punches) > 1:
        return _candidate(
            training_class,
            participant,
            DUPLICATE_PUNCH,
            "high",
            "multiple punches matched by stable ID for the same date",
            punches=exact_punches,
        )

    if len(exact_punches) == 1:
        punch = exact_punches[0]
        match_key = _stable_match(punch, participant)
        if _normalized(punch.venue) != _normalized(training_class.venue):
            return _candidate(
                training_class,
                participant,
                VENUE_MISMATCH,
                "high",
                f"{match_key} matched, but punch venue differs from scheduled venue",
                punches=exact_punches,
            )
        return _candidate(
            training_class,
            participant,
            ATTENDANCE_CANDIDATE,
            "high",
            f"{match_key} and venue matched the Salesforce roster",
            punches=exact_punches,
        )

    if name_punches:
        return _candidate(
            training_class,
            participant,
            NAME_MISMATCH,
            "low",
            "punch matched by name only; stable ID review is required",
            punches=name_punches,
        )

    if exact_posts:
        return _candidate(
            training_class,
            participant,
            ABSENT_WITH_NOTICE,
            "high",
            "no punch; Slack absence class_id and employee_id matched",
            slack_posts=exact_posts,
        )

    if name_posts:
        return _candidate(
            training_class,
            participant,
            NAME_MISMATCH,
            "low",
            "no punch; Slack absence notice matched by name only",
            slack_posts=name_posts,
        )

    return _candidate(
        training_class,
        participant,
        UNAUTHORIZED_ABSENCE_CANDIDATE,
        "medium",
        "no punch and no stable-ID Slack absence notice",
    )


def build_candidates(
    target_date: date,
    training_classes: Sequence[TrainingClass],
    participants: Sequence[Participant],
    punches: Sequence[PunchRecord],
    slack_posts: Sequence[SlackAbsencePost],
) -> EvaluationResult:
    classes_by_id = {item.class_id: item for item in training_classes}
    unknown_class_ids = sorted(
        {participant.class_id for participant in participants} - classes_by_id.keys()
    )
    if unknown_class_ids:
        raise CsvFormatError(
            "participants.csv contains unknown class_id values: "
            + ", ".join(unknown_class_ids)
        )

    target_classes = {
        class_id: item
        for class_id, item in classes_by_id.items()
        if item.training_date == target_date
    }
    scheduled_participants = [
        participant
        for participant in participants
        if participant.class_id in target_classes
    ]
    candidates = [
        classify_participant(
            target_classes[participant.class_id],
            participant,
            punches,
            slack_posts,
        )
        for participant in scheduled_participants
    ]

    warnings: list[str] = []
    for punch in punches:
        if punch.punched_at.date() != target_date:
            continue
        if not any(
            _stable_match(punch, participant)
            or _normalized_name(punch.student_name)
            == _normalized_name(participant.student_name)
            for participant in scheduled_participants
        ):
            warnings.append(f"unmatched punch: {punch.punch_id}")

    for post in slack_posts:
        if post.class_id not in target_classes:
            continue
        class_participants = [
            item
            for item in scheduled_participants
            if item.class_id == post.class_id
        ]
        if not any(
            (post.employee_id and post.employee_id == participant.employee_id)
            or _normalized_name(post.student_name)
            == _normalized_name(participant.student_name)
            for participant in class_participants
        ):
            warnings.append(f"unmatched Slack absence post: {post.post_id}")

    return EvaluationResult(
        candidates=tuple(
            sorted(
                candidates,
                key=lambda item: (item.class_id, item.participant_id),
            )
        ),
        warnings=tuple(warnings),
    )


def write_candidate_csv(
    path: Path, candidates: Sequence[AttendanceCandidate]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(item.to_csv_row() for item in candidates)


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _append_candidate_section(
    lines: list[str],
    title: str,
    candidates: Sequence[AttendanceCandidate],
) -> None:
    lines.extend(
        [
            f"## {title}",
            "",
            "| class_id | participant_id | student_name | classification | punch IDs | punch venues | Slack post IDs | confidence | review_required | reason |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    if not candidates:
        lines.append("| - | - | - | none | - | - | - | - | - | - |")
    else:
        for item in candidates:
            row = (
                item.class_id,
                item.participant_id,
                item.student_name,
                item.classification,
                ", ".join(punch.punch_id for punch in item.punches),
                ", ".join(punch.venue for punch in item.punches),
                ", ".join(post.post_id for post in item.slack_posts),
                item.confidence,
                str(item.review_required).lower(),
                item.reason,
            )
            lines.append("| " + " | ".join(_markdown_cell(value) for value in row) + " |")
    lines.append("")


def write_markdown_report(
    path: Path,
    target_date: date,
    candidates: Sequence[AttendanceCandidate],
    warnings: Sequence[str],
    input_paths: InputPaths,
    *,
    run_id: str,
    operator: str,
    started_at: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter(item.classification for item in candidates)
    lines = [
        f"# Attendance dry-run report ({target_date.isoformat()})",
        "",
        "> DRY-RUN only: no Salesforce, RaySheet, Slack, Google Sheets, LINE, or ICTS AI connection or write was performed.",
        "",
        "Salesforce fixture records are the source of truth. Punch and Slack CSV files are input evidence only.",
        "The current Salesforce attendance value is not present in Phase 1 fixtures, so no current value is inferred and no update can be approved from this report.",
        "",
        "## Execution metadata",
        "",
        f"- run_id: `{run_id}`",
        f"- operator: `{operator}`",
        f"- timestamp: `{started_at}`",
        "- mode: `dry-run`",
        "- approved_by: `none`",
        "- execution_result: `completed`",
        "",
        "## Summary counts",
        "",
        "| classification | count |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {classification} | {counts[classification]} |"
        for classification in CLASSIFICATION_ORDER
    )
    lines.extend([f"| **total** | **{len(candidates)}** |", ""])

    _append_candidate_section(
        lines,
        "Attendance registration candidates",
        [item for item in candidates if item.classification == ATTENDANCE_CANDIDATE],
    )
    _append_candidate_section(
        lines,
        "Absences with Slack notice",
        [item for item in candidates if item.classification == ABSENT_WITH_NOTICE],
    )
    _append_candidate_section(
        lines,
        "Unauthorized absence candidates",
        [
            item
            for item in candidates
            if item.classification == UNAUTHORIZED_ABSENCE_CANDIDATE
        ],
    )
    _append_candidate_section(
        lines,
        "Review-required records",
        [
            item
            for item in candidates
            if item.classification in {VENUE_MISMATCH, NAME_MISMATCH, DUPLICATE_PUNCH}
        ],
    )
    _append_candidate_section(
        lines,
        "Excluded records",
        [item for item in candidates if item.classification == EXCLUDED],
    )

    lines.extend(["## Errors and warnings", "", "- errors: none"])
    if warnings:
        lines.extend(f"- warning: {warning}" for warning in warnings)
    else:
        lines.append("- warnings: none")
    lines.extend(
        [
            "",
            "## Input CSV files",
            "",
            f"- training classes: `{input_paths.training_classes}`",
            f"- participants: `{input_paths.participants}`",
            f"- punch records: `{input_paths.punch_records}`",
            f"- Slack absence posts: `{input_paths.slack_absence_posts}`",
            "",
            "`review_required=false` does not mean an external write occurred. Phase 1 only creates local candidates.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _structured_log(level: int, event: str, **fields: object) -> None:
    LOGGER.log(
        level,
        json.dumps({"event": event, **fields}, ensure_ascii=False, sort_keys=True),
    )


def run_dry_run(
    target_date: date,
    input_paths: InputPaths,
    output_dir: Path,
    *,
    operator: str = "local",
    run_id: str | None = None,
) -> DryRunResult:
    actual_run_id = run_id or str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    common_log_fields = {
        "run_id": actual_run_id,
        "operator": operator,
        "timestamp": started_at,
        "target_date": target_date.isoformat(),
        "mode": "dry-run",
        "input_sources": input_paths.as_log_dict(),
        "approved_by": None,
    }
    _structured_log(
        logging.INFO,
        "attendance_dry_run_started",
        **common_log_fields,
    )

    try:
        evaluation = build_candidates(
            target_date,
            load_training_classes(input_paths.training_classes),
            load_participants(input_paths.participants),
            load_punch_records(input_paths.punch_records),
            load_slack_absence_posts(input_paths.slack_absence_posts),
        )
        suffix = target_date.isoformat()
        markdown_path = output_dir / f"attendance_dry_run_{suffix}.md"
        csv_path = output_dir / f"attendance_candidates_{suffix}.csv"
        write_candidate_csv(csv_path, evaluation.candidates)
        write_markdown_report(
            markdown_path,
            target_date,
            evaluation.candidates,
            evaluation.warnings,
            input_paths,
            run_id=actual_run_id,
            operator=operator,
            started_at=started_at,
        )
    except Exception as exc:
        _structured_log(
            logging.ERROR,
            "attendance_dry_run_failed",
            **common_log_fields,
            errors=[str(exc)],
            execution_result="failed",
        )
        raise

    counts = Counter(item.classification for item in evaluation.candidates)
    _structured_log(
        logging.INFO,
        "attendance_dry_run_completed",
        **common_log_fields,
        result_counts={
            classification: counts[classification]
            for classification in CLASSIFICATION_ORDER
        },
        warnings=list(evaluation.warnings),
        errors=[],
        execution_result="completed",
    )
    return DryRunResult(
        run_id=actual_run_id,
        target_date=target_date,
        candidates=evaluation.candidates,
        warnings=evaluation.warnings,
        markdown_path=markdown_path,
        csv_path=csv_path,
    )
