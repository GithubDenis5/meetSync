# MeetSync

> Distributed web service for organizing joint leisure activities for groups of friends.

MeetSync helps friend groups brainstorm activity ideas, check each other's availability on a shared calendar, vote on what to do, schedule meetings, and send notifications — all through a modern web UI and a Telegram bot.

---

## Architecture Overview

```
┌──────────────┐      ┌──────────────────────────────────────────┐
│   Frontend   │─────▶│              API Gateway                 │
│  React + MUI │      │           (FastAPI proxy)                │
│  :3000       │      │             :8000                        │
└──────────────┘      └────┬───────┬───────┬───────┬─────────────┘
                           │       │       │       │
              ┌────────────┼───────┼───────┼───────┼────────────────────┐
              ▼            ▼       ▼       ▼       ▼                    │
      ┌────────────┐ ┌────────┐ ┌──────┐ ┌────────────┐               │
      │   Auth     │ │  User  │ │Group │ │  Calendar  │               │
      │  :8001     │ │ :8002  │ │:8003 │ │  :8004     │               │
      └────────────┘ └────────┘ └──────┘ └────────────┘               │
      ┌────────────┐ ┌────────┐ ┌────────────┐ ┌────────────┐        │
      │   Ideas    │ │ Voting │ │  Meeting    │ │Recommend.  │        │
      │  :8005     │ │ :8006  │ │  :8011      │ │  :8007     │        │
      └────────────┘ └────────┘ └────────────┘ └────────────┘        │
      ┌────────────┐ ┌────────────┐ ┌─────────────┐                  │
      │  Notif.    │ │  Telegram  │ │  Scheduler  │                  │
      │  :8008     │ │  :8009     │ │  :8010      │                  │
      └────────────┘ └────────────┘ └─────────────┘                  │
                                                                     │
              ┌──────────┐  ┌──────────┐  ┌──────────┐              │
              │PostgreSQL│  │   Redis  │  │ RabbitMQ │              │
              └──────────┘  └──────────┘  └──────────┘              │
              ┌──────────┐  ┌──────────┐                             │
              │Prometheus│  │  Grafana │◀────────────────────────────┘
              └──────────┘  └──────────┘
```

**18 containers** — 12 microservices, 3 infrastructure (PostgreSQL, Redis, RabbitMQ), 1 frontend, 2 monitoring (Prometheus, Grafana).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **Frontend** | React 19, TypeScript, Vite, Material UI 6 |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis 7 |
| **Message Queue** | RabbitMQ 4 |
| **API Gateway** | FastAPI with httpx proxy (lightweight reverse proxy) |
| **Monitoring** | Prometheus + Grafana |
| **Bot** | Telegram Bot API (long-polling + webhook) |
| **Containerization** | Docker, Docker Compose |
| **Shared Library** | `shared/` — installed as editable package in all services |

---

## Quick Start

### Prerequisites

- Docker and Docker Compose (for local development on Apple Silicon, Docker Desktop 4.30+ or OrbStack recommended)
- Git

### Setup

```bash
# Clone the repository
git clone <repo-url> && cd meetsync

# Copy environment file and customize if needed
cp .env.example .env

# Start all services (this will take a few minutes on first run)
docker compose up -d

# Check that all 18 containers are running
docker compose ps
```

### Verify

| URL | Service |
|-----|---------|
| http://localhost:3000 | Frontend |
| http://localhost:8000/docs | API Gateway Swagger |
| http://localhost:3001 | Grafana (admin / admin) |
| http://localhost:15672 | RabbitMQ Management (meetsync / meetsync) |

### First Run

1. Open http://localhost:3000
2. Register a new account
3. Create a group — an invite code is generated automatically
4. Share the invite code with friends (or open another browser tab and register another user)
5. Start adding ideas, marking calendar availability, and proposing events

---

## Environment Variables

