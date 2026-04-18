from app.schemas.recommendations import RecommendationOption, RecommendationPair


class RecommendationEngine:
    def choose_for_tomorrow(self, analysis: dict) -> RecommendationPair:
        fatigue_signal = analysis.get("fatigue_signal", "low")
        ride_category = analysis.get("ride_category", "")
        hard_rides_last_7d = analysis.get("hard_rides_last_7d", 0)
        recent_7d_ride_count = analysis.get("recent_7d_ride_count", 0)
        recent_7d_moving_time_h = analysis.get("recent_7d_moving_time_h", 0.0)

        if hard_rides_last_7d >= 2 or recent_7d_moving_time_h >= 8:
            return RecommendationPair(
                option_a=RecommendationOption(
                    code="rest_day",
                    title="Rest day",
                    summary="Weekly load looks elevated, so full recovery is the safest call.",
                ),
                option_b=RecommendationOption(
                    code="recovery_spin_45_60",
                    title="Recovery spin 45-60 min",
                    summary="Keep it very easy and only use it to stay loose.",
                ),
            )

        if fatigue_signal == "high":
            return RecommendationPair(
                option_a=RecommendationOption(
                    code="rest_day",
                    title="Rest day",
                    summary="Take a full day off the bike to absorb the load.",
                ),
                option_b=RecommendationOption(
                    code="recovery_spin_45_60",
                    title="Recovery spin 45-60 min",
                    summary="Ride very easy in Z1-Z2 with relaxed cadence only if the legs feel okay.",
                ),
            )

        if fatigue_signal == "moderate":
            return RecommendationPair(
                option_a=RecommendationOption(
                    code="recovery_spin_45_60",
                    title="Recovery spin 45-60 min",
                    summary="Keep it easy and aerobic, mainly for circulation and recovery.",
                ),
                option_b=RecommendationOption(
                    code="endurance_60_90",
                    title="Endurance ride 60-90 min",
                    summary="A steady Z2 ride if you wake up feeling fresh enough.",
                ),
            )

        if "short easy spin" in ride_category:
            return RecommendationPair(
                option_a=RecommendationOption(
                    code="endurance_90_120",
                    title="Endurance ride 90-120 min",
                    summary="Build aerobic volume with a controlled Z2 ride.",
                ),
                option_b=RecommendationOption(
                    code="tempo_3x10",
                    title="Tempo 3x10 min",
                    summary="Ride 3 efforts at strong but controlled tempo with easy recovery between them.",
                ),
            )

        if recent_7d_ride_count <= 2 and fatigue_signal == "low":
            return RecommendationPair(
                option_a=RecommendationOption(
                    code="endurance_90_120",
                    title="Endurance ride 90-120 min",
                    summary="Good option to add aerobic volume while you still look relatively fresh.",
                ),
                option_b=RecommendationOption(
                    code="tempo_2x12",
                    title="Tempo 2x12 min",
                    summary="A compact quality session if you want a bit more structure tomorrow.",
                ),
            )

        return RecommendationPair(
            option_a=RecommendationOption(
                code="endurance_60_90",
                title="Endurance ride 60-90 min",
                summary="Keep it mostly Z2 and aim for smooth, steady pressure on the pedals.",
            ),
            option_b=RecommendationOption(
                code="tempo_2x12",
                title="Tempo 2x12 min",
                summary="Do 2 controlled tempo blocks if you feel fresh and want a bit more stimulus.",
            ),
        )
