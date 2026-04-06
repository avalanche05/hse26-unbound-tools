import subprocess
from typing import List


def run_cmd(command: List[str], timeout_s: int = 8) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stderr = (exc.stderr or "") + f"\nCommand timeout after {timeout_s}s"
        return subprocess.CompletedProcess(command, 124, stdout=exc.stdout or "", stderr=stderr.strip())
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(command, 127, stdout="", stderr=str(exc))
    except PermissionError as exc:
        return subprocess.CompletedProcess(command, 126, stdout="", stderr=str(exc))
    except OSError as exc:
        return subprocess.CompletedProcess(command, 125, stdout="", stderr=str(exc))


def run_cmd_with_sudo_fallback(command: List[str], timeout_s: int = 8) -> subprocess.CompletedProcess:
    result = run_cmd(command, timeout_s=timeout_s)
    if result.returncode == 0:
        return result
    if command and command[0] == "sudo":
        return result
    sudo_result = run_cmd(["sudo", "-n", *command], timeout_s=timeout_s)
    if sudo_result.returncode == 0:
        return sudo_result
    return result
