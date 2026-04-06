from typing import Dict

from .command_utils import run_cmd_with_sudo_fallback
from .config import TRACKED_UNBOUND_STATS


def wait_unbound_ready(retries: int = 12) -> bool:
    for _ in range(retries):
        probe = run_cmd_with_sudo_fallback(["unbound-control", "status"], timeout_s=3)
        if probe.returncode == 0:
            return True
    return False


def get_unbound_stats() -> Dict[str, int]:
    if not wait_unbound_ready():
        return {}
    result = run_cmd_with_sudo_fallback(["unbound-control", "stats_noreset"], timeout_s=5)
    if result.returncode != 0:
        return {}

    stats: Dict[str, int] = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        if key in TRACKED_UNBOUND_STATS:
            try:
                stats[key] = int(val)
            except ValueError:
                pass
    return stats


def calc_stat_delta(before: Dict[str, int], after: Dict[str, int]) -> Dict[str, int]:
    keys = set(before) | set(after)
    delta: Dict[str, int] = {}
    for key in keys:
        delta[key] = after.get(key, 0) - before.get(key, 0)
    return delta
