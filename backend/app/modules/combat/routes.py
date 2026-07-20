# backend/app/modules/combat/routes.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.campaigns import get_active_campaign
from app.core.database import get_db
from app.core.models import Campaign
from app.core.realtime import broadcast
from app.core.realtime.manager import manager
from app.engine.encounter import hp_band
from app.modules.combat import service
from app.modules.combat.models import Combatant, Encounter
from app.modules.combat.schemas import (
    CombatantCreate,
    CombatantOut,
    CombatantUpdate,
    ConditionRequest,
    DamageRequest,
    EncounterCreate,
    EncounterDetailOut,
    EncounterListItemOut,
    EncounterUpdate,
    HealRequest,
    PlayerCombatantOut,
    PlayerEncounterOut,
    ReorderRequest,
    SetAcRequest,
)
from app.shared.errors import NotFound

router = APIRouter(prefix="/api/combat", tags=["combat"])


def _combatant_out(combatant: Combatant) -> CombatantOut:
    return CombatantOut(
        id=combatant.id,
        name=combatant.name,
        initiative=combatant.initiative,
        hp_current=combatant.hp_current,
        hp_max=combatant.hp_max,
        ac=combatant.ac,
        conditions=service.get_conditions(combatant),
        concentration=combatant.concentration,
        sort_order=combatant.sort_order,
        is_pc=combatant.is_pc,
        visible_to_players=combatant.visible_to_players,
        npc_id=combatant.npc_id,
        token_id=combatant.token_id,
    )


def _encounter_out(encounter: Encounter) -> EncounterDetailOut:
    return EncounterDetailOut(
        id=encounter.id,
        name=encounter.name,
        round=encounter.round,
        active_combatant_id=encounter.active_combatant_id,
        is_active=encounter.is_active,
        combatants=[_combatant_out(c) for c in encounter.combatants],
    )


def _list_item_out(encounter: Encounter) -> EncounterListItemOut:
    return EncounterListItemOut(
        id=encounter.id,
        name=encounter.name,
        round=encounter.round,
        is_active=encounter.is_active,
    )


def _player_combatant_out(combatant: Combatant, active_id: int | None) -> PlayerCombatantOut:
    visible = combatant.visible_to_players
    return PlayerCombatantOut(
        id=combatant.id,
        name=combatant.name,
        is_pc=combatant.is_pc,
        is_active=combatant.id == active_id,
        band=hp_band(combatant.hp_current, combatant.hp_max),  # type: ignore[arg-type]
        hp_current=combatant.hp_current if visible else None,
        hp_max=combatant.hp_max if visible else None,
    )


def _player_out(encounter: Encounter) -> PlayerEncounterOut:
    return PlayerEncounterOut(
        id=encounter.id,
        name=encounter.name,
        round=encounter.round,
        is_active=encounter.is_active,
        combatants=[
            _player_combatant_out(c, encounter.active_combatant_id) for c in encounter.combatants
        ],
    )


def _get_owned_encounter(db: Session, encounter_id: int, campaign: Campaign) -> Encounter:
    row = service.owned_encounter(db, encounter_id, campaign.id)
    if row is None:
        raise NotFound(f"encounter {encounter_id} not found")
    return row


def _get_owned_combatant(db: Session, combatant_id: int, campaign: Campaign) -> Combatant:
    row = service.owned_combatant(db, combatant_id, campaign.id)
    if row is None:
        raise NotFound(f"combatant {combatant_id} not found")
    return row


async def _notify(encounter_id: int) -> None:
    await manager.publish(
        f"combat:{encounter_id}", {"action": "combat_changed", "encounter_id": encounter_id}
    )


