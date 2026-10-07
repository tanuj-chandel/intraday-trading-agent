from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.notifications.dispatcher import notifier
from app.notifications.telegram_bot import telegram_notifier
from app.core.config import settings

router = APIRouter()

class TelegramConfigRequest(BaseModel):
    bot_token: str
    chat_id: str
    allowed_chat_id: Optional[str] = None
    enabled: bool = True

class TestNotificationRequest(BaseModel):
    custom_message: Optional[str] = None

@router.get("/status")
def get_notification_status():
    """
    Returns current status of mobile alert dispatchers (Telegram, Webhook, Ring Buffer).
    """
    return {
        "telegram_configured": telegram_notifier.is_configured,
        "telegram_enabled": telegram_notifier.enabled,
        "chat_id_set": bool(telegram_notifier.chat_id),
        "allowed_chat_id_set": bool(telegram_notifier.allowed_chat_id),
        "recent_alert_count": len(notifier.get_recent_alerts(100)),
        "instructions": {
            "step_1": "Open Telegram and search for @BotFather",
            "step_2": "Send /newbot to create your bot and copy the API Token",
            "step_3": "Start a chat with your bot or with @userinfobot to get your numeric Chat ID",
            "step_4": "Configure via POST /api/notifications/configure or in your .env file"
        }
    }

@router.get("/recent")
def get_recent_alerts(limit: int = 30):
    """
    Returns the history of recently dispatched mobile and system trade alerts.
    """
    return {
        "total": len(notifier.get_recent_alerts(100)),
        "alerts": notifier.get_recent_alerts(limit)
    }

@router.post("/configure")
def configure_telegram(req: TelegramConfigRequest):
    """
    Updates Telegram Bot credentials dynamically without needing server restart.
    """
    telegram_notifier.bot_token = req.bot_token.strip()
    telegram_notifier.chat_id = req.chat_id.strip()
    telegram_notifier.allowed_chat_id = (req.allowed_chat_id or req.chat_id).strip()
    telegram_notifier.enabled = req.enabled
    telegram_notifier.base_url = f"https://api.telegram.org/bot{telegram_notifier.bot_token}"

    return {
        "status": "CONFIGURED",
        "configured": telegram_notifier.is_configured,
        "enabled": telegram_notifier.enabled,
        "chat_id": telegram_notifier.chat_id,
        "allowed_chat_id": telegram_notifier.allowed_chat_id
    }

@router.post("/test")
async def send_test_notification(req: Optional[TestNotificationRequest] = None):
    """
    Sends an immediate test alert to the configured Telegram chat to verify mobile delivery.
    """
    if req and req.custom_message:
        sent = await telegram_notifier.send_message(f"<b>🔔 Test Alert from Trading Agent:</b>\n\n{req.custom_message}")
        return {"success": sent, "message": "Custom test alert dispatched"}
    
    res = await telegram_notifier.test_connection()
    return res
