# 📦 kvnBox

Универсальная панель управления прокси и VPN-соединениями с маскировкой трафика под обычный веб-сайт. Объединяет VLESS, NaiveProxy, Mieru и NetBird на едином HTTPS-порту.

---

## Возможности

- **Протоколы:** VLESS (WebSocket, gRPC, XHTTP), NaiveProxy, Mieru, NetBird
- **TUI-интерфейс:** Плавное меню управления в терминале (стрелки + Enter)
- **Telegram-бот:** Управление пользователями, статус сервера, генерация ссылок, алерты
- **Диагностика:** Мониторинг CPU/RAM/Disk, логи, speedtest
- **Бэкапы:** Зашифрованные архивы и восстановление в один клик
- **Безопасное обновление:** Автозащита от сбоев при установке

---

## Требования

- **ОС:** Debian 12/13 или Ubuntu 22.04/24.04 LTS (чистая, root-доступ)
- **Домен:** DNS A-запись → IP сервера (до начала установки)
- **Порты:** 80 и 443 свободны

---

## Установка

```bash
bash <(wget -qO- https://raw.githubusercontent.com/denash-git/kvnBox/main/install.sh)
```

После установки запустите панель:

```bash
menu
```

---

## Структура проекта

```
kvnBox/
├── core/              # Ядро: модели, сервисы, системный слой
│   ├── models/        # Pydantic-модели (User, Config, ServiceStatus)
│   ├── services/      # Бизнес-логика (UserService, ServiceManager, BackupService)
│   └── system/        # SystemExecutor (Linux / Mock)
├── tui/               # Консольный интерфейс (prompt_toolkit + rich)
│   ├── components/    # Меню, диалоги, лейаут
│   └── screens/       # Экраны: главная, пользователи, службы, бэкап, настройки
├── bot/               # Telegram-бот (aiogram 3.x)
├── templates/         # Шаблоны Caddyfile, sing-box, NaiveProxy
├── tests/             # Pytest: unit, services, safety
├── install.sh         # Скрипт установки
└── transferbox        # Лаунчер (symlink → menu)
```

---

## Управление

### Консольное меню (`menu`)

Навигация: `↑`/`↓` + `Enter`. Разделы:

- **Пользователи** — добавление, удаление, ссылки подключения
- **Состояние служб** — Caddy, sing-box, Mieru, Telegram-бот
- **Бэкап и Восстановление** — создание/восстановление архивов
- **Системные настройки** — SSH-порт, BBR

### Telegram-бот

Настройка через меню бота: токен + Chat ID. Бот создаёт systemd-службу и запускается автоматически.

---

## Перенос на другой сервер

1. `menu` → Настройки → Бэкап → Создать бэкап
2. Установите панель на новый сервер
3. Скопируйте `.zip` в `/opt/transferbox/backups/`
4. `menu` → Бэкап → Восстановить из последнего бэкапа

---

## Лицензия

Свободное использование. Проект основан на:

- [Caddy](https://github.com/caddyserver/caddy)
- [sing-box](https://github.com/SagerNet/sing-box)
- [NaiveProxy](https://github.com/klzgrad/naiveproxy)
- [Mieru](https://github.com/enfein/mieru)
- [NetBird](https://github.com/netbirdio/netbird)