@router.post("", response_model=EncounterDetailOut)
def create_encounter(
    payload: EncounterCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> EncounterDetailOut:
    row = service.create_encounter(db, campaign.id, payload.name)
    return _encounter_out(row)


@router.get("", response_model=list[EncounterListItemOut])
def list_encounters(
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> list[EncounterListItemOut]:
    rows = service.roster(db, campaign.id)
    return [_list_item_out(r) for r in rows]


@router.get("/{encounter_id}", response_model=EncounterDetailOut)
def detail(
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> EncounterDetailOut:
    return _encounter_out(_get_owned_encounter(db, encounter_id, campaign))


@router.patch("/{encounter_id}", response_model=EncounterDetailOut)
async def update_encounter(
    encounter_id: int,
    payload: EncounterUpdate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> EncounterDetailOut:
    row = _get_owned_encounter(db, encounter_id, campaign)
    row = service.update_encounter(db, row, payload.name)
    await _notify(encounter_id)
    return _encounter_out(row)


@router.delete("/{encounter_id}", status_code=204, response_model=None)
def delete_encounter(
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    row = _get_owned_encounter(db, encounter_id, campaign)
    service.delete_encounter(db, row)


@router.post("/{encounter_id}/activate", response_model=EncounterDetailOut)
async def activate(
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> EncounterDetailOut:
    row = _get_owned_encounter(db, encounter_id, campaign)
    row = service.set_active_encounter(db, campaign.id, row)
    broadcast.set_active_encounter(db, campaign.id, row.id)
    await broadcast.publish_changed(campaign.id)
    await _notify(encounter_id)
    return _encounter_out(row)


@router.get("/{encounter_id}/player", response_model=PlayerEncounterOut)
def player_view(
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> PlayerEncounterOut:
    row = _get_owned_encounter(db, encounter_id, campaign)
    return _player_out(row)


@router.post("/{encounter_id}/sort", response_model=EncounterDetailOut)
async def sort_by_initiative(
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> EncounterDetailOut:
    row = _get_owned_encounter(db, encounter_id, campaign)
    row = service.sort_by_initiative(db, row)
    await _notify(encounter_id)
    return _encounter_out(row)


@router.post("/{encounter_id}/reorder", response_model=EncounterDetailOut)
async def reorder(
    encounter_id: int,
    payload: ReorderRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> EncounterDetailOut:
    row = _get_owned_encounter(db, encounter_id, campaign)
    row = service.reorder(db, row, payload.order)
    await _notify(encounter_id)
    return _encounter_out(row)


@router.post("/{encounter_id}/next-turn", response_model=EncounterDetailOut)
async def next_turn(
    encounter_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> EncounterDetailOut:
    row = _get_owned_encounter(db, encounter_id, campaign)
    row = service.next_turn(db, row)
    await _notify(encounter_id)
    return _encounter_out(row)


@router.post("/{encounter_id}/combatants", response_model=CombatantOut)
async def add_combatant(
    encounter_id: int,
    payload: CombatantCreate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> CombatantOut:
    encounter = _get_owned_encounter(db, encounter_id, campaign)
    combatant = service.add_combatant(
        db,
        encounter,
        payload.name,
        payload.initiative,
        payload.hp_current,
        payload.hp_max,
        payload.ac,
        payload.is_pc,
        payload.visible_to_players,
        payload.npc_id,
    )
    await _notify(encounter_id)
    return _combatant_out(combatant)


@router.patch("/combatants/{combatant_id}", response_model=CombatantOut)
async def update_combatant(
    combatant_id: int,
    payload: CombatantUpdate,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> CombatantOut:
    combatant = _get_owned_combatant(db, combatant_id, campaign)
    encounter_id = combatant.encounter_id
    combatant = service.update_combatant(
        db,
        combatant,
        payload.name,
        payload.initiative,
        payload.is_pc,
        payload.visible_to_players,
        payload.npc_id,
    )
    await _notify(encounter_id)
    return _combatant_out(combatant)


@router.delete("/combatants/{combatant_id}", status_code=204, response_model=None)
async def delete_combatant(
    combatant_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> None:
    combatant = _get_owned_combatant(db, combatant_id, campaign)
    encounter = combatant.encounter
    encounter_id = encounter.id
    service.delete_combatant(db, encounter, combatant)
    await _notify(encounter_id)


@router.post("/combatants/{combatant_id}/damage", response_model=CombatantOut)
async def damage(
    combatant_id: int,
    payload: DamageRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> CombatantOut:
    combatant = _get_owned_combatant(db, combatant_id, campaign)
    encounter_id = combatant.encounter_id
    combatant = service.apply_damage(db, combatant, payload.amount)
    await _notify(encounter_id)
    return _combatant_out(combatant)


@router.post("/combatants/{combatant_id}/heal", response_model=CombatantOut)
async def heal(
    combatant_id: int,
    payload: HealRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> CombatantOut:
    combatant = _get_owned_combatant(db, combatant_id, campaign)
    encounter_id = combatant.encounter_id
    combatant = service.apply_heal(db, combatant, payload.amount)
    await _notify(encounter_id)
    return _combatant_out(combatant)


@router.post("/combatants/{combatant_id}/ac", response_model=CombatantOut)
async def set_ac(
    combatant_id: int,
    payload: SetAcRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> CombatantOut:
    combatant = _get_owned_combatant(db, combatant_id, campaign)
    encounter_id = combatant.encounter_id
    combatant = service.set_ac(db, combatant, payload.ac)
    await _notify(encounter_id)
    return _combatant_out(combatant)


@router.post("/combatants/{combatant_id}/condition", response_model=CombatantOut)
async def apply_condition(
    combatant_id: int,
    payload: ConditionRequest,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> CombatantOut:
    combatant = _get_owned_combatant(db, combatant_id, campaign)
    encounter_id = combatant.encounter_id
    combatant = service.apply_condition(db, combatant, payload.name, payload.op)
    await _notify(encounter_id)
    return _combatant_out(combatant)


@router.post("/combatants/{combatant_id}/concentration", response_model=CombatantOut)
async def toggle_concentration(
    combatant_id: int,
    db: Session = Depends(get_db),
    campaign: Campaign = Depends(get_active_campaign),
) -> CombatantOut:
    combatant = _get_owned_combatant(db, combatant_id, campaign)
    encounter_id = combatant.encounter_id
    combatant = service.toggle_concentration(db, combatant)
    await _notify(encounter_id)
    return _combatant_out(combatant)
