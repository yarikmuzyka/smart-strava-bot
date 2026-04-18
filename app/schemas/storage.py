from pydantic import BaseModel

from app.integrations.strava import StravaAthlete


class StoredStravaConnection(BaseModel):
    athlete: StravaAthlete
    access_token: str
    refresh_token: str
    expires_at: int
    scope: list[str]
