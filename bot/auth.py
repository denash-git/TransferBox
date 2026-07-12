from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from core.config_manager import load_env

class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data):
        env = load_env()
        allowed_chat_id = env.get("TG_CHAT_ID")
        
        user = getattr(event, "from_user", None)
        if user:
            if allowed_chat_id and str(user.id) == str(allowed_chat_id):
                return await handler(event, data)
                
        return None
