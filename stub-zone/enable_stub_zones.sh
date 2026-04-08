#!/bin/bash

# --- Конфигурация ---
STUB_ZONE="ru."
STUB_SERVER_IP="127.0.0.2"  # Изменил IP, чтобы не конфликтовать с основным
STUB_SERVER_PORT="5353"
LOCAL_ZONE_FILE="/etc/unbound/ru_zone.conf"
TEMP_STUB_CONFIG="/etc/unbound/stub_server.conf"

# --- Функции ---
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# --- Основная логика ---
log_message "Начинаем активацию автономного режима для зоны ${STUB_ZONE}"

# 1. Создаем или обновляем файл локальной зоны
log_message "Создаем/обновляем файл локальной зоны: ${LOCAL_ZONE_FILE}"
sudo tee ${LOCAL_ZONE_FILE} > /dev/null <<EOF
local-zone: "${STUB_ZONE}" static
local-data: "mail.ru. IN A 9.9.9.9"
local-data: "yandex.ru. IN A 7.7.7.7"
local-data: "ok.ru. IN A 6.6.6.6"
local-data: "lenta.ru. IN A 4.4.4.4"
local-data: "tass.ru. IN A 3.3.3.3"
# Добавьте здесь другие записи, которые должны быть доступны в автономном режиме
EOF

# 2. Создаем временный конфиг для «теневого» Unbound
log_message "Создаем временный конфиг для теневого Unbound: ${TEMP_STUB_CONFIG}"
sudo tee ${TEMP_STUB_CONFIG} > /dev/null <<EOF
server:
    interface: ${STUB_SERVER_IP}
    port: ${STUB_SERVER_PORT}
    do-daemonize: yes
    access-control: 0.0.0.0/0 allow
    access-control: ::0/0 allow
    include: "${LOCAL_ZONE_FILE}"
    # Отключаем рекурсию - работаем как авторитативный сервер
    do-not-query-address: 0.0.0.0/0
    do-not-query-address: ::0/0
    # Включаем отладочный лог
    verbosity: 2
    use-syslog: no
    logfile: "/var/log/unbound_stub.log"
EOF

# 3. Останавливаем предыдущий экземпляр, если есть
if pgrep -f "unbound -c ${TEMP_STUB_CONFIG}" > /dev/null; then
    log_message "Останавливаем старый экземпляр теневого Unbound"
    sudo pkill -f "unbound -c ${TEMP_STUB_CONFIG}"
    sleep 2
fi

# 4. Запускаем «теневой» Unbound
log_message "Запускаем теневой Unbound на ${STUB_SERVER_IP}:${STUB_SERVER_PORT}"
sudo unbound -c ${TEMP_STUB_CONFIG}
sleep 3

# Проверяем, запустился ли
if pgrep -f "unbound -c ${TEMP_STUB_CONFIG}" > /dev/null; then
    log_message "Теневой Unbound успешно запущен"
    
    # Проверяем, отвечает ли теневой Unbound
    if dig +short @${STUB_SERVER_IP} -p ${STUB_SERVER_PORT} mail.ru | grep -q "9.9.9.9"; then
        log_message "Теневой Unbound корректно отвечает на запросы"
    else
        log_message "ПРЕДУПРЕЖДЕНИЕ: Теневой Unbound не отвечает корректно"
        sudo tail -5 /var/log/unbound_stub.log 2>/dev/null || echo "Лог не найден"
    fi
else
    log_message "ОШИБКА: Теневой Unbound не запустился"
    exit 1
fi

# 5. Удаляем старую стаб-зону, если есть
sudo unbound-control stub_remove ${STUB_ZONE} 2>/dev/null

# 6. Добавляем стаб-зону в основной Unbound
log_message "Добавляем стаб-зону ${STUB_ZONE} в основной Unbound"
sudo unbound-control stub_add ${STUB_ZONE} ${STUB_SERVER_IP}@${STUB_SERVER_PORT}

# 7. Очищаем кэш основного Unbound для этой зоны
log_message "Очищаем кэш основного Unbound для зоны ${STUB_ZONE}"
sudo unbound-control flush_zone ${STUB_ZONE}

log_message "Автономный режим для зоны ${STUB_ZONE} активирован."
log_message "Лог теневого Unbound: tail -f /var/log/unbound_stub.log"
