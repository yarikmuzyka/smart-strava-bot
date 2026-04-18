from pydantic import BaseModel


class AuthStartResponse(BaseModel):
    url: str


class StravaAthleteSummary(BaseModel):
    id: int
    username: str | None = None
    firstname: str | None = None
    lastname: str | None = None


class StravaOAuthCallbackResponse(BaseModel):
    message: str
    athlete: StravaAthleteSummary
    scopes: list[str]
    expires_at: int
    access_token_received: bool
    refresh_token_received: bool


class StravaActivitySummary(BaseModel):
    id: int
    name: str
    sport_type: str
    start_date: str | None = None
    distance_m: float | None = None
    moving_time_s: int | None = None
    elevation_gain_m: float | None = None
    average_speed_mps: float | None = None
    average_heartrate: float | None = None
    average_watts: float | None = None
    trainer: bool | None = None


class StravaLatestActivityResponse(BaseModel):
    athlete_id: int
    activity: StravaActivitySummary | None = None
    message: str
