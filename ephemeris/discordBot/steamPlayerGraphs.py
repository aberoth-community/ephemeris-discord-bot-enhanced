import io
from datetime import datetime
from typing import Optional, Tuple

from .configFiles.steamPlayerDataBase import (
    REALM_KEYS,
    REALM_LABELS,
    get_player_count_series,
)


REALM_LINE_COLORS = {
    "black": "#C4C4C4",
    "green": "#00A745",
    "red": "#C22323",
    "purple": "#8E57CC",
    "yellow": "#FAC32D",
    "cyan": "#00C4D6",
    "blue": "#5B6CFF",
}
TOTAL_LINE_COLOR = "#FFFFFF"


def build_player_count_graph(start_ts: int, end_ts: int) -> Tuple[Optional[io.BytesIO], Optional[str]]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import matplotlib.ticker as mticker
        from matplotlib import patheffects
    except Exception:
        return None, "Graphing requires matplotlib to be installed."

    if end_ts <= start_ts:
        return None, "Graphing requires a positive time range."

    timestamps, series = get_player_count_series(start_ts, end_ts)
    if not timestamps:
        return None, "No player count history available for that range."

    labels = [datetime.utcfromtimestamp(ts) for ts in timestamps]
    totals = [
        sum(series[realm][idx] for realm in REALM_KEYS)
        for idx in range(len(labels))
    ]

    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor("#40444B")
    ax.set_facecolor("#40444B")

    axes_xcolor = "#E9E9E9"
    spine_color = "#1B1C1F"
    grid_color = "#2C2E33"

    last_values = {realm: series[realm][-1] for realm in REALM_KEYS}
    total_last = totals[-1]

    for realm in REALM_KEYS:
        ax.plot(
            labels,
            series[realm],
            color=REALM_LINE_COLORS.get(realm, "#FFFFFF"),
            marker="o",
            label=f"{REALM_LABELS.get(realm, realm)} ({last_values[realm]})",
            linewidth=2,
        )

    # ax.plot(
    #     labels,
    #     totals,
    #     color=TOTAL_LINE_COLOR,
    #     marker="o",
    #     label=f"Total ({total_last})",
    #     linewidth=2.5,
    #     linestyle="--",
    # )

    title_obj = ax.set_title("Player count history", color=axes_xcolor, fontsize=14)
    title_obj.set_path_effects(
        [patheffects.withStroke(linewidth=3, foreground=spine_color)]
    )

    ax.set_xlabel("Time (UTC)", color=axes_xcolor)
    ax.set_ylabel("Players", color=axes_xcolor)
    ax.grid(color=grid_color)
    ax.tick_params(axis="x", colors=axes_xcolor)
    ax.tick_params(axis="y", colors=axes_xcolor)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    for spine in ax.spines.values():
        spine.set_color(spine_color)
        spine.set_linewidth(2)

    range_seconds = end_ts - start_ts
    if range_seconds <= 6 * 3600:
        locator = mdates.HourLocator(interval=1)
        formatter = mdates.DateFormatter("%H:%M")
    elif range_seconds <= 2 * 86400:
        locator = mdates.HourLocator(interval=6)
        formatter = mdates.DateFormatter("%b %d %H:%M")
    else:
        locator = mdates.DayLocator(interval=1)
        formatter = mdates.DateFormatter("%b %d")
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    legend = ax.legend(ncol=2)
    if legend is not None:
        legend.get_frame().set_facecolor("#40444B")
        legend.get_frame().set_edgecolor(spine_color)
        for text in legend.get_texts():
            text.set_color(axes_xcolor)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf, None
