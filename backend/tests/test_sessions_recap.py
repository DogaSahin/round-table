from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.sessions.models import GameSession, SessionLog
from app.modules.sessions.recap import compile_recap


def _make_session_with_logs(db) -> GameSession:
    campaign = Campaign(name="Test Campaign", active=True)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    row = GameSession(campaign_id=campaign.id, number=1, title="Session One")
    db.add(row)
    db.commit()
    db.refresh(row)

    row.logs.append(SessionLog(text="Goblins ambush the party.", tag="combat"))
    row.logs.append(SessionLog(text="The party negotiates with the innkeeper.", tag="roleplay"))
    row.logs.append(SessionLog(text="200 gold found in the chest.", tag="loot"))
    row.logs.append(SessionLog(text="Who sent the assassin?", tag="thread"))
    row.logs.append(SessionLog(text="Scratch note, not part of the story.", tag="none"))
    db.commit()
    db.refresh(row)
    return row


def test_compile_recap_groups_by_tag_in_fixed_order() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        row = _make_session_with_logs(db)
        text = compile_recap(row.logs)

        combat_idx = text.index("## Combat")
        roleplay_idx = text.index("## Roleplay")
        loot_idx = text.index("## Loot")
        threads_idx = text.index("## Threads")
        assert combat_idx < roleplay_idx < loot_idx < threads_idx
        assert "Goblins ambush the party." in text
        assert "Scratch note, not part of the story." not in text
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_compile_recap_respects_tag_filter() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        row = _make_session_with_logs(db)
        text = compile_recap(row.logs, tags={"combat"})

        assert "## Combat" in text
        assert "## Roleplay" not in text
        assert "## Loot" not in text
        assert "## Threads" not in text
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_compile_recap_empty_logs_returns_empty_string() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = Campaign(name="Test Campaign", active=True)
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        row = GameSession(campaign_id=campaign.id, number=1, title="Empty Session")
        db.add(row)
        db.commit()
        db.refresh(row)

        assert compile_recap(row.logs) == ""
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
