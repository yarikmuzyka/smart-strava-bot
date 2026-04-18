# Cycling Coach Bot

This folder stores the product and technical foundation for a Telegram bot
that reads the athlete's latest Strava ride, summarizes it, and suggests two
training options for the next day.

Files:

- `mvp-spec.md` - product scope, target user, flows, and v1 requirements
- `recommendation-rules-v1.md` - ride analysis logic and next-day suggestion rules
- `technical-architecture.md` - system design, services, data model, and roadmap

Working principles:

- optimize for cycling, not generic endurance training
- use deterministic rules for recommendation selection
- use an LLM for concise explanation and message formatting
- build a narrow MVP before expanding into a full AI coach
