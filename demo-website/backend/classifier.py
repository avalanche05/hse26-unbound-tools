from typing import Dict

from .app_state import AppState
from .dns_resolver import normalize_answers_for_compare
from .models import DigResult


def classify_source(
    local_res: DigResult,
    public_res: DigResult,
    stat_delta: Dict[str, int],
    state: AppState,
) -> str:
    if local_res.status in {"ERROR", "SERVFAIL", "REFUSED", "FORMERR", "NOTIMP"}:
        return "resolver-error"

    local_answers_norm = normalize_answers_for_compare(local_res.answers)
    public_answers_norm = normalize_answers_for_compare(public_res.answers)
    if (
        local_res.status == "NOERROR"
        and public_res.status == "NOERROR"
        and local_answers_norm
        and public_answers_norm
        and local_answers_norm != public_answers_norm
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
        # After Unbound flush, fast NOERROR is typically a Redis-backed response.
        if qtime <= 20:
            return "redis"
        if cachemiss > 0 and rec == 0:
            return "redis"
        if rec > 0:
            return "internet"

    if cachemiss > 0 and rec == 0:
        return "redis"

    if cachemiss > 0 and qtime <= 12:
        return "redis"

    if rec > 0:
        return "internet"

    if qtime <= 5:
        return "unbound-cache"
    if qtime <= 20:
        return "redis"
    return "internet"
