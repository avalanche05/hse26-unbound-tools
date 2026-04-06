import re

ALLOWED_TYPES = {"A", "AAAA", "MX", "TXT"}
LOCAL_DNS_SERVER = "127.0.0.1"
PUBLIC_DNS_SERVER = "8.8.8.8"
DNS_PORT = "53"

REDIS_HOST = "127.0.0.1"
REDIS_PORT = "6379"
REDIS_DB = "0"

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(localhost|(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+(?!-)[A-Za-z0-9-]{2,63}(?<!-))$"
)

TRACKED_UNBOUND_STATS = {
    "total.num.cachehits",
    "total.num.cachemiss",
    "total.num.recursivereplies",
}

SOURCE_LABEL_RU = {
    "local-zone": "local-zone",
    "redis": "Redis",
    "unbound-cache": "кэш Unbound",
    "internet": "интернет",
    "resolver-error": "н/д",
}
