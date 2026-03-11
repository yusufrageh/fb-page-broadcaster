# FB Page Broadcaster

A web app to broadcast AI-rephrased messages to Facebook page contacts via browser automation.

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite + TailwindCSS |
| Backend | Python FastAPI + SQLAlchemy + SQLite |
| Automation | Playwright (headless Chromium) |
| AI | Claude API (message rephrasing) |
| Real-time | WebSockets |

## Features
- Facebook login via browser automation (cookie persistence)
- Scrape all contacts who messaged your page
- Write a primary message → AI auto-rephrases each send uniquely
- Configurable delays (min/max seconds between messages)
- Configurable batch size (max messages per run)
- Real-time broadcast progress via WebSocket
- Start/stop broadcast control
- Full broadcast history with message logs
- Encrypted credential storage

## Implementation Phases

| Phase | Description | Details |
|-------|-------------|---------|
| 1 | Project Setup & Foundation | [phase-1](phases/phase-1-project-setup.md) |
| 2 | Settings & Credential Management | [phase-2](phases/phase-2-settings-and-auth.md) |
| 3 | Facebook Login & Page Selection | [phase-3](phases/phase-3-facebook-pages.md) |
| 4 | Contact Scraping | [phase-4](phases/phase-4-contacts-scraping.md) |
| 5 | Message Composer & AI Rephrasing | [phase-5](phases/phase-5-message-composer.md) |
| 6 | Broadcast Engine & Real-time Progress | [phase-6](phases/phase-6-broadcast-engine.md) |
| 7 | History Page & Final Polish | [phase-7](phases/phase-7-history-and-polish.md) |

## Dashboard Pages
1. **Settings** — FB credentials, Claude API key, delay range, batch size
2. **Pages** — Login to FB, fetch & select managed pages
3. **Compose** — Write primary message, preview AI-generated variants
4. **Broadcast** — Start/stop broadcast, live progress tracking
5. **History** — View past broadcasts and individual message logs
