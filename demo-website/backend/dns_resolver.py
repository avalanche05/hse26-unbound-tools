import re
from typing import List

from .command_utils import run_cmd
from .config import DNS_PORT
from .models import DigResult


def parse_dig_output(output: str) -> DigResult:
    status_match = re.search(r"status:\s*([A-Z]+),", output)
    flags_match = re.search(r"flags:\s*([^;]+);", output)
    qtime_match = re.search(r"Query time:\s*(\d+)\s*msec", output)

    status = status_match.group(1) if status_match else "UNKNOWN"
    flags = flags_match.group(1).strip() if flags_match else ""
    ad_flag = " ad" in f" {flags} "
    query_time_ms = int(qtime_match.group(1)) if qtime_match else None

    answers: List[str] = []
    ttl = None

    in_answer = False
    for line in output.splitlines():
        if line.startswith(";; ANSWER SECTION:"):
            in_answer = True
            continue
        if in_answer and line.startswith(";;"):
            break
        if in_answer and line.strip():
            parts = line.split()
            if len(parts) >= 5 and parts[1].isdigit():
                if ttl is None:
                    ttl = int(parts[1])
                answers.append(" ".join(parts[4:]))

    return DigResult(
        status=status,
        answers=answers,
        ttl=ttl,
        ad_flag=ad_flag,
        query_time_ms=query_time_ms,
        flags=flags,
        raw=output,
    )


def _build_dig_command(server: str, domain: str, rr_type: str, use_tcp: bool = False) -> List[str]:
    command = [
        "dig",
        f"@{server}",
        "-p",
        DNS_PORT,
        domain,
        rr_type,
        "+dnssec",
        "+stats",
        "+time=3",
        "+tries=1",
    ]
    if use_tcp:
        command.append("+tcp")
    return command


def dig_query(server: str, domain: str, rr_type: str, retries: int = 1, fallback_tcp: bool = False) -> DigResult:
    attempts = max(1, retries)
    last_result = None

    for _ in range(attempts):
        command = _build_dig_command(server, domain, rr_type, use_tcp=False)
        last_result = run_cmd(command, timeout_s=10)
        if last_result.returncode == 0:
            return parse_dig_output(last_result.stdout)

    if fallback_tcp:
        tcp_command = _build_dig_command(server, domain, rr_type, use_tcp=True)
        tcp_result = run_cmd(tcp_command, timeout_s=10)
        if tcp_result.returncode == 0:
            return parse_dig_output(tcp_result.stdout)
        last_result = tcp_result

    stderr = (last_result.stderr or "").strip() if last_result else ""
    stdout = last_result.stdout if last_result else ""
    return DigResult(
        status="ERROR",
        answers=[],
        ttl=None,
        ad_flag=False,
        query_time_ms=None,
        flags="",
        raw=stdout + (last_result.stderr if last_result else ""),
        error=stderr or "dig failed",
    )


def normalize_answers_for_compare(answers: List[str]) -> List[str]:
    return sorted(a.strip().lower() for a in answers if a.strip())
