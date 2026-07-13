#!/usr/bin/env bash
# =============================================================================
# TransferBox — Установщик прокси-сервера (Caddy + sing-box) на Debian 13
# =============================================================================
set -euo pipefail

# Цвета
BLUE='\033[1;34m'
GREEN='\033[1;32m'
RED='\033[1;31m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
DIM='\033[2m'
BOLD='\033[1m'
RESET='\033[0m'

# Константы
PROJECT_ROOT="/opt/transferbox"
CADDY_BIN="/usr/local/bin/caddy"
CADDY_SERVICE="/etc/systemd/system/caddy.service"
TRANSFERBOX_BIN="/usr/local/bin/menu"
INSTALL_LOG="/tmp/transferbox_install.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IS_PIPED=false

# Очистить экран перед началом установки
clear

if [[ "$SCRIPT_DIR" == /dev/fd* || "$SCRIPT_DIR" == /proc/* || ! -f "$SCRIPT_DIR/install.sh" ]]; then
    IS_PIPED=true
fi
DEFAULT_GO_VERSION="1.26.2"

step()    { echo -e "\n${BLUE}[*] ${1}${RESET}"; }
log_ok()  { echo -e "  ${GREEN}✓${RESET} ${1}"; }
log_info(){ echo -e "  ${DIM}* ${1}${RESET}"; }
warn()    { echo -e "  ${YELLOW}⚠ ${1}${RESET}"; }
error()   { echo -e "\n${RED}✗ ОШИБКА: ${1}${RESET}" >&2; exit 1; }

# Проверка прав root
if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    error "Этот скрипт должен быть запущен от имени root. Используйте: sudo bash install.sh"
fi

# Проверка ОС
if [[ -f /etc/os-release ]]; then
    source /etc/os-release
    if [[ "${ID:-}" != "debian" ]]; then
        warn "Скрипт разработан для Debian 13. Ваша ОС: ${PRETTY_NAME:-unknown}. Продолжение на ваш страх и риск."
    fi
else
    error "Не удалось определить операционную систему."
fi

# Вывод приветственной шапки
echo -e "${BLUE}════════════════════════════════════════════════════════════${RESET}"
echo -e "${YELLOW}                     TransferBox v3.0.1                     ${RESET}"
echo -e "${YELLOW}               Установка Панели Управления                  ${RESET}"
echo -e "${BLUE}────────────────────────────────────────────────────────────${RESET}"
echo -e "  Добро пожаловать в установщик TransferBox!"
echo -e "  Скрипт настроит все в автоматическом режиме."
echo -e "${BLUE}════════════════════════════════════════════════════════════${RESET}"
echo ""

# Сбор настроек
step "Сбор настроек установки"
read -rp "  Введите ваш домен (например, proxy.example.com): " domain
domain="${domain// /}"
if [[ -z "$domain" ]]; then
    error "Домен не может быть пустым."
fi

read -rp "  Введите email для Let's Encrypt (по умолчанию пусто — анонимный SSL): " email
email="${email// /}"

read -rp "  Включить BBR (TCP оптимизация)? [Y/n]: " bbr_input
enable_bbr="true"
[[ "${bbr_input,,}" == "n" ]] && enable_bbr="false"

# Установка необходимых пакетов
step "Установка необходимых пакетов"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
    build-essential curl wget git ca-certificates \
    python3 python3-pip python3-psutil ufw openssl qrencode jq libcap2-bin >/dev/null

log_info "Установка Python-зависимостей (aiogram)..."
pip3 install --break-system-packages aiogram >/dev/null 2>&1 || pip3 install aiogram >/dev/null 2>&1 || true

# Настройка официального репозитория Ookla Speedtest
log_info "Настройка репозитория Ookla Speedtest..."
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash >/dev/null 2>&1
apt-get install -y -qq speedtest >/dev/null 2>&1

log_ok "Базовые пакеты и Ookla Speedtest установлены."

# Применение BBR
if [[ "$enable_bbr" == "true" ]]; then
    step "Включение BBR"
    if modprobe tcp_bbr 2>/dev/null; then
        sysctl -w net.core.default_qdisc=fq >/dev/null 2>&1 || true
        sysctl -w net.ipv4.tcp_congestion_control=bbr >/dev/null 2>&1 || true
        cat > /etc/sysctl.d/99-transferbox-bbr.conf <<EOF
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
EOF
        log_ok "BBR успешно активирован."
    else
        warn "BBR не поддерживается вашим ядром."
    fi
fi

# Скачивание и установка sing-box
step "Установка sing-box"
arch=$(dpkg --print-architecture 2>/dev/null || uname -m)
go_arch="amd64"
case "$arch" in
    amd64|x86_64) go_arch="amd64";;
    arm64|aarch64) go_arch="arm64";;
    *) error "Неподдерживаемая архитектура: ${arch}";;
esac

log_info "Получение последней версии sing-box..."
latest_sb_ver=$(curl -fsSL "https://api.github.com/repos/SagerNet/sing-box/releases/latest" | jq -r .tag_name)
clean_sb_ver="${latest_sb_ver#v}"

deb_url="https://github.com/SagerNet/sing-box/releases/download/${latest_sb_ver}/sing-box_${clean_sb_ver}_linux_${go_arch}.deb"
log_info "Скачивание ${deb_url}..."
wget -qO /tmp/sing-box.deb "$deb_url"
dpkg -i /tmp/sing-box.deb >/dev/null
rm -f /tmp/sing-box.deb
log_ok "sing-box установлен версии ${clean_sb_ver}."

# Скачивание и установка mita (Mieru server)
step "Установка Mieru (Mita) сервера"
log_info "Получение последней версии mita..."
latest_mita_ver=$(curl -fsSL https://api.github.com/repos/enfein/mieru/releases/latest | jq -r .tag_name)
clean_mita_ver=${latest_mita_ver#v}
deb_mita_url="https://github.com/enfein/mieru/releases/download/${latest_mita_ver}/mita_${clean_mita_ver}_${go_arch}.deb"
log_info "Скачивание ${deb_mita_url}..."
wget -qO /tmp/mita.deb "$deb_mita_url"
dpkg -i /tmp/mita.deb >/dev/null
rm -f /tmp/mita.deb
systemctl stop mita >/dev/null 2>&1 || true
systemctl disable mita >/dev/null 2>&1 || true
log_ok "Сервер Mieru (Mita) версии ${clean_mita_ver} установлен (по умолчанию отключен)."

# Сборка Caddy с плагином forwardproxy
step "Сборка Caddy с плагином NaiveProxy (это может занять 1-2 минуты)"
if [[ -x "$CADDY_BIN" ]]; then
    log_ok "Caddy уже установлен."
else
    warn "Внимание: сборка Caddy из исходников занимает значительное время (1-2 минуты). Пожалуйста, подождите..."
    mkdir -p /root/tmp
    export TMPDIR="/root/tmp"
    tmpdir=$(mktemp -d -p /root/tmp)
    log_info "Загрузка Go..."
    wget -qO "${tmpdir}/go.tar.gz" "https://go.dev/dl/go${DEFAULT_GO_VERSION}.linux-${go_arch}.tar.gz"
    tar -xzf "${tmpdir}/go.tar.gz" -C "$tmpdir"
    
    export GOROOT="${tmpdir}/go"
    export GOPATH="${tmpdir}/gopath"
    export GOBIN="${tmpdir}/bin"
    export GOTMPDIR="${tmpdir}/gotmp"
    mkdir -p "$GOTMPDIR"

    export PATH="${GOBIN}:${GOROOT}/bin:${PATH}"
    mkdir -p "$GOPATH" "$GOBIN"
    
    log_info "Установка xcaddy..."
    go install github.com/caddyserver/xcaddy/cmd/xcaddy@latest >/dev/null 2>&1
    
    log_info "Сборка бинарника..."
    xcaddy build \
        --output "${tmpdir}/caddy" \
        --with github.com/caddyserver/forwardproxy=github.com/klzgrad/forwardproxy@naive >/dev/null 2>&1
        
    cp "${tmpdir}/caddy" "$CADDY_BIN"
    chmod 755 "$CADDY_BIN"
    setcap cap_net_bind_service=+ep "$CADDY_BIN"
    rm -rf "$tmpdir"
    log_ok "Caddy успешно собран и установлен."
fi

# Установка systemd сервиса для Caddy
step "Настройка службы Caddy"
cat > "$CADDY_SERVICE" <<EOF
[Unit]
Description=Caddy Frontend Service
After=network.target network-online.target
Requires=network-online.target

[Service]
Type=notify
ExecStart=${CADDY_BIN} run --config /etc/caddy/Caddyfile --environ
ExecReload=${CADDY_BIN} reload --config /etc/caddy/Caddyfile --force
ExecStop=${CADDY_BIN} stop
TimeoutStopSec=5s
LimitNOFILE=1048576
LimitNPROC=512
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable caddy >/dev/null 2>&1
systemctl enable sing-box >/dev/null 2>&1
log_ok "Службы caddy и sing-box зарегистрированы и добавлены в автозагрузку."

# Копирование файлов проекта
step "Копирование файлов TransferBox"
if [[ "$IS_PIPED" == "true" ]]; then
    if [[ -d "./core" && -d "./templates" && -d "./lib" && -d "./bot" && -f "./transferbox" ]]; then
        SCRIPT_DIR="$(pwd)"
    else
        log_info "Запуск в режиме стрима, клонируем файлы проекта из GitHub..."
        rm -rf /tmp/TransferBox
        git clone -q https://github.com/denash-git/TransferBox.git /tmp/TransferBox
        SCRIPT_DIR="/tmp/TransferBox"
    fi
fi
mkdir -p "$PROJECT_ROOT"
mkdir -p "${PROJECT_ROOT}/backups"
cp -r "$SCRIPT_DIR/core" "$SCRIPT_DIR/templates" "$SCRIPT_DIR/lib" "$SCRIPT_DIR/bot" "$PROJECT_ROOT/"
chmod 755 "$PROJECT_ROOT"
chmod -R 755 "$PROJECT_ROOT/core" "$PROJECT_ROOT/templates" "$PROJECT_ROOT/lib" "$PROJECT_ROOT/bot" 2>/dev/null || true
chmod 700 "$PROJECT_ROOT/backups"

# Определение FQDN
fqdn_val=$(hostname -f 2>/dev/null || hostname)

# Запись конфигурации инстанса
cat > "${PROJECT_ROOT}/instance.env" <<EOF
DOMAIN=${domain}
ADMIN_EMAIL=${email}
FAKE_SITE_TEMPLATE=aether
VLESS_WS_PATH=/
VLESS_GRPC_SERVICE=
VLESS_XHTTP_PATH=/xhttp
MIERU_ENABLED=false
MIERU_PORT=21000
BBR_ENABLED=${enable_bbr}
FQDN=${fqdn_val}
EOF
chmod 600 "${PROJECT_ROOT}/instance.env"

# Создание базы пользователей и добавление начального пользователя
cat > "${PROJECT_ROOT}/users.json" <<EOF
[
  {
    "nickname": "admin",
    "protocol": "naive",
    "credentials": {
      "username": "admin_naive",
      "password": "$(openssl rand -hex 12)"
    },
    "enabled": true
  },
  {
    "nickname": "admin",
    "protocol": "vless",
    "credentials": {
      "uuid": "$(cat /proc/sys/kernel/random/uuid)",
      "type": "ws"
    },
    "enabled": true
  }
]
EOF
chmod 600 "${PROJECT_ROOT}/users.json"

# Установка исполняемой команды
cp "$SCRIPT_DIR/transferbox" "$TRANSFERBOX_BIN"
chmod +x "$TRANSFERBOX_BIN"
log_ok "Утилита установлена. Вы можете запустить её командой: menu"

# Настройка фаервола UFW
step "Настройка фаервола UFW"

# Сброс правил UFW на дефолтные
ufw --force reset >/dev/null 2>&1
ufw default deny incoming >/dev/null 2>&1
ufw default allow outgoing >/dev/null 2>&1

# Определение порта SSH
ssh_port=22
if [ -f /etc/ssh/sshd_config ]; then
    detected_port=$(grep -E "^Port " /etc/ssh/sshd_config | awk '{print $2}')
    if [ -n "$detected_port" ]; then
        ssh_port=$detected_port
    fi
fi

# Разрешаем SSH, HTTP и HTTPS
ufw allow "$ssh_port"/tcp >/dev/null 2>&1
ufw allow 80/tcp >/dev/null 2>&1
ufw allow 443/tcp >/dev/null 2>&1
ufw allow 443/udp >/dev/null 2>&1

# Включаем UFW в неинтерактивном режиме
ufw --force enable >/dev/null 2>&1
log_ok "UFW фаервол настроен (открыты порты: $ssh_port/tcp, 80/tcp, 443/tcp, 443/udp)."

# Рендеринг конфигураций и запуск
step "Запуск прокси-серверов"
export PYTHONPATH="$PROJECT_ROOT"
python3 <<'PYEOF'
import sys
from core.config_manager import render_configs, validate_and_restart
render_configs()
ok, msg = validate_and_restart()
if not ok:
    print(msg, file=sys.stderr)
    sys.exit(1)
PYEOF
if [ $? -ne 0 ]; then
    echo -e "  ${RED}✗ Ошибка: Не удалось применить конфигурацию и запустить службы.${RESET}"
    echo -e "    Проверьте ошибки выше. Установка прервана.${RESET}"
    exit 1
fi
log_ok "Конфигурации применены, службы запущены."

# Вывод результатов
step "Установка завершена!"
echo -e "  Домен: ${GREEN}${domain}${RESET}"
echo -e "  Команда управления: ${GREEN}menu${RESET}"
echo
echo -e "  Сгенерированы стартовые учетные записи для пользователя ${BOLD}admin${RESET}."
echo -e "  Запустите ${GREEN}menu${RESET} -> выберите ${BOLD}1${RESET}, чтобы просмотреть ссылки подключения и QR-коды."
echo
echo -e "  ${YELLOW}⚠️ Важное примечание по SSL:${RESET}"
echo -e "  Если ваш домен ${BOLD}${domain}${RESET} еще не направлен на IP этого сервера,"
echo -e "  сертификат Let's Encrypt не будет получен сразу. Caddy автоматически"
echo -e "  получит SSL-сертификат, как только обновятся DNS-записи домена."
echo

