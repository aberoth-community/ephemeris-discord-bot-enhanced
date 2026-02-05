import subprocess
import re
import requests
import sys
from pathlib import Path


IP = "192.99.201.128"
URL = f"http://{IP}/get_store_session_and_names_for_steam"


def run_exe_capture_output(exe_path: Path) -> str:
    """Runs an exe and returns combined stdout+stderr as a string."""
    p = subprocess.run(
        [str(exe_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(exe_path.parent),
    )
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    return out


def extract_ticket(output: str) -> str:
    """
    Extracts the long hex ticket from ticket_open.exe output.
    Your ticket is a long hex string (0-9a-f) printed alone on a line.
    """
    candidates = re.findall(r"\b[0-9a-fA-F]{200,}\b", output)
    if not candidates:
        raise RuntimeError("Could not find a ticket in ticket_open.exe output.")

    # Usually the ticket is the longest hex blob printed
    ticket = max(candidates, key=len).lower()
    return ticket


def _parse_mapping(response: str) -> dict:
    parts = response.strip().split(",", 1)
    if len(parts) < 2:
        preview = response[:200].replace("\n", "\\n")
        raise RuntimeError(
            f"Unexpected response format (missing mapping). "
            f"Preview: {preview}"
        )

    mapping_str = parts[1].strip()
    if not mapping_str:
        raise RuntimeError("Unexpected response format (empty mapping).")

    try:
        nums = [int(x) for x in mapping_str.split("_") if x]
    except ValueError as exc:
        preview = mapping_str[:200]
        raise RuntimeError(
            f"Unexpected response format (non-integer mapping). "
            f"Preview: {preview}"
        ) from exc

    if len(nums) % 2 != 0:
        raise RuntimeError(
            f"Unexpected response format (odd mapping length: {len(nums)})."
        )

    return dict(zip(nums[0::2], nums[1::2]))


def do_request(ticket: str):
    headers = {
        "User-Agent": "Java/1.8.0_131",
        "Host": IP,
        "Accept": "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2",
        "Connection": "keep-alive",
    }

    r = requests.get(
        URL,
        params={"ticket": ticket},
        headers=headers,
        allow_redirects=False,
        timeout=10,
    )

    # print("FINAL URL:", r.request.url)
    # print("STATUS:", r.status_code)
    # print("HEADERS:", dict(r.headers))
    # print("\nRAW BYTES (first 64):", r.content[:64])
    # print("\nBODY AS TEXT (lossy):")
    # print(r.content.decode("utf-8", errors="replace"))

    response = r.text.strip()
    mapping = _parse_mapping(response)
    # print(mapping)

    return r, mapping


def get_steam_player_count():
    here = Path(__file__).resolve().parent
    open_exe = here / "steam_ticket_generator" / "ticket_open.exe"
    close_exe = here / "steam_ticket_generator" / "ticket_close.exe"

    if not open_exe.exists():
        # print(f"ERROR: Missing {open_exe}", file=sys.stderr)
        sys.exit(1)

    if not close_exe.exists():
        # print(f"ERROR: Missing {close_exe}", file=sys.stderr)
        sys.exit(1)

    # print("[1/3] Running ticket_open.exe...")
    open_out = run_exe_capture_output(open_exe)
    # Uncomment to debug:
    # print("ticket_open.exe output:\n", open_out)

    ticket = extract_ticket(open_out)
    # print("[2/3] Extracted ticket length:", len(ticket))
    # print("[3/3] Sending web request...")
    try:
        _, player_dict = do_request(ticket)
        color_map = {
            2: "black",
            3: "green",
            4: "red",
            5: "purple",
            6: "yellow",
            7: "cyan",
            8: "blue",
        }
        player_dict = {
            color_map[k]: v for k, v in player_dict.items() if k in color_map
        }

        # print(player_dict)
    finally:
        # print("\n[cleanup] Running ticket_close.exe...")
        close_out = run_exe_capture_output(close_exe)
        # Uncomment to debug:
        # print("ticket_close.exe output:\n", close_out)

    # print("\nDone.")
    return player_dict


if __name__ == "__main__":
    print(get_steam_player_count())
