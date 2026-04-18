import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.telegram import TelegramSendMessageResponse


class TelegramClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
    ) -> TelegramSendMessageResponse:
        if not self.settings.telegram_bot_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Telegram bot token is not configured.",
            )

        url = (
            f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        )
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = "Telegram sendMessage failed."
                try:
                    error_payload = exc.response.json()
                    if isinstance(error_payload, dict) and error_payload.get("description"):
                        detail = f"{detail} {error_payload['description']}"
                except ValueError:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=detail,
                ) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to reach Telegram API.",
                ) from exc

        return TelegramSendMessageResponse.model_validate(response.json())
