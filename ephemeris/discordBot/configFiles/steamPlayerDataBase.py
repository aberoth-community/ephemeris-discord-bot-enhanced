import time
from typing import Dict, List, Optional, Tuple

from peewee import CharField, IntegerField, Model, SqliteDatabase, fn


steam_db = SqliteDatabase("ephemeris\\discordBot\\configFiles\\steam_player_DB.db")

REALM_KEYS = ["black", "green", "red", "purple", "yellow", "cyan", "blue"]
REALM_LABELS = {realm: realm.capitalize() for realm in REALM_KEYS}


class BaseModel(Model):
    class Meta:
        database = steam_db


class SteamPlayerCount(BaseModel):
    ts = IntegerField(index=True)
    realm = CharField(index=True)
    count = IntegerField()

    class Meta:
        indexes = ((("ts", "realm"), True),)


class SteamPlayerMenu(BaseModel):
    message_id = CharField(primary_key=True)
    channel_id = CharField()
    guild_id = CharField()
    include_graph = IntegerField(default=0)
    range_hours = IntegerField(default=24)


steam_db.connect()
steam_db.create_tables([SteamPlayerCount, SteamPlayerMenu])


def record_player_counts(ts: Optional[int], counts: Dict[str, int]) -> int:
    if ts is None:
        ts = int(time.time())
    SteamPlayerCount.delete().where(SteamPlayerCount.ts == ts).execute()
    rows = []
    for realm in REALM_KEYS:
        rows.append(
            {
                "ts": ts,
                "realm": realm,
                "count": int(counts.get(realm, 0)),
            }
        )
    SteamPlayerCount.insert_many(rows).execute()
    return ts


def _get_counts_for_ts(ts: int) -> Dict[str, int]:
    counts = {realm: 0 for realm in REALM_KEYS}
    for row in SteamPlayerCount.select().where(SteamPlayerCount.ts == ts):
        counts[row.realm] = row.count
    return counts


def get_latest_player_counts() -> Optional[Tuple[int, Dict[str, int]]]:
    row = (
        SteamPlayerCount.select(SteamPlayerCount.ts)
        .order_by(SteamPlayerCount.ts.desc())
        .first()
    )
    if row is None:
        return None
    return row.ts, _get_counts_for_ts(row.ts)


def get_player_counts_at_or_before(ts: int) -> Optional[Tuple[int, Dict[str, int]]]:
    max_ts = (
        SteamPlayerCount.select(fn.MAX(SteamPlayerCount.ts))
        .where(SteamPlayerCount.ts <= ts)
        .scalar()
    )
    if max_ts is None:
        return None
    return max_ts, _get_counts_for_ts(max_ts)


def get_player_counts_before(ts: int) -> Optional[Tuple[int, Dict[str, int]]]:
    max_ts = (
        SteamPlayerCount.select(fn.MAX(SteamPlayerCount.ts))
        .where(SteamPlayerCount.ts < ts)
        .scalar()
    )
    if max_ts is None:
        return None
    return max_ts, _get_counts_for_ts(max_ts)


def get_player_count_series(
    start_ts: int, end_ts: int
) -> Tuple[List[int], Dict[str, List[int]]]:
    per_ts = {}
    query = (
        SteamPlayerCount.select(
            SteamPlayerCount.ts,
            SteamPlayerCount.realm,
            SteamPlayerCount.count,
        )
        .where(SteamPlayerCount.ts.between(start_ts, end_ts))
        .order_by(SteamPlayerCount.ts)
    )
    for row in query:
        per_ts.setdefault(row.ts, {})[row.realm] = row.count
    timestamps = sorted(per_ts.keys())
    series = {realm: [] for realm in REALM_KEYS}
    for ts in timestamps:
        snapshot = per_ts[ts]
        for realm in REALM_KEYS:
            series[realm].append(snapshot.get(realm, 0))
    return timestamps, series


def upsert_steam_menu(
    message_id: str,
    channel_id: str,
    guild_id: str,
    include_graph: int,
    range_hours: int,
) -> None:
    SteamPlayerMenu.insert(
        message_id=str(message_id),
        channel_id=str(channel_id),
        guild_id=str(guild_id),
        include_graph=int(include_graph),
        range_hours=int(range_hours),
    ).on_conflict(
        conflict_target=[SteamPlayerMenu.message_id],
        update={
            SteamPlayerMenu.channel_id: str(channel_id),
            SteamPlayerMenu.guild_id: str(guild_id),
            SteamPlayerMenu.include_graph: int(include_graph),
            SteamPlayerMenu.range_hours: int(range_hours),
        },
    ).execute()


def get_steam_menu(message_id: str) -> Optional[SteamPlayerMenu]:
    return SteamPlayerMenu.get_or_none(
        SteamPlayerMenu.message_id == str(message_id)
    )


def get_all_steam_menus() -> List[SteamPlayerMenu]:
    return list(SteamPlayerMenu.select())


def delete_steam_menu(message_id: str) -> None:
    SteamPlayerMenu.delete().where(
        SteamPlayerMenu.message_id == str(message_id)
    ).execute()
