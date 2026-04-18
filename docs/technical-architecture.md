# Technical Architecture

## Recommended Approach

For the first implementation, use a small service-oriented backend:

- `FastAPI` for backend and webhook endpoints
- `PostgreSQL` for persistent data
- `Redis` for lightweight jobs and caching
- `Telegram Bot API` for delivery and commands
- `Strava API` for athlete authentication and ride data
- `OpenAI API` for concise summaries with structured outputs

This stack is practical for a narrow MVP and keeps the recommendation logic in
our control.

## High-Level Flow

1. User starts the Telegram bot
2. Bot provides Strava connect link
3. User completes Strava OAuth in browser
4. Backend stores tokens and athlete mapping
5. Strava webhook notifies backend about a new activity
6. Backend fetches activity details
7. Analyzer computes ride features and fatigue state
8. Recommendation engine chooses two next-day options
9. LLM formats a short Telegram-ready message
10. Bot sends the summary to the user

## Services

### 1. API Service

Responsibilities:

- Telegram webhook or polling handler
- Strava OAuth callback
- Strava webhook verification and event intake
- internal endpoints for profile updates

### 2. Ingestion Service

Responsibilities:

- fetch latest ride details from Strava
- normalize raw activity payload
- upsert activity records

### 3. Analysis Service

Responsibilities:

- calculate derived ride metrics
- classify ride
- compute fatigue and recent load features

### 4. Recommendation Service

Responsibilities:

- apply rules from `recommendation-rules-v1.md`
- produce exactly two candidate workouts
- record reasoning metadata for debugging

### 5. Messaging Service

Responsibilities:

- build Telegram message payloads
- send summary
- later handle feedback buttons

## Data Model

### users

- `id`
- `telegram_user_id`
- `telegram_chat_id`
- `created_at`

### strava_connections

- `id`
- `user_id`
- `strava_athlete_id`
- `access_token`
- `refresh_token`
- `expires_at`

### athlete_profiles

- `user_id`
- `goal`
- `ftp`
- `max_hr`
- `available_days_per_week`
- `preferred_long_ride_day`
- `has_indoor_trainer`

### activities

- `id`
- `user_id`
- `strava_activity_id`
- `sport_type`
- `start_date`
- `raw_payload_json`
- `moving_time_sec`
- `distance_m`
- `elevation_gain_m`
- `avg_hr`
- `max_hr`
- `avg_cadence`
- `avg_watts`
- `weighted_avg_watts`
- `trainer`

### activity_features

- `activity_id`
- `ride_category`
- `duration_minutes`
- `distance_km`
- `load_score_simple`
- `fatigue_signal`
- `recent_7d_load`
- `days_since_last_hard_ride`

### daily_recommendations

- `id`
- `user_id`
- `source_activity_id`
- `option_a_code`
- `option_b_code`
- `reasoning_json`
- `telegram_message_text`
- `created_at`

### user_feedback

- `id`
- `user_id`
- `recommendation_id`
- `selected_option`
- `feedback_value`
- `created_at`

## API Endpoints

Minimum endpoints:

- `GET /health`
- `GET /auth/strava/start`
- `GET /auth/strava/callback`
- `POST /webhooks/strava`
- `GET /webhooks/strava` for verification
- `POST /webhooks/telegram`

## Recommendation Engine Boundary

Important design choice:

- deterministic code selects the recommendation pair
- the LLM does not invent the training structure

The LLM receives:

- ride classification
- key observations
- two recommendation objects

The LLM returns:

- short summary
- final Telegram-ready phrasing

## Suggested Repository Structure

```text
app/
  api/
  services/
  models/
  schemas/
  integrations/
  rules/
  prompts/
docs/
  README.md
  mvp-spec.md
  recommendation-rules-v1.md
  technical-architecture.md
```

## Delivery Phases

### Phase 1: Product Foundation

- finalize MVP spec
- finalize recommendation rules
- finalize architecture

### Phase 2: Functional Prototype

- create FastAPI service skeleton
- implement Telegram bot setup
- implement Strava OAuth flow
- store users and tokens

### Phase 3: First Useful Automation

- implement webhook ingestion
- store activities
- compute simple features
- send first automated recommendation

### Phase 4: Quality Upgrade

- add feedback buttons
- improve personalization
- add baseline comparisons
- refine prompts and rules

## Decisions To Make Soon

- Python or Node.js as the implementation language
- webhook deployment target
- whether to support polling during local development
- whether FTP is required or optional during onboarding
