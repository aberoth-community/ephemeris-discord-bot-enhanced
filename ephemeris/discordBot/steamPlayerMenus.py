from typing import Optional

from .commonImports import *
from .configFiles.steamPlayerDataBase import (
    get_steam_menu,
    upsert_steam_menu,
)
from .steamPlayerReports import build_player_count_report


GRAPH_RANGE_CHOICES = [
    ("6 hours", 6),
    ("12 hours", 12),
    ("24 hours", 24),
    ("48 hours", 48),
    ("7 days", 168),
]


def _apply_graph_error(message: str, graph_error: Optional[str]) -> str:
    if graph_error:
        return f"{message}\n**Graph:** {graph_error}"
    return message


class SteamGraphRangeSelect(discord.ui.Select):
    def __init__(self, range_hours: int):
        options = []
        for label, hours in GRAPH_RANGE_CHOICES:
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(hours),
                    default=int(range_hours) == int(hours),
                )
            )
        super().__init__(
            placeholder="Graph range",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="steam_graph_range",
        )

    async def callback(self, interaction: discord.Interaction):
        settings = get_steam_menu(str(interaction.message.id))
        include_graph = bool(settings.include_graph) if settings else False
        range_hours = int(self.values[0])

        upsert_steam_menu(
            message_id=str(interaction.message.id),
            channel_id=str(interaction.channel_id),
            guild_id=str(interaction.guild_id),
            include_graph=1 if include_graph else 0,
            range_hours=range_hours,
        )

        message, graph_buf, graph_error = build_player_count_report(
            include_graph=include_graph, range_hours=range_hours
        )
        message = _apply_graph_error(message, graph_error)
        view = GuildSteamPlayerMenu(
            include_graph=include_graph, range_hours=range_hours
        )

        if include_graph and graph_buf is not None:
            graph_file = discord.File(fp=graph_buf, filename="steam_player_counts.png")
            await interaction.response.edit_message(
                content=message, attachments=[graph_file], view=view
            )
        else:
            await interaction.response.edit_message(
                content=message, attachments=[], view=view
            )


class GuildSteamPlayerMenu(discord.ui.View):
    def __init__(self, include_graph: bool = False, range_hours: int = 24):
        super().__init__(timeout=None)
        self.add_item(SteamGraphRangeSelect(range_hours))
        self.include_graph = include_graph

    @discord.ui.button(
        label="Toggle graph",
        style=discord.ButtonStyle.blurple,
        custom_id="steam_graph_toggle",
    )
    async def toggle_graph(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        settings = get_steam_menu(str(interaction.message.id))
        range_hours = settings.range_hours if settings else 24
        include_graph = not bool(settings.include_graph) if settings else True

        upsert_steam_menu(
            message_id=str(interaction.message.id),
            channel_id=str(interaction.channel_id),
            guild_id=str(interaction.guild_id),
            include_graph=1 if include_graph else 0,
            range_hours=int(range_hours),
        )

        message, graph_buf, graph_error = build_player_count_report(
            include_graph=include_graph, range_hours=int(range_hours)
        )
        message = _apply_graph_error(message, graph_error)
        view = GuildSteamPlayerMenu(
            include_graph=include_graph, range_hours=int(range_hours)
        )

        if include_graph and graph_buf is not None:
            graph_file = discord.File(fp=graph_buf, filename="steam_player_counts.png")
            await interaction.response.edit_message(
                content=message, attachments=[graph_file], view=view
            )
        else:
            await interaction.response.edit_message(
                content=message, attachments=[], view=view
            )
