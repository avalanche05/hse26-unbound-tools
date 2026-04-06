#!/usr/bin/env python3
from flask import Flask, jsonify, render_template, request

from .admin_actions import flush_redis_cache, flush_unbound_cache
from .app_state import AppState
from .classifier import classify_source
from .config import ALLOWED_TYPES, DOMAIN_RE, LOCAL_DNS_SERVER, PUBLIC_DNS_SERVER, SOURCE_LABEL_RU
from .dns_resolver import dig_query
from .unbound_stats import calc_stat_delta, get_unbound_stats

app = Flask(__name__, template_folder="../templates")
state = AppState()


def normalize_domain(domain: str) -> str:
    d = domain.strip().rstrip(".")
    return d.lower()


def is_valid_domain(domain: str) -> bool:
    return bool(DOMAIN_RE.fullmatch(domain))


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/resolve")
def resolve_dns():
    payload = request.get_json(silent=True) or {}
    domain = normalize_domain(str(payload.get("domain", "")))
    rr_type = str(payload.get("type", "A")).upper().strip()

    if not domain or not is_valid_domain(domain):
        return jsonify({"ok": False, "error": "Некорректный домен"}), 400
    if rr_type not in ALLOWED_TYPES:
        return jsonify({"ok": False, "error": "Некорректный тип записи"}), 400

    before_stats = get_unbound_stats()
    local_res = dig_query(LOCAL_DNS_SERVER, domain, rr_type)
    after_stats = get_unbound_stats()
    public_res = dig_query(PUBLIC_DNS_SERVER, domain, rr_type, retries=2, fallback_tcp=True)

    delta = calc_stat_delta(before_stats, after_stats)
    source_key = classify_source(local_res, public_res, delta, state)
    source_ru = SOURCE_LABEL_RU.get(source_key, source_key)

    if local_res.status == "NOERROR":
        state.mark_after_successful_local_resolve()

    answer_text = "\n".join(local_res.answers) if local_res.answers else "—"
    if local_res.status == "ERROR" and local_res.error:
        answer_text = f"Ошибка: {local_res.error}"
    elif local_res.status != "NOERROR" and not local_res.answers:
        answer_text = f"DNS статус: {local_res.status}"

    public_answer_text = "\n".join(public_res.answers) if public_res.answers else "—"
    if public_res.status == "ERROR" and public_res.error:
        public_answer_text = f"Ошибка: {public_res.error}"
    elif public_res.status != "NOERROR" and not public_res.answers:
        public_answer_text = f"DNS статус: {public_res.status}"

    local_payload = {
        "status": local_res.status,
        "answers": local_res.answers,
        "answer_text": answer_text,
        "ttl": local_res.ttl,
        "ad_flag": local_res.ad_flag,
        "query_time_ms": local_res.query_time_ms,
        "error": local_res.error,
        "source": source_ru,
        "source_code": source_key,
    }
    public_payload = {
        "status": public_res.status,
        "answers": public_res.answers,
        "answer_text": public_answer_text,
        "ttl": public_res.ttl,
        "ad_flag": public_res.ad_flag,
        "query_time_ms": public_res.query_time_ms,
        "error": public_res.error,
    }

    return jsonify(
        {
            "ok": True,
            "domain": domain,
            "type": rr_type,
            "local": local_payload,
            "public": public_payload,
            "google_8_8_8_8": public_payload,
            "source": source_ru,
            "source_key": source_key,
            "meta": {"unbound_stats_available": bool(before_stats or after_stats)},
        }
    )


@app.post("/api/admin/flush-unbound")
def api_flush_unbound():
    msg = flush_unbound_cache(state)
    return jsonify({"ok": msg.startswith("OK"), "message": msg})


@app.post("/api/admin/flush-redis")
def api_flush_redis():
    msg = flush_redis_cache(state)
    return jsonify({"ok": msg.startswith("OK"), "message": msg})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
