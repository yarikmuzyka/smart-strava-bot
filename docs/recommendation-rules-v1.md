# Recommendation Rules V1

## Goal

Use a simple deterministic rules engine to:

- classify the latest ride
- estimate next-day freshness
- generate two safe and useful training options

The LLM should not choose training logic on its own. It should only explain the
selected result in concise natural language.

## Analysis Window

Use two time windows:

- latest ride
- recent load over the last 7 days

Optional future extension:

- rolling 28-day baseline

## Ride Classification

Each ride should be assigned one primary type.

### With Power Data

- `recovery`
- `endurance`
- `tempo`
- `threshold`
- `vo2_or_high_intensity`
- `long_ride`

Suggested heuristics:

- `recovery`: low average intensity and short duration
- `endurance`: mostly low to moderate intensity, no major spikes
- `tempo`: sustained moderate-high load without threshold profile
- `threshold`: repeated or sustained high power near ftp
- `vo2_or_high_intensity`: strong peaks and high-intensity concentration
- `long_ride`: duration-driven category that may overlap but wins when ride is unusually long

### Without Power Data

Fallback on:

- duration
- elevation gain
- average speed relative to user baseline
- heart rate pattern
- cadence stability

Categories stay the same, but confidence should be lower.

## Required Derived Features

- `ride_duration_minutes`
- `distance_km`
- `elevation_gain_m`
- `intensity_score_simple`
- `recent_7d_load`
- `days_since_last_hard_ride`
- `hard_days_in_last_3`
- `long_ride_in_last_7d`
- `fatigue_signal`

## Fatigue Signal

Estimate as:

- `low`
- `moderate`
- `high`

Inputs:

- latest ride category
- latest ride duration
- recent 7-day load
- back-to-back hard days
- signs of decoupling if detectable

Examples:

- high-intensity ride after already elevated 7-day load -> `high`
- easy spin after recovery day -> `low`
- long endurance ride with climbing -> `moderate` or `high`

## Training Options Library

The engine may choose from this library in v1:

- `rest_day`
- `recovery_spin_30_45`
- `recovery_spin_45_60`
- `endurance_60_90`
- `endurance_90_120`
- `tempo_2x12`
- `tempo_3x10`
- `threshold_3x8`
- `threshold_4x6`

Each option must include:

- title
- duration
- intensity guidance
- short purpose statement

## Selection Rules

### Rule Group A: High Fatigue

If:

- latest ride is `threshold`, `vo2_or_high_intensity`, or very long `long_ride`
- or `hard_days_in_last_3 >= 2`
- or `recent_7d_load` is well above baseline

Then tomorrow options:

- `Option A:` rest day
- `Option B:` recovery spin 30-45 or 45-60 depending on user availability

### Rule Group B: Moderate Fatigue

If:

- latest ride is endurance or tempo
- and recent load is normal to slightly elevated

Then tomorrow options:

- `Option A:` recovery spin 45-60
- `Option B:` endurance 60-90

### Rule Group C: Low Fatigue After Easy Day

If:

- latest ride is recovery or short endurance
- and no recent overload signals exist

Then tomorrow options:

- `Option A:` endurance 90-120
- `Option B:` tempo 2x12 or 3x10

### Rule Group D: Pre-Long-Ride Positioning

If tomorrow is close to preferred long ride day:

- avoid assigning threshold if that would compromise the long ride
- prefer recovery or short opener style endurance

### Rule Group E: Missing Data Safety

If:

- power absent
- heart rate absent or unreliable
- too little user history

Then:

- bias toward conservative options
- never recommend a hardest-session template

## Message Construction Rules

The message must contain:

- one concise ride label
- 2 to 4 observations
- two clearly distinct next-day options

Tone rules:

- concise
- practical
- not medical
- not absolute

Preferred phrasing:

- "looks like"
- "suggests"
- "better option if you feel fresh"

Avoid:

- false certainty
- very long coaching monologues

## Example Outputs

### Example 1: Hard Trainer Session

Input:

- 68 min indoor ride
- strong power spikes
- elevated recent load

Output direction:

- summary says the ride was high intensity
- note that recovery is the priority
- options: `rest_day` and `recovery_spin_45_60`

### Example 2: Easy Weekday Spin

Input:

- 52 min easy outdoor ride
- low recent load

Output direction:

- summary says this was a light aerobic session
- options: `endurance_90_120` and `tempo_2x12`

## Known Limitations

- no direct interval detection yet
- no readiness input from the athlete yet
- no race calendar awareness in v1
- no weather-aware recommendation logic
