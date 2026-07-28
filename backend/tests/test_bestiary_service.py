from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.database import Base, SessionLocal, engine
from app.core.models import Campaign
from app.modules.bestiary import service
from app.shared.statblock import AbilityScores, Speed, Statblock


def _make_campaign(db) -> Campaign:
    campaign = Campaign(name="Test Campaign", active=True)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def _statblock(creature_type: str = "beast", challenge_rating: float = 0.25) -> Statblock:
    return Statblock(
        size="Small",
        creature_type=creature_type,
        alignment="unaligned",
        armor_class=12,
        hit_points=7,
        hit_dice="2d6",
        speed=Speed(walk=30),
        ability_scores=AbilityScores(
            strength=8, dexterity=15, constitution=11, intelligence=2, wisdom=10, charisma=4
        ),
        challenge_rating=challenge_rating,
        experience_points=50,
    )


def test_create_monster_persists_statblock_and_denormalized_columns() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        statblock = _statblock(creature_type="beast", challenge_rating=0.5)

        row = service.create_monster(db, campaign.id, "Giant Rat", statblock, None)

        assert row.id is not None
        assert row.slug == "giant-rat"
        assert row.creature_type == "beast"
        assert row.challenge_rating == 0.5
        assert service.load_statblock(row) == statblock
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_unique_slug_appends_suffix_on_collision() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        service.create_monster(db, campaign.id, "Goblin", _statblock(), None)
        second = service.create_monster(db, campaign.id, "Goblin", _statblock(), None)

        assert second.slug == "goblin-2"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_update_monster_replaces_statblock_resyncs_columns_and_preserves_slug_on_rename() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_monster(db, campaign.id, "Goblin", _statblock(), None)
        original_slug = row.slug

        updated = service.update_monster(
            db,
            row,
            name="Goblin Boss",
            statblock=_statblock(creature_type="humanoid", challenge_rating=1.0),
            image_url="/media/goblin-boss.png",
        )

        assert updated.name == "Goblin Boss"
        assert updated.slug == original_slug
        assert updated.creature_type == "humanoid"
        assert updated.challenge_rating == 1.0
        assert updated.image_url == "/media/goblin-boss.png"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_set_favorite_toggles_both_directions() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_monster(db, campaign.id, "Goblin", _statblock(), None)
        assert row.is_favorite is False

        row = service.set_favorite(db, row, True)
        assert row.is_favorite is True

        row = service.set_favorite(db, row, False)
        assert row.is_favorite is False
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_delete_monster() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        row = service.create_monster(db, campaign.id, "Doomed", _statblock(), None)

        service.delete_monster(db, row)

        assert service.owned(db, row.id, campaign.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_owned_scoped_to_campaign() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        c1, c2 = _make_campaign(db), _make_campaign(db)
        row = service.create_monster(db, c1.id, "Goblin", _statblock(), None)

        assert service.owned(db, row.id, c1.id) is not None
        assert service.owned(db, row.id, c2.id) is None
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_roster_search_matches_name_and_creature_type() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        service.create_monster(
            db, campaign.id, "Giant Rat", _statblock(creature_type="beast"), None
        )
        service.create_monster(db, campaign.id, "Zombie", _statblock(creature_type="undead"), None)

        by_name = service.roster(db, campaign.id, "rat", None, None, None, False, "name")
        by_type = service.roster(db, campaign.id, "undead", None, None, None, False, "name")

        assert [m.name for m in by_name] == ["Giant Rat"]
        assert [m.name for m in by_type] == ["Zombie"]
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_roster_filters_by_type_cr_range_and_favorites_only() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        low = service.create_monster(
            db, campaign.id, "Rat", _statblock(creature_type="beast", challenge_rating=0.125), None
        )
        service.create_monster(
            db,
            campaign.id,
            "Owlbear",
            _statblock(creature_type="monstrosity", challenge_rating=3.0),
            None,
        )
        service.set_favorite(db, low, True)

        assert [
            m.name
            for m in service.roster(db, campaign.id, None, "beast", None, None, False, "name")
        ] == ["Rat"]
        assert [
            m.name for m in service.roster(db, campaign.id, None, None, 1.0, 5.0, False, "name")
        ] == ["Owlbear"]
        assert [
            m.name for m in service.roster(db, campaign.id, None, None, None, None, True, "name")
        ] == ["Rat"]
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_roster_sort_orders_by_name_cr_and_created_at() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        campaign = _make_campaign(db)
        zebra = service.create_monster(
            db, campaign.id, "Zebra Swarm", _statblock(challenge_rating=2.0), None
        )
        ant = service.create_monster(
            db, campaign.id, "Ant Swarm", _statblock(challenge_rating=0.25), None
        )
        # Force a deterministic created_at ordering instead of relying on real-time gaps.
        zebra.created_at = datetime.now(UTC) - timedelta(minutes=10)
        ant.created_at = datetime.now(UTC)
        db.commit()

        by_name = service.roster(db, campaign.id, None, None, None, None, False, "name")
        by_cr = service.roster(db, campaign.id, None, None, None, None, False, "cr")
        by_created = service.roster(db, campaign.id, None, None, None, None, False, "created_at")

        assert [m.name for m in by_name] == ["Ant Swarm", "Zebra Swarm"]
        assert [m.name for m in by_cr] == ["Ant Swarm", "Zebra Swarm"]
        assert [m.name for m in by_created] == ["Zebra Swarm", "Ant Swarm"]
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