All configuration is in `.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `meetsync` | PostgreSQL database name |
| `POSTGRES_USER` | `meetsync` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `change_me` | PostgreSQL password |
| `JWT_SECRET_KEY` | — | JWT signing secret (change in production!) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token (optional, leave empty to disable) |
| `TELEGRAM_WEBHOOK_URL` | — | Public webhook URL for Telegram (leave empty for polling mode) |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Allowed CORS origins |
| `RATE_LIMIT_PER_MINUTE` | `60` | API rate limit per IP |

Full list in [`.env.example`](.env.example).

---

## Services

### Microservices (12)

| Service | Port | Description |
|---------|------|-------------|
| **gateway** | 8000 | API Gateway — single entry point, proxies to microservices |
| **auth-service** | 8001 | Registration, JWT auth, refresh tokens, Telegram OAuth |
| **user-service** | 8002 | User profiles, settings, avatars |
| **group-service** | 8003 | Groups, memberships, roles (OWNER/ADMIN/MEMBER), invite codes |
| **calendar-service** | 8004 | Personal availability calendar (free/busy/maybe per day) |
| **ideas-service** | 8005 | Idea bank with emoji reactions and comments |
| **voting-service** | 8006 | Voting on ideas (random / popular / by category) |
| **recommendation-service** | 8007 | External API recommendations (events, weather) |
| **notification-service** | 8008 | WebSocket notifications + persistent notification history |
| **telegram-service** | 8009 | Telegram bot — deep-link invites, notifications (long-polling + webhook) |
| **scheduler-service** | 8010 | Scheduled tasks — availability confirmation, meeting proposals |
| **meeting-service** | 8011 | Meeting CRUD, RSVP (going/not_going/maybe) |

### Infrastructure (6)

| Container | Port | Description |
|-----------|------|-------------|
| postgres | 5432 | Primary database |
| redis | 6379 | Cache, JWT blacklist, rate limiting |
| rabbitmq | 5672 / 15672 | Message queue + management UI |
| frontend | 3000 | React SPA (served via nginx) |
| prometheus | 9090 | Metrics collection |
| grafana | 3001 | Monitoring dashboards |

---

## API Routes

All routes go through the Gateway at `/api/v1/{service}/{path}`.

| Prefix | Service | Key Endpoints |
|--------|---------|---------------|
| `/auth` | auth-service | `POST /register`, `POST /login`, `POST /refresh`, `POST /telegram`, `GET /me` |
| `/users` | user-service | `GET /me`, `PATCH /me` |
| `/groups` | group-service | `GET /`, `POST /`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`, `POST /join`, `GET /{id}/members` |
| `/calendar` | calendar-service | `POST /availability`, `GET /availability/me`, `GET /availability/group` |
| `/ideas` | ideas-service | `GET /`, `POST /`, `GET /{id}`, `PATCH /{id}`, `POST /{id}/reactions`, `POST /{id}/comments` |
| `/voting` | voting-service | `GET /`, `POST /`, `GET /{id}`, `POST /{id}/vote` |
| `/meetings` | meeting-service | `GET /`, `POST /`, `GET /{id}`, `POST /{id}/rsvp`, `DELETE /{id}` |
| `/recommendations` | recommendation-service | `GET /`, `GET /weather` |
| `/notifications` | notification-service | `GET /`, `POST /{id}/read`, `POST /read-all` |
| `/telegram` | telegram-service | `POST /send`, `GET /me` |

Every service also has its own Swagger UI at `http://localhost:{port}/docs`.

---

## Database Schema

```
users          — id, name, email, password_hash, telegram_id, timezone, is_active
groups         — id, name, description, invite_code, owner_id, min_people_for_meeting
memberships    — id, user_id, group_id, role (OWNER/ADMIN/MEMBER)
calendars      — id, user_id, group_id (preferences per group)
availability   — id, user_id, group_id, date, status (free/busy/maybe), start_time, end_time
ideas          — id, group_id, title, description, cost, category, photo, tags, location, suggestor_id
idea_reactions — id, idea_id, user_id, reaction (👍❤️🔥👎)
idea_comments  — id, idea_id, user_id, text
votes          — id, group_id, title, vote_type, status, ends_at
vote_options   — id, vote_id, idea_id (links to an idea)
vote_responses — id, vote_id, option_id, user_id
meetings       — id, group_id, idea_id?, title, description, date, time, location, creator_id
meeting_participants — id, meeting_id, user_id, status (going/not_going/maybe)
notifications  — id, user_id, type, title, message, is_read
```

---

## RabbitMQ Events

Services communicate asynchronously via RabbitMQ (topic exchange `meetsync.events`).

