from .app_state import AppState
from .command_utils import run_cmd_with_sudo_fallback
from .config import REDIS_DB, REDIS_HOST, REDIS_PORT
from .unbound_stats import wait_unbound_ready


def flush_unbound_cache(state: AppState) -> str:
    if not wait_unbound_ready():
        return "Ошибка: unbound-control недоступен"
    flush = run_cmd_with_sudo_fallback(["unbound-control", "flush_zone", "."], timeout_s=8)
    if flush.returncode == 0:
        state.mark_unbound_cleared("flush_unbound")
        return "OK: кэш Unbound сброшен"
    return f"Ошибка: {(flush.stderr or flush.stdout).strip()}"


def flush_redis_cache(state: AppState) -> str:
    flush = run_cmd_with_sudo_fallback(
        ["redis-cli", "-h", REDIS_HOST, "-p", REDIS_PORT, "-n", REDIS_DB, "FLUSHDB"],
        timeout_s=5,
    )
    if flush.returncode == 0 and "OK" in flush.stdout:
        state.mark_redis_cleared("flush_redis")
        return "OK: кэш Redis сброшен"
    return f"Ошибка: {(flush.stderr or flush.stdout).strip()}"
