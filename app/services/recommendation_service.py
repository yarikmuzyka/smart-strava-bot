import time

from fastapi import HTTPException, status

from app.integrations.strava import StravaClient
from app.rules.recommender import RecommendationEngine
from app.schemas.recommendations import (
    PowerZoneDistribution,
    RideAnalysis,
    RideRecommendationResponse,
)
from app.services.activity_analyzer import ActivityAnalyzer
from app.services.message_builder import MessageBuilder
from app.services.token_store import TokenStore


class RecommendationService:
    async def build_latest_recommendation(self, athlete_id: int) -> RideRecommendationResponse:
        return await self.build_recommendation_for_activity(athlete_id=athlete_id)

    async def build_recommendation_for_activity(
        self,
        athlete_id: int,
        activity_id: int | None = None,
    ) -> RideRecommendationResponse:
        token_store = TokenStore()
        connection = token_store.get_connection(athlete_id)

        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No stored Strava connection for this athlete. Reconnect Strava first.",
            )

        client = StravaClient()
        connection = await self._ensure_fresh_connection(client, token_store, connection)
        if activity_id is None:
            activity = await client.get_latest_activity(connection.access_token)
        else:
            activity = await client.get_activity_by_id(connection.access_token, activity_id)
        recent_activities = await client.get_recent_activities(
            connection.access_token,
            per_page=10,
            days_back=7,
        )

        if activity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Strava activities found for this athlete yet.",
            )

        analyzer = ActivityAnalyzer()
        analysis = analyzer.analyze_latest_ride(
            activity.model_dump(),
            recent_activities=[item.model_dump() for item in recent_activities],
        )

        zone_payloads = []
        for item in recent_activities:
            zones = await client.get_activity_zones(connection.access_token, item.id)
            if zones:
                zone_payloads.append([zone.model_dump() for zone in zones])

        power_zone_breakdown = [
            PowerZoneDistribution(**item) for item in analyzer.aggregate_power_zones(zone_payloads)
        ]

        recommender = RecommendationEngine()
        recommendations = recommender.choose_for_tomorrow(analysis)

        message_builder = MessageBuilder()
        summary_text = message_builder.build_summary(
            analysis,
            recommendations,
            power_zones=power_zone_breakdown,
        )
        telegram_text = message_builder.build_telegram_summary(
            ride_name=activity.name,
            analysis=analysis,
            recommendations=recommendations,
            power_zones=power_zone_breakdown,
        )

        return RideRecommendationResponse(
            athlete_id=athlete_id,
            ride_name=activity.name,
            analysis=RideAnalysis(
                ride_category=analysis["ride_category"],
                fatigue_signal=analysis["fatigue_signal"],
                load_label=analysis["load_label"],
                key_observations=analysis["key_observations"],
                recent_7d_ride_count=analysis["recent_7d_ride_count"],
                recent_7d_moving_time_h=analysis["recent_7d_moving_time_h"],
                recent_7d_distance_km=analysis["recent_7d_distance_km"],
                hard_rides_last_7d=analysis["hard_rides_last_7d"],
            ),
            recommendations=recommendations,
            recent_7d_power_zones=power_zone_breakdown,
            summary_text=summary_text,
            telegram_text=telegram_text,
        )

    async def _ensure_fresh_connection(self, client: StravaClient, token_store: TokenStore, connection):
        now = int(time.time())
        if connection.expires_at > now + 60:
            return connection

        refreshed = await client.refresh_access_token(connection.refresh_token)
        updated_connection = connection.model_copy(
            update={
                "athlete": refreshed.athlete or connection.athlete,
                "access_token": refreshed.access_token,
                "refresh_token": refreshed.refresh_token,
                "expires_at": refreshed.expires_at,
            }
        )
        token_store.save_connection(updated_connection)
        return updated_connection
