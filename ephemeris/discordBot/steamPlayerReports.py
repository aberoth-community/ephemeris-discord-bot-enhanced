import io
from typing import Dict, Optional, Tuple

from .configFiles.steamPlayerDataBase import (
    REALM_KEYS,
    REALM_LABELS,
    get_latest_player_counts,
    get_player_counts_at_or_before,
    get_player_counts_before,
)
from .steamPlayerGraphs import build_player_count_graph


def _format_delta(current: int, previous: int) -> str:
    delta = current - previous
    if delta > 0:
        return f"+{delta}"
    return f"{delta}"


def build_player_count_report(
    include_graph: bool = False,
    range_hours: int = 24,
) -> Tuple[str, Optional[io.BytesIO], Optional[str]]:
    latest = get_latest_player_counts()
    if latest is None:
        return "No player count history available yet.", None, None

    current_ts, current_counts = latest
    compare_target = current_ts - 3600
    previous = get_player_counts_at_or_before(compare_target)
    if previous is None:
        previous = get_player_counts_before(current_ts)

    prev_ts = None
    prev_counts: Dict[str, int] = {realm: 0 for realm in REALM_KEYS}
    if previous is not None:
        prev_ts, prev_counts = previous
    else:
        prev_counts = dict(current_counts)

    total_current = sum(current_counts.get(realm, 0) for realm in REALM_KEYS)
    total_prev = sum(prev_counts.get(realm, 0) for realm in REALM_KEYS)

    lines = [
        "**Steam player counts**",
        f"**Updated:** <t:{current_ts}:R>",
        f"**Users online:** {total_current} ({_format_delta(total_current, total_prev)})",
    ]
    if prev_ts is not None:
        lines.append(f"**Compared to:** <t:{prev_ts}:R>")
    else:
        lines.append("**Compared to:** no earlier snapshots")

    lines.append("**Realms:**")
    for realm in REALM_KEYS:
        current = current_counts.get(realm, 0)
        previous_count = prev_counts.get(realm, 0)
        label = REALM_LABELS.get(realm, realm)
        lines.append(f"- {label}: {current} ({_format_delta(current, previous_count)})")

    message = "\n".join(lines)
    if not include_graph:
        return message, None, None

    if range_hours < 1:
        range_hours = 1
    start_ts = current_ts - int(range_hours) * 3600
    graph_buf, graph_error = build_player_count_graph(
        start_ts=start_ts, end_ts=current_ts
    )
    return message, graph_buf, graph_error
