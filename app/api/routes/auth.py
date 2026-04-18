from fastapi import APIRouter, HTTPException, Query, status

from app.integrations.strava import StravaClient
from app.schemas.auth import (
    AuthStartResponse,
    StravaActivitySummary,
    StravaAthleteSummary,
    StravaLatestActivityResponse,
    StravaOAuthCallbackResponse,
)
from app.schemas.recommendations import RideRecommendationResponse
from app.schemas.storage import StoredStravaConnection
from app.services.recommendation_service import RecommendationService
from app.services.token_store import TokenStore

router = APIRouter()


@router.get("/strava/start", response_model=AuthStartResponse)
def start_strava_auth() -> AuthStartResponse:
    client = StravaClient()
    state = client.create_state()
    return AuthStartResponse(url=client.build_authorize_url(state=state))


@router.get("/strava/callback", response_model=StravaOAuthCallbackResponse)
async def strava_callback(
    code: str | None = None,
    scope: str | None = None,
    state: str | None = None,
    error: str | None = Query(default=None),
) -> StravaOAuthCallbackResponse:
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strava authorization failed: {error}",
        )

    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Strava callback parameters.",
        )

    client = StravaClient()
    client.validate_state(state)
    token_result = await client.exchange_code_for_token(code)
    scopes = [item.strip() for item in scope.split(",")] if scope else []

    token_store = TokenStore()
    token_store.save_connection(
        StoredStravaConnection(
            athlete=token_result.athlete,
            access_token=token_result.access_token,
            refresh_token=token_result.refresh_token,
            expires_at=token_result.expires_at,
            scope=scopes,
        )
    )

    return StravaOAuthCallbackResponse(
        message="Strava account connected successfully.",
        athlete=StravaAthleteSummary(**token_result.athlete.model_dump()),
        scopes=scopes,
        expires_at=token_result.expires_at,
        access_token_received=bool(token_result.access_token),
        refresh_token_received=bool(token_result.refresh_token),
    )


@router.get("/strava/latest-activity", response_model=StravaLatestActivityResponse)
async def get_latest_activity(athlete_id: int) -> StravaLatestActivityResponse:
    token_store = TokenStore()
    connection = token_store.get_connection(athlete_id)

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stored Strava connection for this athlete. Reconnect Strava first.",
        )

    client = StravaClient()
    activity = await client.get_latest_activity(connection.access_token)

    if activity is None:
        return StravaLatestActivityResponse(
            athlete_id=athlete_id,
            activity=None,
            message="No activities found for this athlete yet.",
        )

    return StravaLatestActivityResponse(
        athlete_id=athlete_id,
        activity=StravaActivitySummary(
            id=activity.id,
            name=activity.name,
            sport_type=activity.sport_type,
            start_date=activity.start_date,
            distance_m=activity.distance,
            moving_time_s=activity.moving_time,
            elevation_gain_m=activity.total_elevation_gain,
            average_speed_mps=activity.average_speed,
            average_heartrate=activity.average_heartrate,
            average_watts=activity.average_watts,
            trainer=activity.trainer,
        ),
        message="Latest activity fetched successfully.",
    )


@router.get("/strava/latest-recommendation", response_model=RideRecommendationResponse)
async def get_latest_recommendation(athlete_id: int) -> RideRecommendationResponse:
    service = RecommendationService()
    return await service.build_latest_recommendation(athlete_id)
