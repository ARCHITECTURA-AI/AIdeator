"""Migration script from JSON to SQLite."""

import json
import logging
from datetime import datetime
from pathlib import Path
from uuid import UUID

from db.base import db_session, initialize_db
from db.comments import add_comment
from db.ideas import save_idea
from db.reports import save_report
from db.runs import RunModel, save_run
from db.signals import save_signal
from models.comment import Comment
from models.idea import Idea
from models.report import Report
from models.run import Run

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("migration")

DATA_DIR = Path("data")


def migrate_ideas():
    path = DATA_DIR / "ideas.json"
    if not path.exists():
        return
    with open(path) as f:
        data = json.load(f)

    count = 0
    for row in data:
        idea_id_str = row["idea_id"]
        try:
            idea = Idea(
                title=row["title"],
                description=row["description"],
                target_user=row["target_user"],
                context=row["context"],
                tier=row.get("tier", "Bronze"),
                brand_hex=row.get("brand_hex", "#888888"),
            )
            idea.idea_id = UUID(idea_id_str)
            idea.created_at = datetime.fromisoformat(row["created_at"])
            save_idea(idea)
            count += 1
        except Exception as e:
            LOGGER.error(f"Failed to migrate idea {idea_id_str}: {e}")
    LOGGER.info(f"Migrated {count} ideas")


def migrate_runs():
    path = DATA_DIR / "runs.json"
    if not path.exists():
        return
    with open(path) as f:
        data = json.load(f)

    count = 0
    runs_data = data.get("runs", [])
    idempotency_data = data.get("idempotency", [])

    # Map idempotency keys for later
    idem_map = {
        (row["idea_id"], row["run_id"]): row["key"] for row in idempotency_data if "key" in row
    }

    for row in runs_data:
        try:
            run = Run(idea_id=UUID(row["idea_id"]), tier=row["tier"], mode=row["mode"])
            run.run_id = UUID(row["run_id"])
            run.status = row["status"]
            run.created_at = datetime.fromisoformat(row["created_at"])
            run.updated_at = datetime.fromisoformat(row["updated_at"])
            run.duration_ms = row.get("duration_ms")
            run.error_code = row.get("error_code")

            save_run(run)

            # Update idempotency key directly in DB if found
            key = idem_map.get((row["idea_id"], row["run_id"]))
            if key:
                session = db_session()
                model = session.query(RunModel).filter_by(run_id=str(run.run_id)).first()
                if model:
                    model.idempotency_key = key
                    session.commit()
                db_session.remove()

            count += 1
        except Exception as e:
            LOGGER.error(f"Failed to migrate run {row.get('run_id')}: {e}")
    LOGGER.info(f"Migrated {count} runs")


def migrate_reports():
    path = DATA_DIR / "reports.json"
    if not path.exists():
        return
    with open(path) as f:
        rows = json.load(f)

    count = 0
    for row in rows:
        try:
            report = Report.model_validate(row)
            save_report(report)
            count += 1
        except Exception as e:
            LOGGER.error(f"Failed to migrate report for run {row.get('run_id')}: {e}")
    LOGGER.info(f"Migrated {count} reports")


def migrate_signals():
    path = DATA_DIR / "signals.json"
    if not path.exists():
        return
    with open(path) as f:
        data = json.load(f)

    count = 0
    for run_id_str, signals in data.items():
        try:
            run_id = UUID(run_id_str)
            for signal in signals:
                save_signal(run_id, signal)
                count += 1
        except Exception as e:
            LOGGER.error(f"Failed to migrate signals for run {run_id_str}: {e}")
    LOGGER.info(f"Migrated {count} signals")


def migrate_comments():
    path = DATA_DIR / "comments.json"
    if not path.exists():
        return
    with open(path) as f:
        rows = json.load(f)

    count = 0
    for row in rows:
        try:
            comment = Comment(
                idea_id=UUID(row["idea_id"]), author=row["author"], content=row["content"]
            )
            comment.comment_id = UUID(row["comment_id"])
            comment.created_at = datetime.fromisoformat(row["created_at"])
            add_comment(comment)
            count += 1
        except Exception as e:
            LOGGER.error(f"Failed to migrate comment {row.get('comment_id')}: {e}")
    LOGGER.info(f"Migrated {count} comments")


def main():
    initialize_db()
    migrate_ideas()
    migrate_runs()
    migrate_reports()
    migrate_signals()
    migrate_comments()
    LOGGER.info("Migration complete!")


if __name__ == "__main__":
    main()
