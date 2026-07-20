from __future__ import annotations

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.combat.models import Combatant, Encounter


def _make_campaign(session) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


def test_encounter_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        encounter = Encounter(campaign_id=campaign.id, name="Test Encounter")
        session.add(encounter)
        session.commit()
        session.refresh(encounter)

        assert encounter.round == 1
        assert encounter.is_active is False
        assert encounter.active_combatant_id is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_combatant_defaults() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        encounter = Encounter(campaign_id=campaign.id, name="Test Encounter")
        session.add(encounter)
        session.commit()
        session.refresh(encounter)

        combatant = Combatant(encounter_id=encounter.id, name="Test Combatant")
        session.add(combatant)
        session.commit()
        session.refresh(combatant)

        assert combatant.initiative == 0
        assert combatant.hp_current == 0
        assert combatant.hp_max == 0
        assert combatant.ac is None
        assert combatant.conditions_json == "[]"
        assert combatant.concentration is False
        assert combatant.sort_order == 0
        assert combatant.is_pc is False
        assert combatant.visible_to_players is False
        assert combatant.npc_id is None
        assert combatant.token_id is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_encounter_cascade_delete_combatants() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        campaign = _make_campaign(session)
        encounter = Encounter(campaign_id=campaign.id, name="Test Encounter")
        session.add(encounter)
        session.commit()
        session.refresh(encounter)

        combatant1 = Combatant(encounter_id=encounter.id, name="Combatant 1")
        combatant2 = Combatant(encounter_id=encounter.id, name="Combatant 2")
        session.add(combatant1)
        session.add(combatant2)
        session.commit()
        session.refresh(combatant1)
        session.refresh(combatant2)

        combatant1_id = combatant1.id
        combatant2_id = combatant2.id

        # Delete the encounter
        session.delete(encounter)
        session.commit()

        # Verify combatants are deleted
        found_combatant1 = session.query(Combatant).filter_by(id=combatant1_id).first()
        found_combatant2 = session.query(Combatant).filter_by(id=combatant2_id).first()

        assert found_combatant1 is None
        assert found_combatant2 is None
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
