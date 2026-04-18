from fastapi import APIRouter, Query

from app.core.config import get_settings
from app.schemas.webhooks import StravaWebhookEvent
from app.services.chat_binding_store import ChatBindingStore
from app.services.recommendation_service import RecommendationService
from app.integrations.telegram import TelegramClient

router = APIRouter()


@router.get("/strava")
def verify_strava_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> dict[str, str]:
    settings = get_settings()

    if hub_mode == "subscribe" and hub_verify_token == settings.strava_verify_token:
        return {"hub.challenge": hub_challenge}

    return {"hub.challenge": ""}


@router.post("/strava")
async def receive_strava_webhook(event: StravaWebhookEvent) -> dict[str, str]:
    if event.object_type != "activity":
        return {"status": "ignored"}

    if event.aspect_type != "create":
        return {"status": "ignored"}

    chat_binding_store = ChatBindingStore()
    chat_id = chat_binding_store.get_chat_id(event.owner_id)
    if chat_id is None:
        return {"status": "accepted_no_chat_binding"}

    recommendation_service = RecommendationService()
    recommendation = await recommendation_service.build_recommendation_for_activity(
        athlete_id=event.owner_id,
        activity_id=event.object_id,
    )

    telegram_client = TelegramClient()
    await telegram_client.send_message(
        chat_id=chat_id,
        text=recommendation.telegram_text,
        parse_mode="HTML",
    )

    return {"status": "delivered"}
