import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import get_settings

CYCLING_SPORT_TYPES = {
    "Ride",
    "VirtualRide",
    "EBikeRide",
    "GravelRide",
    "MountainBikeRide",
    "Handcycle",
    "Velomobile",
}


class StravaAthlete(BaseModel):
    id: int
    username: str | None = None
    firstname: str | None = None
    lastname: str | None = None


class StravaTokenExchangeResult(BaseModel):
    token_type: str
    expires_at: int
    expires_in: int
    refresh_token: str
    access_token: str
    athlete: StravaAthlete | None = None


class StravaActivity(BaseModel):
    id: int
    name: str
    sport_type: str
    start_date: str | None = None
    distance: float | None = None
    moving_time: int | None = None
    total_elevation_gain: float | None = None
    average_speed: float | None = None
    average_heartrate: float | None = None
    average_watts: float | None = None
    trainer: bool | None = None


class StravaZoneBucket(BaseModel):
    max: int | None = None
    min: int | None = None
    time: int


class StravaActivityZone(BaseModel):
    type: str
    score: int | None = None
    sensor_based: bool | None = None
    custom_zones: bool | None = None
    points: int | None = None
    max: int | None = None
    distribution_buckets: list[StravaZoneBucket] | None = None


class StravaClient:
    authorize_url = "https://www.strava.com/oauth/authorize"
    token_url = "https://www.strava.com/oauth/token"
    athlete_activities_url = "https://www.strava.com/api/v3/athlete/activities"
    activity_zones_url_template = "https://www.strava.com/api/v3/activities/{activity_id}/zones"
    activity_url_template = "https://www.strava.com/api/v3/activities/{activity_id}"

    def __init__(self) -> None:
        self.settings = get_settings()

    def build_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self.settings.strava_client_id,
            "redirect_uri": self.settings.strava_redirect_uri,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": self.settings.strava_scopes,
            "state": state,
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    def create_state(self) -> str:
        payload = {
            "nonce": secrets.token_urlsafe(16),
            "issued_at": int(time.time()),
        }
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        signature = self._sign(payload_json)
        return self._encode_state(payload_json, signature)

    def validate_state(self, state: str, max_age_seconds: int = 600) -> None:
        try:
            payload_json, provided_signature = self._decode_state(state)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth state payload.",
            ) from exc

        expected_signature = self._sign(payload_json)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth state verification failed.",
            )

        payload = json.loads(payload_json)
        issued_at = int(payload["issued_at"])
        now = int(time.time())

        if now - issued_at > max_age_seconds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth state expired. Start Strava connect again.",
            )

    async def exchange_code_for_token(self, code: str) -> StravaTokenExchangeResult:
        payload = {
            "code": code,
            "grant_type": "authorization_code",
        }
        return await self._exchange_token(payload)

    async def refresh_access_token(self, refresh_token: str) -> StravaTokenExchangeResult:
        payload = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        return await self._exchange_token(payload)

    async def get_latest_activity(self, access_token: str) -> StravaActivity | None:
        activities = await self.get_recent_activities(
            access_token=access_token,
            per_page=30,
            days_back=30,
        )
        if not activities:
            return None
        return self._select_latest_cycling_activity(activities)

    async def get_recent_activities(
        self,
        access_token: str,
        *,
        per_page: int = 7,
        days_back: int = 7,
    ) -> list[StravaActivity]:
        headers = {"Authorization": f"Bearer {access_token}"}
        after = int((datetime.now(UTC) - timedelta(days=days_back)).timestamp())
        params = {"page": 1, "per_page": per_page, "after": after}

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(
                    self.athlete_activities_url,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = "Failed to fetch latest Strava activity."
                try:
                    error_payload = exc.response.json()
                    if isinstance(error_payload, dict) and error_payload.get("message"):
                        detail = f"{detail} {error_payload['message']}"
                except ValueError:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=detail,
                ) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to reach Strava while fetching activities.",
                ) from exc

        activities = response.json()
        if not activities:
            return []

        return [StravaActivity.model_validate(item) for item in activities]

    async def get_activity_by_id(
        self,
        access_token: str,
        activity_id: int,
    ) -> StravaActivity:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = self.activity_url_template.format(activity_id=activity_id)

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = "Failed to fetch Strava activity."
                try:
                    error_payload = exc.response.json()
                    if isinstance(error_payload, dict) and error_payload.get("message"):
                        detail = f"{detail} {error_payload['message']}"
                except ValueError:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=detail,
                ) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to reach Strava while fetching the activity.",
                ) from exc

        return StravaActivity.model_validate(response.json())

    async def get_activity_zones(
        self,
        access_token: str,
        activity_id: int,
    ) -> list[StravaActivityZone]:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = self.activity_zones_url_template.format(activity_id=activity_id)

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in {401, 403, 404}:
                    return []
                detail = "Failed to fetch Strava activity zones."
                try:
                    error_payload = exc.response.json()
                    if isinstance(error_payload, dict) and error_payload.get("message"):
                        detail = f"{detail} {error_payload['message']}"
                except ValueError:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=detail,
                ) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to reach Strava while fetching activity zones.",
                ) from exc

        return [StravaActivityZone.model_validate(item) for item in response.json()]

    def _select_latest_cycling_activity(
        self,
        activities: list[StravaActivity],
    ) -> StravaActivity | None:
        if not activities:
            return None

        sorted_activities = sorted(
            activities,
            key=lambda activity: activity.start_date or "",
            reverse=True,
        )

        for activity in sorted_activities:
            if activity.sport_type in CYCLING_SPORT_TYPES:
                return activity

        return sorted_activities[0]

    async def _exchange_token(self, payload: dict[str, str]) -> StravaTokenExchangeResult:
        if not self.settings.strava_client_id or not self.settings.strava_client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Strava credentials are not configured.",
            )

        request_payload = {
            "client_id": self.settings.strava_client_id,
            "client_secret": self.settings.strava_client_secret,
            **payload,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(self.token_url, data=request_payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = "Strava token exchange failed."
                try:
                    error_payload = exc.response.json()
                    if isinstance(error_payload, dict) and error_payload.get("message"):
                        detail = f"{detail} {error_payload['message']}"
                except ValueError:
                    pass
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=detail,
                ) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to reach Strava during token exchange.",
                ) from exc

        return StravaTokenExchangeResult.model_validate(response.json())

    def _sign(self, payload_json: str) -> str:
        digest = hmac.new(
            self.settings.app_secret_key.encode("utf-8"),
            payload_json.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    def _encode_state(self, payload_json: str, signature: str) -> str:
        payload = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
        return f"{payload}.{signature}"

    def _decode_state(self, state: str) -> tuple[str, str]:
        encoded_payload, signature = state.split(".", 1)
        padding = "=" * (-len(encoded_payload) % 4)
        payload_json = base64.urlsafe_b64decode(f"{encoded_payload}{padding}").decode("utf-8")
        return payload_json, signature
