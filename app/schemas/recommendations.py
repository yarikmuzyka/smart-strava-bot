from pydantic import BaseModel


class RecommendationOption(BaseModel):
    code: str
    title: str
    summary: str


class RecommendationPair(BaseModel):
    option_a: RecommendationOption
    option_b: RecommendationOption


class RideAnalysis(BaseModel):
    ride_category: str
    fatigue_signal: str
    load_label: str
    key_observations: list[str]
    recent_7d_ride_count: int
    recent_7d_moving_time_h: float
    recent_7d_distance_km: float
    hard_rides_last_7d: int


class PowerZoneDistribution(BaseModel):
    zone: str
    percentage: float


class RideRecommendationResponse(BaseModel):
    athlete_id: int
    ride_name: str
    analysis: RideAnalysis
    recommendations: RecommendationPair
    recent_7d_power_zones: list[PowerZoneDistribution]
    summary_text: str
    telegram_text: str
