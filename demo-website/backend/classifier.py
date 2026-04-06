from typing import Dict

from .app_state import AppState
from .models import DigResult


def classify_source(
    local_res: DigResult,
    public_res: DigResult,
    stat_delta: Dict[str, int],
    state: AppState,
) -> str:
    if local_res.status in {"ERROR", "SERVFAIL", "REFUSED", "FORMERR", "NOTIMP"}:
        return "resolver-error"

    if (
        local_res.status == "NOERROR"
        and public_res.status == "NOERROR"
        and local_res.answers
        and local_res.answers != public_res.answers
    ):
        return "local-zone"

    cachehits = stat_delta.get("total.num.cachehits", 0)
    cachemiss = stat_delta.get("total.num.cachemiss", 0)
    rec = stat_delta.get("total.num.recursivereplies", 0)
    snapshot = state.snapshot()
    qtime = local_res.query_time_ms if local_res.query_time_ms is not None else 999

    if cachehits > 0:
        return "unbound-cache"

    if snapshot["unbound_cleared"] and snapshot["redis_cleared"] and rec > 0:
        return "internet"

    if snapshot["unbound_cleared"] and not snapshot["redis_cleared"]:
        if rec > 0:
            return "internet"
        if cachemiss > 0 or qtime <= 20:
            return "redis"

    if rec > 0:
        return "internet"

    if cachemiss > 0 and qtime <= 20:
        return "redis"

    if qtime <= 5:
        return "unbound-cache"
    if qtime <= 20:
        return "redis"
    return "internet"
