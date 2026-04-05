#!/bin/bash

DOMAIN="${1:?Usage: $0 <domain>}"
UPSTREAM="8.8.8.8"
COLLECTED="/tmp/${DOMAIN}-real.txt"
OUTPUT="/etc/unbound/unbound.conf.d/local-zone-${DOMAIN//./-}.conf"

# собираем реальные данные
echo "# $DOMAIN real zone data $(date)" > "$COLLECTED"

for fqdn in "$DOMAIN" "www.$DOMAIN"; do
    for type in A AAAA MX NS TXT SOA; do
        result=$(dig @$UPSTREAM "$fqdn" "$type" +short 2>/dev/null)
        [ -z "$result" ] && continue
        echo "$fqdn $type:" >> "$COLLECTED"
        echo "  $result"   >> "$COLLECTED"
    done
done

cat "$COLLECTED"

# генерируем конфиг подмены
cat > "$OUTPUT" << EOF
server:
    domain-insecure: "$DOMAIN"
    local-zone: "$DOMAIN." static

    local-data: "$DOMAIN.      300 IN A   1.2.3.4"
    local-data: "www.$DOMAIN.  300 IN A   5.6.7.8"
    local-data: "$DOMAIN.      300 IN TXT \"spoofed by local unbound\""
EOF

# добавляем реальные NS и MX
for fqdn in "$DOMAIN" "www.$DOMAIN"; do
    for type in NS MX; do
        dig @$UPSTREAM "$fqdn" "$type" +short 2>/dev/null | while read -r rdata; do
            [ -z "$rdata" ] && continue
            echo "    local-data: \"$fqdn. 300 IN $type $rdata\"" >> "$OUTPUT"
        done
    done
done

echo "# generated at $(date)" >> "$OUTPUT"

echo "done: $OUTPUT"
