from pydantic import BaseModel


class TelegramChat(BaseModel):
    id: int


class TelegramMessage(BaseModel):
    message_id: int
    text: str | None = None
    chat: TelegramChat


class TelegramUpdate(BaseModel):
    update_id: int
    message: TelegramMessage | None = None


class TelegramSendMessageResponse(BaseModel):
    ok: bool
    result: dict | None = None


class TelegramDeliveryResponse(BaseModel):
    athlete_id: int
    chat_id: int
    delivered: bool
    message: str


class TelegramWebhookResponse(BaseModel):
    status: str
    handled: bool
    command: str | None = None
