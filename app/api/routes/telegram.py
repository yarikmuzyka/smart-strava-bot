import secrets

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import get_settings
from app.integrations.telegram import TelegramClient
from app.schemas.chat_binding import AthleteChatBinding
from app.schemas.telegram import TelegramDeliveryResponse
from app.schemas.telegram import TelegramUpdate
from app.schemas.telegram import TelegramWebhookResponse
from app.services.chat_binding_store import ChatBindingStore
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.post("/webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> TelegramWebhookResponse:
    settings = get_settings()
    if settings.telegram_webhook_secret:
        if not x_telegram_bot_api_secret_token or not secrets.compare_digest(
            x_telegram_bot_api_secret_token,
            settings.telegram_webhook_secret,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram webhook secret.",
            )

    message = update.message
    if message is None or not message.text:
        return TelegramWebhookResponse(status="accepted", handled=False)

    command = message.text.strip().split()[0].lower()
    telegram_client = TelegramClient()
    chat_binding_store = ChatBindingStore()

    if command == "/start":
        if settings.default_strava_athlete_id is not None:
            chat_binding_store.save_binding(
                AthleteChatBinding(
                    athlete_id=settings.default_strava_athlete_id,
                    chat_id=message.chat.id,
                )
            )
        await telegram_client.send_message(
            chat_id=message.chat.id,
            text=(
                "Smart Strava Bot is ready.\n"
                "Use /last_ride to analyze your latest Strava ride and get two training options."
            ),
        )
        return TelegramWebhookResponse(status="accepted", handled=True, command=command)

    if command == "/last_ride":
        if settings.default_strava_athlete_id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DEFAULT_STRAVA_ATHLETE_ID is not configured.",
            )

        chat_binding_store.save_binding(
            AthleteChatBinding(
                athlete_id=settings.default_strava_athlete_id,
                chat_id=message.chat.id,
            )
        )
        recommendation_service = RecommendationService()
        recommendation = await recommendation_service.build_latest_recommendation(
            settings.default_strava_athlete_id
        )
        await telegram_client.send_message(
            chat_id=message.chat.id,
            text=recommendation.telegram_text,
            parse_mode="HTML",
        )
        return TelegramWebhookResponse(status="accepted", handled=True, command=command)

    await telegram_client.send_message(
        chat_id=message.chat.id,
        text="Unknown command. Try /start or /last_ride.",
    )
    return TelegramWebhookResponse(status="accepted", handled=True, command=command)


@router.post("/send-latest-recommendation", response_model=TelegramDeliveryResponse)
async def send_latest_recommendation(
    athlete_id: int,
    chat_id: int,
) -> TelegramDeliveryResponse:
    recommendation_service = RecommendationService()
    recommendation = await recommendation_service.build_latest_recommendation(athlete_id)

    telegram_client = TelegramClient()
    telegram_response = await telegram_client.send_message(
        chat_id=chat_id,
        text=recommendation.telegram_text,
        parse_mode="HTML",
    )

    return TelegramDeliveryResponse(
        athlete_id=athlete_id,
        chat_id=chat_id,
        delivered=telegram_response.ok,
        message="Latest recommendation sent to Telegram.",
    )
