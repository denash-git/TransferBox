import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from core.config_manager import load_env
from bot.auth import AuthMiddleware
from bot.handlers import start, users, status, services

async def main():
    env = load_env()
    token = env.get("TG_BOT_TOKEN")
    enabled = env.get("TG_BOT_ENABLED", "false").lower() == "true"
    
    if not enabled:
        print("[TG BOT] Bot is disabled (TG_BOT_ENABLED is not true).")
        sys.exit(0)
        
    if not token:
        print("[TG BOT] TG_BOT_TOKEN is missing in instance.env")
        sys.exit(1)
        
    bot = Bot(token=token)
    dp = Dispatcher()
    
    # Регистрация команд в меню Telegram
    commands = [
        BotCommand(command="start", description="Главное меню управления"),
        BotCommand(command="users", description="Список пользователей"),
        BotCommand(command="diag", description="Диагностика системы"),
        BotCommand(command="status", description="Мониторинг ресурсов"),
        BotCommand(command="services", description="Перезапуск служб")
    ]
    await bot.set_my_commands(commands)
    
    # Регистрация middleware для авторизации по CHAT_ID
    dp.update.outer_middleware(AuthMiddleware())
    
    # Подключение роутеров обработчиков
    dp.include_router(start.router)
    dp.include_router(users.router)
    dp.include_router(status.router)
    dp.include_router(services.router)
    
    print("[TG BOT] Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
