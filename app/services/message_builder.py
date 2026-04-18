from html import escape

from app.schemas.recommendations import PowerZoneDistribution, RecommendationPair

ZONE_MARKERS = {
    "Z1": "⚪",
    "Z2": "🔵",
    "Z3": "🟢",
    "Z4": "🟡",
    "Z5": "🟠",
}


class MessageBuilder:
    def build_summary(
        self,
        analysis: dict,
        recommendations: RecommendationPair,
        power_zones: list[PowerZoneDistribution] | None = None,
    ) -> str:
        ride_category = analysis.get("ride_category", "ride")
        fatigue_signal = analysis.get("fatigue_signal", "unknown")
        load_label = analysis.get("load_label", "unknown")
        observations = analysis.get("key_observations", [])
        observation_lines = "\n".join(f"- {item}" for item in observations)
        power_zone_line = ""

        if power_zones:
            compact = ", ".join(f"{zone.zone} {zone.percentage:.1f}%" for zone in power_zones)
            power_zone_line = f"\n\nLast 7 days power zones: {compact}"

        return (
            f"Last ride analysis: {ride_category}.\n"
            f"Estimated load: {load_label}. Fatigue signal: {fatigue_signal}.\n\n"
            f"{observation_lines}\n\n"
            f"Next options:\n"
            f"A. {recommendations.option_a.title} - {recommendations.option_a.summary}\n"
            f"B. {recommendations.option_b.title} - {recommendations.option_b.summary}"
            f"{power_zone_line}"
        )

    def build_telegram_summary(
        self,
        ride_name: str,
        analysis: dict,
        recommendations: RecommendationPair,
        power_zones: list[PowerZoneDistribution] | None = None,
    ) -> str:
        fatigue_signal = escape(analysis.get("fatigue_signal", "unknown").title())
        load_label = escape(analysis.get("load_label", "unknown").title())
        observations = analysis.get("key_observations", [])
        power_zone_line = ""
        training_vibe = self._build_training_vibe(analysis)

        if power_zones:
            visible_power_zones = [zone for zone in power_zones if zone.percentage >= 10]
            if not visible_power_zones:
                visible_power_zones = power_zones
            zone_lines = "\n".join(
                f"{ZONE_MARKERS.get(zone.zone, '⚫')} {zone.zone}: <b>{zone.percentage:.0f}%</b>"
                for zone in visible_power_zones
            )
            power_zone_line = f"\n\n⚡ <b>7d Power Zones</b>\n{zone_lines}"

        observation_lines = "\n".join(f"• {escape(item)}" for item in observations)

        return (
            f"🚴 <b>Last Ride: {escape(training_vibe)}</b>\n"
            f"{escape(ride_name)}\n\n"
            f"📌 <b>Summary</b>\n"
            f"Load: {load_label}\n"
            f"Fatigue: {fatigue_signal}\n\n"
            f"📊 <b>Key Notes</b>\n"
            f"{observation_lines}\n\n"
            f"🧭 <b>Next Options</b>\n"
            f"A. <b>{escape(recommendations.option_a.title)}</b>\n"
            f"{escape(recommendations.option_a.summary)}\n\n"
            f"B. <b>{escape(recommendations.option_b.title)}</b>\n"
            f"{escape(recommendations.option_b.summary)}"
            f"{power_zone_line}"
        )

    def _build_training_vibe(self, analysis: dict) -> str:
        ride_category = analysis.get("ride_category", "")
        fatigue_signal = analysis.get("fatigue_signal", "")
        load_label = analysis.get("load_label", "")
        observations = analysis.get("key_observations", [])

        first_observation = observations[0] if observations else ""
        duration_minutes = 0
        try:
            duration_minutes = int(first_observation.split(":")[1].split("min")[0].strip())
        except (IndexError, ValueError):
            duration_minutes = 0

        if "short easy spin" in ride_category or (load_label == "light" and duration_minutes <= 75):
            return "Vovan style"
        if "high-intensity" in ride_category:
            return "Pogacar style"
        if "tempo or threshold" in ride_category:
            return "Remco style"
        if "long ride" in ride_category:
            return "Van Aert style"
        if "structured indoor" in ride_category:
            return "Ganna style"
        if fatigue_signal == "low":
            return "Vingegaard style"
        return "Classic diesel style"
