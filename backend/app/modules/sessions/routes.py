# backend/app/modules/sessions/routes.py
from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.modules.sessions import service
from app.modules.sessions.models import GameSession, SessionLog
from app.modules.sessions.schemas import (
    LogCreate,
    RecapOut,
    RecapRequest,
    SessionCreate,
    SessionDetailOut,
    SessionListItemOut,
    SessionLogOut,
    SessionUpdate,
    Tag,
)
from app.shared.errors import NotFound

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _log_out(log: SessionLog) -> SessionLogOut:
    # log.tag is a plain `str` column (Task 1's models.py is frozen re: the old app's
    # schema); SessionLogOut.tag is the narrower `Tag` literal. The value is always one
    # of TAGS in practice (enforced by LogCreate on write) — this cast tells mypy what
    # the DB already guarantees, it doesn't change any runtime value.
    return SessionLogOut(
        id=log.id,
        text=log.text,
        tag=cast(Tag, log.tag),
        logged_at=log.logged_at,
        resolved_at=log.resolved_at,
    )


def _detail_out(session_row: GameSession) -> SessionDetailOut:
    return SessionDetailOut(
        id=session_row.id,
        number=session_row.number,
        date=session_row.date,
        title=session_row.title,
        summary=session_row.summary,
        status=session_row.status,
        logs=[_log_out(log) for log in session_row.logs],
    )


def _get_owned(db: Session, session_id: int, campaign: Campaign) -> GameSession:
    row = service.owned(db, session_id, campaign.id)
    if row is None:
        raise NotFound(f"session {session_id} not found")
    return row


def _get_owned_log(db: Session, log_id: int, campaign: Campaign) -> SessionLog:
    log = service.owned_log(db, log_id, campaign.id)
    if log is None:
        raise NotFound(f"session log {log_id} not found")
    return log


@router.post("", response_model=SessionDetailOut)
def create(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> SessionDetailOut:
    row = service.create_session(db, campaign.id, payload.title, payload.date)
    return _detail_out(row)


@router.get("", response_model=list[SessionListItemOut])
def list_sessions(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> list[SessionListItemOut]:
    rows = service.roster(db, campaign.id)
    return [
        SessionListItemOut(id=r.id, number=r.number, date=r.date, title=r.title, status=r.status)
        for r in rows
    ]


@router.get("/{session_id}", response_model=SessionDetailOut)
def detail(
    session_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> SessionDetailOut:
    return _detail_out(_get_owned(db, session_id, campaign))


@router.patch("/{session_id}", response_model=SessionDetailOut)
def update(
    session_id: int,
    payload: SessionUpdate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> SessionDetailOut:
    row = _get_owned(db, session_id, campaign)
    row = service.update_session(db, row, payload.title, payload.date, payload.summary)
    return _detail_out(row)


@router.delete("/{session_id}", status_code=204, response_model=None)
def delete(
    session_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    row = _get_owned(db, session_id, campaign)
    service.delete_session(db, row)


@router.post("/{session_id}/activate", response_model=SessionDetailOut)
def activate(
    session_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> SessionDetailOut:
    row = _get_owned(db, session_id, campaign)
    service.activate(db, row)
    return _detail_out(row)


@router.post("/{session_id}/logs", response_model=SessionLogOut)
def add_log(
    session_id: int,
    payload: LogCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> SessionLogOut:
    row = _get_owned(db, session_id, campaign)
    log = service.append_log(db, row, payload.text, payload.tag)
    return _log_out(log)


@router.delete("/logs/{log_id}", status_code=204, response_model=None)
def delete_log(
    log_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    log = _get_owned_log(db, log_id, campaign)
    service.delete_log(db, log)


@router.post("/logs/{log_id}/resolve", response_model=SessionLogOut)
def resolve(
    log_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> SessionLogOut:
    log = _get_owned_log(db, log_id, campaign)
    return _log_out(service.resolve_log(db, log))


@router.post("/logs/{log_id}/unresolve", response_model=SessionLogOut)
def unresolve(
    log_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> SessionLogOut:
    log = _get_owned_log(db, log_id, campaign)
    return _log_out(service.unresolve_log(db, log))


@router.post("/{session_id}/recap", response_model=RecapOut)
def recap(
    session_id: int,
    payload: RecapRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> RecapOut:
    row = _get_owned(db, session_id, campaign)
    # payload.tags is `list[Tag]` (Pydantic's Literal-constrained field); service.py's
    # signature is the broader `list[str]` since it has no FastAPI/Pydantic dependency.
    # `list` is invariant so mypy won't accept one for the other without this cast.
    text = service.compile_recap_for_session(row, cast(list[str], payload.tags))
    return RecapOut(text=text)
