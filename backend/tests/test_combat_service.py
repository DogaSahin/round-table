# backend/tests/test_combat_service.py
from __future__ import annotations

import json

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.combat import service
from app.modules.combat.models import Combatant, Encounter


def _make_campaign(db) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def _add_combatant(db, encounter: Encounter, name: str, **overrides) -> Combatant:
    defaults = dict(
        initiative=0,
        hp_current=0,
        hp_max=0,
        ac=None,
        is_pc=False,
        visible_to_players=False,
        npc_id=None,
    )
    defaults.update(overrides)
    return service.add_combatant(db, encounter, name, **defaults)


def test_create_and_delete_encounter_cascades_combatants() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Goblin Ambush")
        c1 = _add_combatant(db, encounter, "Goblin 1")
        c2 = _add_combatant(db, encounter, "Goblin 2")
        c1_id, c2_id = c1.id, c2.id

        service.delete_encounter(db, encounter)

        assert db.get(Combatant, c1_id) is None
        assert db.get(Combatant, c2_id) is None
        assert service.roster(db, campaign.id) == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_owned_encounter_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        encounter = service.create_encounter(db, c1.id, "Encounter")

        assert service.owned_encounter(db, encounter.id, c1.id) is not None
        assert service.owned_encounter(db, encounter.id, c2.id) is None
        assert service.owned_encounter(db, 999_999, c1.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_owned_combatant_traverses_encounter_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        encounter = service.create_encounter(db, c1.id, "Encounter")
        combatant = _add_combatant(db, encounter, "Goblin")

        assert service.owned_combatant(db, combatant.id, c1.id) is not None
        assert service.owned_combatant(db, combatant.id, c2.id) is None
        assert service.owned_combatant(db, 999_999, c1.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_set_active_encounter_isolated_per_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        e1a = service.create_encounter(db, c1.id, "E1A")
        e1b = service.create_encounter(db, c1.id, "E1B")
        e2a = service.create_encounter(db, c2.id, "E2A")

        service.set_active_encounter(db, c1.id, e1a)
        db.refresh(e1a)
        db.refresh(e1b)
        db.refresh(e2a)
        assert e1a.is_active is True
        assert e1b.is_active is False
        assert e2a.is_active is False

        # Activating an encounter in campaign 2 must not touch campaign 1's rows.
        service.set_active_encounter(db, c2.id, e2a)
        db.refresh(e1a)
        db.refresh(e2a)
        assert e1a.is_active is True
        assert e2a.is_active is True

        # Switching the active encounter within campaign 1 clears the old one.
        service.set_active_encounter(db, c1.id, e1b)
        db.refresh(e1a)
        db.refresh(e1b)
        db.refresh(e2a)
        assert e1a.is_active is False
        assert e1b.is_active is True
        assert e2a.is_active is True
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_add_combatant_sort_order_increments() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")

        c1 = _add_combatant(db, encounter, "First")
        assert c1.sort_order == 0

        db.refresh(encounter)
        c2 = _add_combatant(db, encounter, "Second")
        assert c2.sort_order == 1

        db.refresh(encounter)
        c3 = _add_combatant(db, encounter, "Third")
        assert c3.sort_order == 2
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_apply_damage_and_heal_clamp_normally() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")
        combatant = _add_combatant(db, encounter, "Fighter", hp_current=10, hp_max=10)

        damaged = service.apply_damage(db, combatant, 25)
        assert damaged.hp_current == 0

        healed = service.apply_heal(db, combatant, 100)
        assert healed.hp_current == 10
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_apply_damage_and_heal_no_cap_when_hp_max_zero() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")
        combatant = _add_combatant(db, encounter, "Swarm", hp_current=0, hp_max=0)

        healed = service.apply_heal(db, combatant, 500)
        assert healed.hp_current == 500

        damaged = service.apply_damage(db, combatant, 10_000)
        assert damaged.hp_current == 0
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_apply_condition_add_is_idempotent_and_remove_absent_is_noop() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")
        combatant = _add_combatant(db, encounter, "Fighter")

        service.apply_condition(db, combatant, "prone", "add")
        service.apply_condition(db, combatant, "prone", "add")
        assert service.get_conditions(combatant) == ["prone"]

        # Removing a condition that isn't present is a no-op, not an error.
        service.apply_condition(db, combatant, "blinded", "remove")
        assert service.get_conditions(combatant) == ["prone"]

        service.apply_condition(db, combatant, "prone", "remove")
        assert service.get_conditions(combatant) == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_get_conditions_never_raises_on_malformed_json() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")
        combatant = _add_combatant(db, encounter, "Fighter")

        combatant.conditions_json = "not valid json {{{"
        assert service.get_conditions(combatant) == []

        combatant.conditions_json = json.dumps({"not": "a list"})
        assert service.get_conditions(combatant) == []

        combatant.conditions_json = json.dumps(42)
        assert service.get_conditions(combatant) == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_next_turn_uses_sort_order_not_insertion_order() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")

        c1 = _add_combatant(db, encounter, "First")
        db.refresh(encounter)
        c2 = _add_combatant(db, encounter, "Second")
        db.refresh(encounter)
        c3 = _add_combatant(db, encounter, "Third")
        db.refresh(encounter)

        # Insertion order is c1, c2, c3 but reorder makes turn order c3, c1, c2.
        service.reorder(db, encounter, [c3.id, c1.id, c2.id])
        db.refresh(encounter)

        encounter = service.next_turn(db, encounter)
        assert encounter.active_combatant_id == c3.id
        assert encounter.round == 1

        encounter = service.next_turn(db, encounter)
        assert encounter.active_combatant_id == c1.id
        assert encounter.round == 1

        encounter = service.next_turn(db, encounter)
        assert encounter.active_combatant_id == c2.id
        assert encounter.round == 1

        # Wrapping past the last combatant (by sort_order) advances the round.
        encounter = service.next_turn(db, encounter)
        assert encounter.active_combatant_id == c3.id
        assert encounter.round == 2
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_delete_combatant_reassigns_active_marker_to_next_in_sort_order() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")

        _add_combatant(db, encounter, "First")
        db.refresh(encounter)
        c2 = _add_combatant(db, encounter, "Second")
        db.refresh(encounter)
        c3 = _add_combatant(db, encounter, "Third")
        db.refresh(encounter)

        encounter.active_combatant_id = c2.id
        db.commit()
        db.refresh(encounter)

        service.delete_combatant(db, encounter, c2)
        db.refresh(encounter)

        assert encounter.active_combatant_id == c3.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_delete_combatant_wraps_to_first_when_active_was_last() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")

        c1 = _add_combatant(db, encounter, "First")
        db.refresh(encounter)
        _add_combatant(db, encounter, "Second")
        db.refresh(encounter)
        c3 = _add_combatant(db, encounter, "Third")
        db.refresh(encounter)

        encounter.active_combatant_id = c3.id
        db.commit()
        db.refresh(encounter)

        service.delete_combatant(db, encounter, c3)
        db.refresh(encounter)

        assert encounter.active_combatant_id == c1.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_delete_combatant_clears_marker_when_last_combatant_removed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")
        c1 = _add_combatant(db, encounter, "Only")

        encounter.active_combatant_id = c1.id
        db.commit()
        db.refresh(encounter)

        service.delete_combatant(db, encounter, c1)
        db.refresh(encounter)

        assert encounter.active_combatant_id is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_delete_combatant_leaves_marker_untouched_when_not_active() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")

        c1 = _add_combatant(db, encounter, "First")
        db.refresh(encounter)
        c2 = _add_combatant(db, encounter, "Second")
        db.refresh(encounter)

        encounter.active_combatant_id = c1.id
        db.commit()
        db.refresh(encounter)

        service.delete_combatant(db, encounter, c2)
        db.refresh(encounter)

        assert encounter.active_combatant_id == c1.id
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_reorder_appends_omitted_combatants_preserving_relative_order() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")

        c1 = _add_combatant(db, encounter, "A")
        db.refresh(encounter)
        c2 = _add_combatant(db, encounter, "B")
        db.refresh(encounter)
        c3 = _add_combatant(db, encounter, "C")
        db.refresh(encounter)
        c4 = _add_combatant(db, encounter, "D")
        db.refresh(encounter)

        # Partial order: only c3, c1 given. c2 and c4 (omitted) must be appended
        # after them, preserving their original relative order (c2 before c4).
        service.reorder(db, encounter, [c3.id, c1.id])
        db.refresh(encounter)

        ordered = sorted(encounter.combatants, key=lambda c: (c.sort_order, c.id))
        assert [c.id for c in ordered] == [c3.id, c1.id, c2.id, c4.id]
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_reorder_accepts_full_id_list() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        encounter = service.create_encounter(db, campaign.id, "Encounter")

        c1 = _add_combatant(db, encounter, "A")
        db.refresh(encounter)
        c2 = _add_combatant(db, encounter, "B")
        db.refresh(encounter)
        c3 = _add_combatant(db, encounter, "C")
        db.refresh(encounter)

        service.reorder(db, encounter, [c3.id, c2.id, c1.id])
        db.refresh(encounter)

        ordered = sorted(encounter.combatants, key=lambda c: (c.sort_order, c.id))
        assert [c.id for c in ordered] == [c3.id, c2.id, c1.id]
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
