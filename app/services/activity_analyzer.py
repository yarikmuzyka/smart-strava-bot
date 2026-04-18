class ActivityAnalyzer:
    def analyze_latest_ride(self, activity: dict, recent_activities: list[dict] | None = None) -> dict:
        recent_activities = recent_activities or []
        duration_minutes = round((activity.get("moving_time") or 0) / 60)
        distance_km = self._meters_to_km(activity.get("distance"))
        elevation_gain = round(activity.get("total_elevation_gain") or 0)
        average_speed_kmh = self._mps_to_kmh(activity.get("average_speed"))
        average_watts = activity.get("average_watts")
        average_hr = activity.get("average_heartrate")
        trainer = bool(activity.get("trainer"))
        sport_type = activity.get("sport_type") or "Ride"

        ride_category = self._classify_ride(
            duration_minutes=duration_minutes,
            elevation_gain=elevation_gain,
            average_watts=average_watts,
            trainer=trainer,
        )
        fatigue_signal, load_label = self._estimate_fatigue(
            ride_category=ride_category,
            duration_minutes=duration_minutes,
            elevation_gain=elevation_gain,
            average_watts=average_watts,
            recent_activities=recent_activities,
        )
        recent_context = self._build_recent_context(recent_activities)

        observations = self._build_observations(
            sport_type=sport_type,
            duration_minutes=duration_minutes,
            distance_km=distance_km,
            elevation_gain=elevation_gain,
            average_speed_kmh=average_speed_kmh,
            average_watts=average_watts,
            average_hr=average_hr,
            trainer=trainer,
            ride_category=ride_category,
            fatigue_signal=fatigue_signal,
            recent_context=recent_context,
        )

        return {
            "ride_category": ride_category,
            "fatigue_signal": fatigue_signal,
            "load_label": load_label,
            "key_observations": observations,
            "recent_7d_ride_count": recent_context["ride_count"],
            "recent_7d_moving_time_h": recent_context["moving_time_h"],
            "recent_7d_distance_km": recent_context["distance_km"],
            "hard_rides_last_7d": recent_context["hard_rides"],
            "metrics": {
                "duration_minutes": duration_minutes,
                "distance_km": distance_km,
                "elevation_gain_m": elevation_gain,
                "average_speed_kmh": average_speed_kmh,
                "average_watts": average_watts,
                "average_heartrate": average_hr,
                "trainer": trainer,
            },
            "raw_activity": activity,
        }

    def aggregate_power_zones(self, activity_zones: list[list[dict]]) -> list[dict]:
        zone_totals: dict[int, int] = {}

        for zones in activity_zones:
            power_zone = next((zone for zone in zones if zone.get("type") == "power"), None)
            if not power_zone:
                continue

            buckets = power_zone.get("distribution_buckets") or []
            for index, bucket in enumerate(buckets, start=1):
                zone_totals[index] = zone_totals.get(index, 0) + int(bucket.get("time", 0))

        total_seconds = sum(zone_totals.values())
        if total_seconds == 0:
            return []

        return [
            {
                "zone": f"Z{zone}",
                "percentage": round((seconds / total_seconds) * 100, 1),
            }
            for zone, seconds in sorted(zone_totals.items())
            if zone <= 5
        ]

    def _classify_ride(
        self,
        *,
        duration_minutes: int,
        elevation_gain: int,
        average_watts: float | None,
        trainer: bool,
    ) -> str:
        if duration_minutes >= 180:
            return "long ride"
        if average_watts and average_watts >= 240:
            return "high-intensity session"
        if average_watts and average_watts >= 185:
            return "tempo or threshold ride"
        if duration_minutes >= 120 or elevation_gain >= 1200:
            return "endurance ride"
        if trainer and duration_minutes <= 75 and average_watts:
            return "structured indoor session"
        if duration_minutes <= 50:
            return "short easy spin"
        return "steady endurance ride"

    def _estimate_fatigue(
        self,
        *,
        ride_category: str,
        duration_minutes: int,
        elevation_gain: int,
        average_watts: float | None,
        recent_activities: list[dict],
    ) -> tuple[str, str]:
        score = 0

        if duration_minutes >= 180:
            score += 3
        elif duration_minutes >= 120:
            score += 2
        elif duration_minutes >= 75:
            score += 1

        if elevation_gain >= 1500:
            score += 2
        elif elevation_gain >= 800:
            score += 1

        if average_watts and average_watts >= 240:
            score += 2
        elif average_watts and average_watts >= 185:
            score += 1

        if "high-intensity" in ride_category or "threshold" in ride_category:
            score += 1

        recent_context = self._build_recent_context(recent_activities)
        if recent_context["ride_count"] >= 5:
            score += 1
        if recent_context["hard_rides"] >= 2:
            score += 2
        if recent_context["moving_time_h"] >= 8:
            score += 1

        if score >= 5:
            return "high", "high"
        if score >= 3:
            return "moderate", "moderate"
        return "low", "light"

    def _build_observations(
        self,
        *,
        sport_type: str,
        duration_minutes: int,
        distance_km: float,
        elevation_gain: int,
        average_speed_kmh: float | None,
        average_watts: float | None,
        average_hr: float | None,
        trainer: bool,
        ride_category: str,
        fatigue_signal: str,
        recent_context: dict,
    ) -> list[str]:
        observations: list[str] = []
        observations.append(
            f"{sport_type}: {duration_minutes} min / {distance_km:.1f} km."
        )

        if average_watts:
            observations.append(f"Average power: {round(average_watts)} W.")
        elif average_speed_kmh:
            observations.append(f"Average speed: {average_speed_kmh:.1f} km/h.")

        if average_hr:
            observations.append(f"Average heart rate: {round(average_hr)} bpm.")

        if trainer:
            observations.append("Trainer ride.")

        return observations[:4]

    def _meters_to_km(self, value: float | None) -> float:
        if value is None:
            return 0.0
        return value / 1000

    def _mps_to_kmh(self, value: float | None) -> float | None:
        if value is None:
            return None
        return value * 3.6

    def _build_recent_context(self, recent_activities: list[dict]) -> dict:
        ride_count = len(recent_activities)
        moving_time_h = round(
            sum((item.get("moving_time") or 0) for item in recent_activities) / 3600,
            1,
        )
        distance_km = round(
            sum((item.get("distance") or 0) for item in recent_activities) / 1000,
            1,
        )
        hard_rides = 0

        for item in recent_activities:
            duration_minutes = round((item.get("moving_time") or 0) / 60)
            elevation_gain = round(item.get("total_elevation_gain") or 0)
            average_watts = item.get("average_watts")

            if duration_minutes >= 180:
                hard_rides += 1
                continue
            if average_watts and average_watts >= 220:
                hard_rides += 1
                continue
            if elevation_gain >= 1400 and duration_minutes >= 90:
                hard_rides += 1

        return {
            "ride_count": ride_count,
            "moving_time_h": moving_time_h,
            "distance_km": distance_km,
            "hard_rides": hard_rides,
        }
