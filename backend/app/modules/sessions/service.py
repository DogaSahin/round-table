# backend/app/modules/sessions/service.py
from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_type

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.sessions import recap
from app.modules.sessions.models import THREAD_TAG, GameSession, SessionLog
from app.shared.errors import Validation


def next_number(db: Session, campaign_id: int) -> int:
    """Session numbers run per campaign, not globally."""
    top = (
        db.query(func.max(GameSession.number))
        .filter(GameSession.campaign_id == campaign_id)
        .scalar()
    )
    return (top or 0) + 1


def roster(db: Session, campaign_id: int) -> list[GameSession]:
    return (
        db.query(GameSession)
        .filter_by(campaign_id=campaign_id)
        .order_by(GameSession.number.desc())
        .all()
    )


def owned(db: Session, session_id: int, campaign_id: int) -> GameSession | None:
    row = db.get(GameSession, session_id)
    return row if row is not None and row.campaign_id == campaign_id else None


def owned_log(db: Session, log_id: int, campaign_id: int) -> SessionLog | None:
    log = db.get(SessionLog, log_id)
    if log is None or log.session.campaign_id != campaign_id:
        return None
    return log


def create_session(
    db: Session, campaign_id: int, title: str, date: date_type | None
) -> GameSession:
    row = GameSession(
        campaign_id=campaign_id,
        number=next_number(db, campaign_id),
        date=date if date is not None else datetime.now(UTC).date(),
        title=title,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_session(
    db: Session,
    session_row: GameSession,
    title: str | None,
    date: date_type | None,
    summary: str | None,
) -> GameSession:
    if title is not None:
        session_row.title = title
    if date is not None:
        session_row.date = date
    if summary is not None:
        session_row.summary = summary
    db.commit()
    db.refresh(session_row)
    return session_row


def delete_session(db: Session, session_row: GameSession) -> None:
    db.delete(session_row)
    db.commit()


def activate(db: Session, session_row: GameSession) -> None:
    """Exactly one active session per campaign: activating demotes the incumbent.

    Enforced here rather than with a DB constraint — a partial unique index buys
    little on SQLite and fights Alembic.
    """
    db.query(GameSession).filter(
        GameSession.campaign_id == session_row.campaign_id,
        GameSession.status == "active",
        GameSession.id != session_row.id,
    ).update({"status": "done"}, synchronize_session=False)
    session_row.status = "active"
    db.commit()
    db.refresh(session_row)


def append_log(db: Session, session_row: GameSession, text: str, tag: str) -> SessionLog:
    log = SessionLog(session_id=session_row.id, text=text, tag=tag)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def delete_log(db: Session, log: SessionLog) -> None:
    db.delete(log)
    db.commit()


def resolve_log(db: Session, log: SessionLog) -> SessionLog:
    if log.tag != THREAD_TAG:
        raise Validation("only thread-tagged logs can be resolved")
    log.resolved_at = datetime.now(UTC)
    db.commit()
    db.refresh(log)
    return log


def unresolve_log(db: Session, log: SessionLog) -> SessionLog:
    if log.tag != THREAD_TAG:
        raise Validation("only thread-tagged logs can be resolved")
    log.resolved_at = None
    db.commit()
    db.refresh(log)
    return log


def compile_recap_for_session(session_row: GameSession, tags: list[str]) -> str:
    return recap.compile_recap(session_row.logs, set(tags) if tags else None)
