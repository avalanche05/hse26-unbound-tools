from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DigResult:
    status: str
    answers: List[str]
    ttl: Optional[int]
    ad_flag: bool
    query_time_ms: Optional[int]
    flags: str
    raw: str
    error: Optional[str] = None
