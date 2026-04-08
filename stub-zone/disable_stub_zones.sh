#!/bin/bash

# --- Конфигурация ---
STUB_ZONE="ru."
TEMP_STUB_CONFIG="/etc/unbound/stub_server.conf"

# --- Функции ---
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# --- Основная логика ---
log_message "Начинаем деактивацию автономного режима для зоны ${STUB_ZONE}"

# 1. Удаляем стаб-зону из основного Unbound
log_message "Удаляем стаб-зону ${STUB_ZONE} из основного Unbound"
sudo unbound-control stub_remove ${STUB_ZONE}

# 2. Очищаем кэш основного Unbound для этой зоны
log_message "Очищаем кэш основного Unbound для зоны ${STUB_ZONE}"
sudo unbound-control flush_zone ${STUB_ZONE}

# 3. Останавливаем «теневой» Unbound
if pgrep -f "unbound -c ${TEMP_STUB_CONFIG}" > /dev/null; then
    log_message "Останавливаем теневой Unbound"
    sudo pkill -f "unbound -c ${TEMP_STUB_CONFIG}"
    sleep 1
    # Проверяем, что остановился
    if pgrep -f "unbound -c ${TEMP_STUB_CONFIG}" > /dev/null; then
        log_message "ОШИБКА: Теневой Unbound не остановился, принудительно убиваем"
        sudo pkill -9 -f "unbound -c ${TEMP_STUB_CONFIG}"
    else
        log_message "Теневой Unbound остановлен"
    fi
else
    log_message "Теневой Unbound не был запущен"
fi

log_message "Автономный режим для зоны ${STUB_ZONE} деактивирован"
