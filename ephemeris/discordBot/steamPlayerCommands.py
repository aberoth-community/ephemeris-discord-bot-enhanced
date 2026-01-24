import asyncio
import time
from typing import Optional

from .bot import *
from .helperFuncs import *
from .steamPlayerCount import get_steam_player_count
from .steamPlayerMenus import GRAPH_RANGE_CHOICES
from .steamPlayerReports import build_player_count_report
from .configFiles.steamPlayerDataBase import (
    get_latest_player_counts,
    record_player_counts,
)


async def _ensure_player_counts() -> bool:
    if get_latest_player_counts() is not None:
        return True
    try:
        counts = await asyncio.to_thread(get_steam_player_count)
        record_player_counts(None, counts)
        return True
    except BaseException:
        return False


def _apply_graph_error(message: str, graph_error: Optional[str]) -> str:
    if graph_error:
        return f"{message}\n**Graph:** {graph_error}"
    return message


@bot.tree.command(
    name="steam_player_counts",
    description="Shows current Steam player counts.",
)
@app_commands.allowed_installs(guilds=False, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    graph="Include a player count history graph",
    range_hours="Hours of history to graph (default 24)",
)
@app_commands.choices(
    range_hours=[
        discord.app_commands.Choice(name=label, value=hours)
        for (label, hours) in GRAPH_RANGE_CHOICES
    ]
)
async def steamPlayerCountsUser(
    interaction: discord.Interaction,
    graph: Optional[bool] = False,
    range_hours: Optional[discord.app_commands.Choice[int]] = None,
) -> None:
    userSettings = fetch_user_settings(interaction.user.id)
    whiteListed = False
    if userSettings:
        exp = userSettings.get("expiration")
        whiteListed = True if exp == -1 else exp > time.time()
    else:
        userSettings = newUserSettings(interaction.user.id, interaction.user.name)
        update_user_settings(interaction.user.id, userSettings)
    if not whiteListed and not disableWhitelisting:
        await interaction.response.send_message(
            content="**User does not have permission to use this command.**\nType `/permissions` for more information.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=False, thinking=True)
    if not await _ensure_player_counts():
        await interaction.followup.send(
            content="Unable to gather player counts right now.",
            ephemeral=True,
        )
        return

    hours_value = range_hours.value if range_hours else 24
    message, graph_buf, graph_error = build_player_count_report(
        include_graph=bool(graph),
        range_hours=hours_value,
    )
    message = _apply_graph_error(message, graph_error)

    log_usage(
        interaction=interaction,
        feature="steam",
        action="counts_user",
        details={"graph": bool(graph), "range_hours": hours_value},
    )

    chunks = splitMsg(message)
    graph_file = None
    if graph and graph_buf is not None and graph_error is None:
        graph_file = discord.File(fp=graph_buf, filename="steam_player_counts.png")

    if graph_file is not None:
        await interaction.followup.send(content=chunks[0], file=graph_file)
        for chunk in chunks[1:]:
            await interaction.followup.send(content=chunk)
    else:
        for chunk in chunks:
            await interaction.followup.send(content=chunk)


@bot.tree.command(
    name="steam_player_counts_guild",
    description="Shows current Steam player counts (guild install).",
)
@app_commands.allowed_installs(guilds=True, users=False)
@app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@app_commands.describe(
    graph="Include a player count history graph",
    range_hours="Hours of history to graph (default 24)",
)
@app_commands.choices(
    range_hours=[
        discord.app_commands.Choice(name=label, value=hours)
        for (label, hours) in GRAPH_RANGE_CHOICES
    ]
)
async def steamPlayerCountsGuild(
    interaction: discord.Interaction,
    graph: Optional[bool] = False,
    range_hours: Optional[discord.app_commands.Choice[int]] = None,
) -> None:
    noPermission = False
    exp = 0
    guildSettings = fetch_guild_settings(interaction.guild_id)
    if not guildSettings:
        guildSettings = newGuildSettings(interaction)
        noPermission = True
    else:
        exp = guildSettings.get("expiration")
    if exp is not None and exp < time.time() and exp != -1:
        noPermission = True
    if noPermission and not disableWhitelisting:
        await interaction.response.send_message(
            content="**Server does not have permission to use this command.**\nType `/permissions` for more information.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=False, thinking=True)
    if not await _ensure_player_counts():
        await interaction.followup.send(
            content="Unable to gather player counts right now.",
            ephemeral=True,
        )
        return

    hours_value = range_hours.value if range_hours else 24
    message, graph_buf, graph_error = build_player_count_report(
        include_graph=bool(graph),
        range_hours=hours_value,
    )
    message = _apply_graph_error(message, graph_error)

    log_usage(
        interaction=interaction,
        feature="steam",
        action="counts_guild",
        details={"graph": bool(graph), "range_hours": hours_value},
    )

    chunks = splitMsg(message)
    graph_file = None
    if graph and graph_buf is not None and graph_error is None:
        graph_file = discord.File(fp=graph_buf, filename="steam_player_counts.png")

    if graph_file is not None:
        await interaction.followup.send(content=chunks[0], file=graph_file)
        for chunk in chunks[1:]:
            await interaction.followup.send(content=chunk)
    else:
        for chunk in chunks:
            await interaction.followup.send(content=chunk)
