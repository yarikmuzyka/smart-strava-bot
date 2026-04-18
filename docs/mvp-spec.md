# Cycling Coach Bot MVP Spec

## Product Summary

Cycling Coach Bot is a Telegram bot for amateur and enthusiast cyclists. After
each new ride appears in Strava, the bot analyzes the ride and sends a short
summary with two training options for the next day.

The bot is not a full training platform in v1. It focuses on one fast, useful
moment:

- understand what today's ride was
- estimate likely fatigue and recovery state
- suggest two sensible options for tomorrow

## Primary User

The initial user profile is:

- road cyclist or gravel cyclist
- trains 3 to 6 days per week
- tracks rides in Strava
- may or may not have a power meter
- wants actionable guidance, not long reports

## Product Goal

Deliver a useful coaching interaction within 15 to 30 seconds after a ride is
available in Strava.

Success means the user feels:

- "this summary understood my ride"
- "the two options for tomorrow are realistic"
- "I can make a decision quickly"

## Core User Story

As a cyclist, I want my latest Strava ride to be analyzed automatically so that
I receive a short explanation of the session and two recommendations for the
next day in Telegram.

## MVP Scope

### In Scope

- connect Strava account via OAuth
- receive new ride events from Strava webhook
- fetch latest ride details from Strava API
- analyze latest ride plus recent 7-day training context
- send concise Telegram summary
- suggest exactly two next-day training options
- store user settings needed for better recommendations

### Out of Scope

- full multi-week training plans
- race prediction
- deep nutrition guidance
- injury detection
- support for multiple sports in v1
- advanced chart-heavy dashboards

## Inputs

### From Strava

- activity id
- sport type
- name
- start date
- moving time
- elapsed time
- distance
- elevation gain
- average speed
- average heart rate
- max heart rate
- average cadence
- average watts
- weighted average watts if available
- max watts
- trainer flag
- commute flag
- manual activity flag if available

### From User Profile

- training goal
- ftp if known
- max heart rate if known
- preferred long ride day
- available training days per week
- indoor trainer available or not

## Output Format

The Telegram message should be short and structured.

Template:

1. one-line ride classification
2. 2 to 4 key observations
3. two options for tomorrow

Example:

`Today's ride: 1h48 endurance with moderate climbing.`

- load was moderate to high for a weekday session
- heart rate stayed stable for most of the ride
- last 20 minutes suggest mild fatigue

`Tomorrow:`

- `Option A:` 45-60 min recovery spin in Z1-Z2
- `Option B:` rest day or 30 min easy trainer spin

## User Commands

Initial command set:

- `/start`
- `/connect_strava`
- `/lastride`
- `/tomorrow`
- `/goal`
- `/ftp`
- `/profile`

## Recommendation Philosophy

The bot should not act like an overconfident coach. It should:

- prefer conservative suggestions when fatigue is uncertain
- explain why it chose the recommendation
- never suggest a second hard day after clear high load unless user context supports it
- adapt to missing power data

## Non-Functional Requirements

- summary should be readable in under 20 seconds
- recommendation generation should be deterministic before final phrasing
- recommendations should still work for users without a power meter
- each message should remain useful even with partial Strava data

## Risks

- using only the last ride is too naive
- missing power data reduces recommendation quality
- a generic LLM response can sound convincing but be wrong
- Strava data quality varies by device and recording habits

## MVP Success Metrics

- user successfully connects Strava
- bot sends first summary after a new ride
- recommendation click or feedback rate
- percentage of days where user accepts one of two options
- weekly retention after first connected ride