| Event | Publisher | Consumers | Description |
|-------|-----------|-----------|-------------|
| `UserRegistered` | auth-service | notification | New user registered |
| `UserJoinedGroup` | group-service | notification | User joined a group via invite |
| `UserLeftGroup` | group-service | notification | User left or was removed |
| `IdeaCreated` | ideas-service | notification | New idea posted |
| `IdeaArchived` | ideas-service | notification | Idea archived or restored |
| `AvailabilityUpdated` | calendar-service | scheduler | User changed their availability |
| `AvailabilityConfirmed` | calendar-service | scheduler | User confirmed availability |
| `MeetingPossible` | scheduler-service | voting, notification, telegram | N people are free → trigger voting |
| `MeetingCancelled` | scheduler-service | notification | Meeting was cancelled |
| `VotingStarted` | voting-service | notification | Voting session opened |
| `VotingFinished` | voting-service | notification, telegram | Voting ended, winner determined |
| `ReminderNeeded` | scheduler-service | telegram | Reminder to mark availability |
| `NotificationSent` | notification-service | — | Notification was delivered |

---

## Useful Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Rebuild a specific service (e.g. frontend)
docker compose up -d --no-deps --build frontend

# Rebuild all services
docker compose build

# View logs (all services)
docker compose logs -f

# View logs for a specific service
docker compose logs -f auth-service

# Check container health
docker compose ps

# Run database migrations (all services)
make migrate

# Open a shell in a container
make shell-auth-service

# Full clean (removes volumes — all data lost!)
docker compose down -v

# Tail all logs with make
make logs
```

---

## Telegram Bot

The Telegram bot works in two modes:

1. **Polling (local dev)** — Leave `TELEGRAM_WEBHOOK_URL` empty in `.env`. The service polls `getUpdates` every 30 seconds.
2. **Webhook (production)** — Set `TELEGRAM_WEBHOOK_URL` to a public HTTPS URL. The service registers the webhook on startup.

### Bot commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/start <invite_code>` | Join a group using an invite code |

### Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
2. Set `TELEGRAM_BOT_TOKEN` in `.env`
3. Restart the telegram service:

```bash
docker compose up -d --no-deps --build telegram-service
```

---

## Key Flows

### 1. Idea → Schedule → RSVP

```
User proposes idea → Others react with emojis
                    → Someone schedules it as a meeting
                    → Group members RSVP (going/not_going/maybe)
```

### 2. Calendar Availability

```
User marks day as Free/Busy/Maybe
                    → Calendar service stores it
                    → Group members can see who's available when
                    → Scheduler suggests optimal dates
```

### 3. Voting

```
Admin starts a vote → Ideas loaded from idea bank
  (random / popular / category)
                     → Members vote within time limit
                     → Winner auto-determined
                     → Winner can be scheduled as a meeting
```

---

## Monitoring

- **Prometheus** collects metrics from all services at `/metrics`
- **Grafana** is pre-configured with Prometheus as a data source (login: `admin` / `admin`)
- All services log structured JSON to stdout (ready for Loki/Grafana)

---

## Project Structure

```
/
├── gateway/              # API Gateway
├── auth-service/         # Auth (JWT, registration)
├── user-service/         # User profiles
├── group-service/        # Groups and memberships
├── calendar-service/     # Availability calendar
├── ideas-service/        # Idea bank
├── voting-service/       # Voting engine
├── meeting-service/      # Meetings and RSVP
├── recommendation-service/ # External recommendations
├── notification-service/ # WebSocket notifications
├── telegram-service/     # Telegram bot
├── scheduler-service/    # Scheduled tasks
├── shared/               # Shared library (models, schemas, config, auth, rabbitmq)
├── frontend/             # React SPA
├── monitoring/           # Prometheus/Grafana config
├── .env.example          # Environment template
├── docker-compose.yml    # Container orchestration
├── Makefile              # Dev commands
└── README.md             # You are here
```

---

## Principles

- **Every service is independent** — its own `app/`, `Dockerfile`, `requirements.txt`, and database tables
- **Communication via REST + RabbitMQ** — synchronous queries through gateway, async events through message queue
- **Configuration from `.env`** — all services read from the same environment file at runtime
- **Persistent volumes** — PostgreSQL, Redis, and RabbitMQ data survive container restarts
- **Token auth** — JWT access + refresh tokens, service-to-service calls validated by shared `AuthHandler`
- **All services have Swagger** at `/docs` for development and testing
