# backend/app/modules/combat/service.py
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.engine.encounter import advance_turn, clamp_hp
from app.modules.combat.models import Combatant, Encounter


def roster(db: Session, campaign_id: int) -> list[Encounter]:
    return db.query(Encounter).filter_by(campaign_id=campaign_id).order_by(Encounter.name).all()


def owned_encounter(db: Session, encounter_id: int, campaign_id: int) -> Encounter | None:
    row = db.get(Encounter, encounter_id)
    return row if row is not None and row.campaign_id == campaign_id else None


def owned_combatant(db: Session, combatant_id: int, campaign_id: int) -> Combatant | None:
    row = db.get(Combatant, combatant_id)
    if row is None or row.encounter.campaign_id != campaign_id:
        return None
    return row


def create_encounter(db: Session, campaign_id: int, name: str) -> Encounter:
    row = Encounter(campaign_id=campaign_id, name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_encounter(db: Session, encounter_row: Encounter, name: str | None) -> Encounter:
    if name is not None:
        encounter_row.name = name
    db.commit()
    db.refresh(encounter_row)
    return encounter_row


def delete_encounter(db: Session, encounter_row: Encounter) -> None:
    db.delete(encounter_row)
    db.commit()


def set_active_encounter(db: Session, campaign_id: int, encounter_row: Encounter) -> Encounter:
    db.query(Encounter).filter_by(campaign_id=campaign_id).update({"is_active": False})
    encounter_row.is_active = True
    db.commit()
    db.refresh(encounter_row)
    return encounter_row


def add_combatant(
    db: Session,
    encounter_row: Encounter,
    name: str,
    initiative: int,
    hp_current: int,
    hp_max: int,
    ac: int | None,
    is_pc: bool,
    visible_to_players: bool,
    npc_id: int | None,
) -> Combatant:
    next_order = max((c.sort_order for c in encounter_row.combatants), default=-1) + 1
    row = Combatant(
        encounter_id=encounter_row.id,
        name=name,
        initiative=initiative,
        hp_current=hp_current,
        hp_max=hp_max,
        ac=ac,
        is_pc=is_pc,
        visible_to_players=visible_to_players,
        npc_id=npc_id,
        sort_order=next_order,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_combatant(
    db: Session,
    combatant: Combatant,
    name: str | None,
    initiative: int | None,
    is_pc: bool | None,
    visible_to_players: bool | None,
    npc_id: int | None,
) -> Combatant:
    if name is not None:
        combatant.name = name
    if initiative is not None:
        combatant.initiative = initiative
    if is_pc is not None:
        combatant.is_pc = is_pc
    if visible_to_players is not None:
        combatant.visible_to_players = visible_to_players
    if npc_id is not None:
        combatant.npc_id = npc_id
    db.commit()
    db.refresh(combatant)
    return combatant


def delete_combatant(db: Session, encounter_row: Encounter, combatant: Combatant) -> None:
    was_active = encounter_row.active_combatant_id == combatant.id
    next_active_id: int | None = None
    if was_active:
        ordered = sorted(encounter_row.combatants, key=lambda c: (c.sort_order, c.id))
        if len(ordered) > 1:
            idx = next(i for i, c in enumerate(ordered) if c.id == combatant.id)
            next_active_id = ordered[(idx + 1) % len(ordered)].id
    db.delete(combatant)
    db.commit()
    if was_active:
        db.refresh(encounter_row)
        encounter_row.active_combatant_id = next_active_id
        db.commit()
        db.refresh(encounter_row)


def sort_by_initiative(db: Session, encounter_row: Encounter) -> Encounter:
    ordered = sorted(encounter_row.combatants, key=lambda c: (-c.initiative, c.id))
    for i, c in enumerate(ordered):
        c.sort_order = i
    db.commit()
    db.refresh(encounter_row)
    return encounter_row


def reorder(db: Session, encounter_row: Encounter, order: list[int]) -> Encounter:
    by_id = {c.id: c for c in encounter_row.combatants}
    idx = 0
    for combatant_id in order:
        c = by_id.pop(combatant_id, None)
        if c is not None:
            c.sort_order = idx
            idx += 1
    for c in sorted(by_id.values(), key=lambda c: (c.sort_order, c.id)):
        c.sort_order = idx
        idx += 1
    db.commit()
    db.refresh(encounter_row)
    return encounter_row


def apply_damage(db: Session, combatant: Combatant, amount: int) -> Combatant:
    maximum = combatant.hp_max if combatant.hp_max > 0 else None
    combatant.hp_current = clamp_hp(combatant.hp_current - amount, maximum)
    db.commit()
    db.refresh(combatant)
    return combatant


def apply_heal(db: Session, combatant: Combatant, amount: int) -> Combatant:
    maximum = combatant.hp_max if combatant.hp_max > 0 else None
    combatant.hp_current = clamp_hp(combatant.hp_current + amount, maximum)
    db.commit()
    db.refresh(combatant)
    return combatant


def set_ac(db: Session, combatant: Combatant, ac: int | None) -> Combatant:
    combatant.ac = ac
    db.commit()
    db.refresh(combatant)
    return combatant


def toggle_concentration(db: Session, combatant: Combatant) -> Combatant:
    combatant.concentration = not combatant.concentration
    db.commit()
    db.refresh(combatant)
    return combatant


def get_conditions(combatant: Combatant) -> list[str]:
    try:
        data = json.loads(combatant.conditions_json)
    except (json.JSONDecodeError, TypeError):
        return []
    return data if isinstance(data, list) else []


def apply_condition(db: Session, combatant: Combatant, name: str, op: str) -> Combatant:
    current = get_conditions(combatant)
    if op == "add":
        if name not in current:
            current.append(name)
    else:
        current = [c for c in current if c != name]
    combatant.conditions_json = json.dumps(current)
    db.commit()
    db.refresh(combatant)
    return combatant


def next_turn(db: Session, encounter_row: Encounter) -> Encounter:
    ordered_ids = [
        c.id for c in sorted(encounter_row.combatants, key=lambda c: (c.sort_order, c.id))
    ]
    new_active, new_round = advance_turn(
        encounter_row.active_combatant_id, ordered_ids, encounter_row.round
    )
    encounter_row.active_combatant_id = new_active
    encounter_row.round = new_round
    db.commit()
    db.refresh(encounter_row)
    return encounter_row
