from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from core.config_manager import load_env

class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data):
        env = load_env()
        allowed_chat_id = env.get("TG_CHAT_ID")
        
        user = None
        # event является объектом Update в dp.update.outer_middleware
        if hasattr(event, "message") and event.message:
            user = event.message.from_user
        elif hasattr(event, "callback_query") and event.callback_query:
            user = event.callback_query.from_user
        elif hasattr(event, "edited_message") and event.edited_message:
            user = event.edited_message.from_user
            
        if user:
            if allowed_chat_id and str(user.id) == str(allowed_chat_id):
                return await handler(event, data)
                
        return None
