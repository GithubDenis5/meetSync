# MeetSync Architecture

## System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                                Internet / Browser                                  │
└───────────────────────────┬────────────────────────────────────────────────────────┘
                            │
                      ┌─────▼──────┐
                      │  Frontend   │  React SPA, TypeScript, MUI 6
                      │ :3000       │  served via nginx
                      │             │
                      └─────┬──────┘
                            │ HTTP (REST)
                            │
                      ┌─────▼──────────────────────────────────────────────────────┐
                      │                    API Gateway                            │
                      │  FastAPI + httpx reverse proxy                            │
                      │  :8000                                                    │
                      │  Routes: /api/v1/{service}/* → http://{service}:{port}/* │
                      │  Rate limiting, CORS, JWT passthrough                     │
                      └─────┬──────┬───────┬──────┬───────┬───────────────────────┘
                            │      │       │      │       │
         ┌──────────────────┤      │       │      │       └─────────────────────────┐
         │                  │      │       │      │                                 │
    ┌────▼────┐      ┌─────▼────┐ │ ┌─────▼────┐ │  ┌─────────▼──────┐      ┌───────▼──────┐
    │  Auth   │      │   User   │ │ │  Group   │ │  │  Calendar      │      │    Ideas     │
    │ :8001   │      │ :8002    │ │ │ :8003    │ │  │  :8004          │      │  :8005       │
    └─────────┘      └──────────┘ │ └──────────┘ │  └────────────────┘      └──────────────┘
                                  │              │
    ┌─────────┐      ┌──────────┐ │ ┌──────────┐ │  ┌────────────────┐      ┌──────────────┐
    │ Voting  │      │ Meeting  │ │ │  Notif.  │ │  │  Telegram      │      │  Scheduler   │
    │ :8006   │      │ :8011    │ │ │ :8008    │ │  │  :8009          │      │  :8010       │
    └─────────┘      └──────────┘ │ └──────────┘ │  └────────────────┘      └──────────────┘
                                  │              │
                           ┌──────▼──────┐  ┌────▼────────────┐
                           │  Recommend. │  │  PostgreSQL     │
                           │  :8007      │  │  :5432          │
                           └─────────────┘  └─────────────────┘

                           ┌─────────────┐  ┌─────────────────┐  ┌──────────────────────┐
                           │    Redis    │  │    RabbitMQ     │  │  Prometheus/Grafana  │
                           │  :6379      │  │  :5672 / :15672  │  │  :9090 / :3001       │
                           └─────────────┘  └─────────────────┘  └──────────────────────┘
```

**Communication patterns:**
- **Synchronous (REST):** Frontend → Gateway → Microservice. All HTTP calls go through the gateway.
- **Asynchronous (RabbitMQ):** Microservice → Exchange → Queue → Microservice. Events published for side effects.
- **WebSocket:** Notification service maintains persistent connections for real-time updates.
- **Telegram Bot:** Outbound HTTPS to Telegram API (polling mode) or inbound via webhook.

---

## How a Request Flows

```
Browser                  Gateway               Auth Service              Database
  │                        │                       │                       │
  │  POST /api/v1/auth/    │                       │                       │
  │  login {email, pass}   │                       │                       │
  │───────────────────────▶│                       │                       │
  │                        │  POST /auth/login     │                       │
  │                        │──────────────────────▶│                       │
  │                        │                       │  SELECT user by email │
  │                        │                       │──────────────────────▶│
  │                        │                       │◀──────────────────────│
  │                        │                       │                       │
  │                        │                       │  Verify password      │
  │                        │                       │  (bcrypt)             │
  │                        │                       │                       │
  │                        │                       │  Generate JWT         │
  │                        │                       │  Store refresh token  │
  │                        │◀──────────────────────│                       │
  │◀───────────────────────│                       │                       │
  │  {access_token,        │                       │                       │
  │   refresh_token}       │                       │                       │
```

```
Browser                  Gateway               Calendar Service            DB
  │                        │                       │                       │
  │  POST /api/v1/calendar │                       │                       │
  │  /availability         │                       │                       │
  │  {group_id, date,      │                       │                       │
  │   status: "free"}      │                       │                       │
  │───────────────────────▶│──────────────────────▶│──────────────────────▶│
  │                        │                       │  INSERT availability  │
  │                        │                       │◀──────────────────────│
  │                        │                       │                       │
  │                        │                       │  Publish              │
  │                        │                       │  AvailabilityUpdated  │
  │                        │                       │  ───────────────────▶ │
  │                        │                       │     RabbitMQ          │
  │◀───────────────────────│◀──────────────────────│                       │
```

---

## Service Details

### Gateway (:8000)

- **Role:** Single entry point, reverse proxy
- **Tech:** FastAPI + httpx.AsyncClient (30s timeout)
- **Routing:** Path prefix → service URL (e.g. `/api/v1/auth/*` → `http://auth-service:8001/api/v1/auth/*`)
- **Features:** JWT passthrough, rate limiting (60 req/min), CORS, 502 on service unavailable
- **Swagger:** http://localhost:8000/docs

### Auth Service (:8001)

- **Endpoints:** `/register`, `/login`, `/refresh`, `/telegram`, `/logout`, `/me`
- **Auth flow:** bcrypt password hashing → JWT access token (30 min) + refresh token (7 day)
- **Storage:** JWT blacklist in Redis for logout
- **Telegram OAuth:** Link Telegram account via deep link
- **Events published:** `UserRegistered`

### Group Service (:8003)

- **Endpoints:** CRUD groups, `/join`, `/{id}/members`, `/{id}/refresh-invite`
- **Roles:** OWNER (creator), ADMIN, MEMBER
- **Invite system:** Unique alphanumeric invite code per group
- **Events published:** `UserJoinedGroup`, `UserLeftGroup`

### Calendar Service (:8004)

- **Core entity** — personal availability tracking
- **Statuses:** `free`, `busy`, `maybe`
- **Endpoints:** `POST /availability`, `GET /availability/me`, `GET /availability/group`, `GET /availability/user/{id}`, `DELETE /availability/{id}`
- **Events published:** `AvailabilityUpdated`, `AvailabilityConfirmed`

### Ideas Service (:8005)

- **Endpoints:** CRUD ideas, reactions (4 emoji: 👍❤️🔥👎), comments
- **Features:** Archiving, categories, cost levels, tags, location
- **Events published:** `IdeaCreated`, `IdeaArchived`

### Meeting Service (:8011)

- **Endpoints:** CRUD meetings, `/{id}/rsvp`
- **RSVP statuses:** `going`, `not_going`, `maybe` (default: `maybe`)
- **Idea link:** Optional `idea_id` FK — an idea can be scheduled as a meeting
- **Permissions:** Only creator can delete a meeting

### Voting Service (:8006)

- **Endpoints:** CRUD votes, `/{id}/vote`
- **Vote types:** `random` (random ideas pick), `popular` (most reacted), `category`
- **Auto-end:** Timer-based, winner determined by highest votes
- **Events published:** `VotingStarted`, `VotingFinished`

### Notification Service (:8008)

- **Endpoints:** `GET /notifications`, `POST /{id}/read`, `POST /read-all`
- **Channels:** WebSocket (persistent connection) + stored notifications
- **Events consumed:** All major events

### Telegram Service (:8009)

- **Modes:** Long-polling (local dev) or webhook (production)
- **Commands:** `/start` (welcome), `/start <code>` (join group via deep link)
- **Events consumed:** `VotingFinished`, `MeetingPossible`, `ReminderNeeded`, `NotificationSent`
- **Inline buttons:** Dynamic keyboard creation

### Recommendation Service (:8007)

- **Endpoints:** `GET /recommendations`, `GET /weather`
- **Sources:** Open APIs (Ticketmaster, OpenWeather, Google Places — configurable via API keys)
- **Filtering:** By city, category

### Scheduler Service (:8010)

- **Role:** Background task runner
- **Functions:** Daily availability check, meeting proposal when N members are free
- **Events consumed:** `AvailabilityUpdated`, `AvailabilityConfirmed`
- **Events published:** `MeetingPossible`, `ReminderNeeded`, `MeetingCancelled`

---

## Data Flow Diagrams

### 1. Idea → Schedule → RSVP

```
User A                     User B                    Meeting Service
  │                          │                           │
  │──► Ideas Service ◄──► react with emojis              │
  │                          │                           │
  │──► "Schedule" button ────┤                           │
  │       {idea_id, date}    │                           │
  │                          │──► Meeting created ──────►│
  │                          │    {idea_id, title, date} │
  │                          │                           │
  │◄── RSVP (going) ────────┤                           │
  │                          │──► RSVP (maybe) ─────────►│
  │                          │                           │
  │                          │──► RSVP (going) ─────────►│
  │                          │                           │
```

### 2. Availability → Group View

```
User A                Calendar Service             Group Members
  │                        │                           │
  │──► Mark "free" ───────►──► Store availability      │
  │       on Aug 12        │    in database            │
  │                        │                           │
  │                        │──► Publish event ─────────┤
  │                        │   (AvailabilityUpdated)   │
  │                        │                           │
  │◄── Fetch group ────────┤──► Query all users'       │
  │    availability        │    availability for month │
  │                        │                           │
```

### 3. Voting Flow

```
Admin                     Voting Service                Notification          Telegram
  │                           │                             │                    │
  │──► Create vote ──────────►──► Publish VotingStarted ───▶│                    │
  │    (type, duration)       │                             │──► In-app notif ──▶│
  │                           │                             │                    │
  │◄── Vote (pick idea) ─────┤                                                   │
  │                           │                                                   │
  │◄── Vote ─────────────────┤                                                   │
  │                           │                                                   │
  │                           │── (timer expires)                                 │
  │                           │──► Count votes                                    │
  │                           │──► Publish VotingFinished ───────────────────────▶│
  │                           │                             │                    │
  │◄── Winner displayed ─────┤                             │──► Notify winner ──▶│
```

---

## Database ER Diagram

```
┌───────────────┐     ┌──────────────────┐     ┌──────────────────┐
│     users     │     │     groups       │     │   memberships    │
│───────────────│     │──────────────────│     │──────────────────│
│ id (PK)       │◄────│ owner_id (FK)    │────▶│ id (PK)          │
│ name          │     │ id (PK)          │     │ user_id (FK)     │
│ email         │     │ name             │◀────│ group_id (FK)    │
│ password_hash │     │ description      │     │ role (ENUM)      │
│ telegram_id   │     │ invite_code      │     └──────────────────┘
│ timezone      │     │ min_people       │
│ is_active     │     └──────────────────┘
└───────┬───────┘
        │
        │  ┌──────────────────┐     ┌──────────────────┐
        │  │  availability    │     │    meetings      │
        ├──│──────────────────│     │──────────────────│
        │  │ id (PK)          │     │ id (PK)          │
        │  │ user_id (FK)     │     │ group_id (FK)    │
        │  │ group_id (FK)    │     │ idea_id (FK)     │◄───────┐
        │  │ date             │     │ title            │        │
        │  │ status (ENUM)    │     │ date / time      │        │
        │  └──────────────────┘     │ creator_id (FK)──┤        │
        │                           └──────────────────┘        │
        │  ┌──────────────────┐     ┌──────────────────┐        │
        │  │  ideas           │     │ meeting_particip  │        │
        ├──│──────────────────│     │──────────────────│        │
        │  │ id (PK)          │     │ id (PK)          │        │
        │  │ group_id (FK)    │     │ meeting_id (FK)  │        │
        │  │ title            │     │ user_id (FK)     │        │
        │  │ description      │     │ status (ENUM)    │        │
        │  │ category / cost  │     └──────────────────┘        │
        │  │ suggestor_id (FK)│                                  │
        │  │ is_archived      │                                  │
        │  └──────────────────┘                                  │
        │                           ┌──────────────────┐        │
        │  ┌──────────────────┐     │  votes           │        │
        │  │ idea_reactions   │     │──────────────────│        │
        │  │──────────────────│     │ id (PK)          │        │
        │  │ idea_id (FK)     │     │ group_id (FK)    │        │
        │  │ user_id (FK)     │     │ title            │        │
        │  │ reaction (ENUM)  │     │ vote_type (ENUM) │        │
        │  └──────────────────┘     │ ends_at          │        │
        │                           └──────────────────┘        │
        │  ┌──────────────────┐     ┌──────────────────┐        │
        │  │ idea_comments    │     │  vote_options    │        │
        │  │──────────────────│     │──────────────────│        │
        │  │ idea_id (FK)     │     │ idea_id (FK)──────┘       │
        │  │ user_id (FK)     │     │ vote_id (FK)              │
        │  │ text             │     └──────────────────┘        │
        │  └──────────────────┘                                 │
        │                           ┌──────────────────┐        │
        │  ┌──────────────────┐     │  vote_responses  │        │
        │  │ notifications    │     │──────────────────│        │
        │  │──────────────────│     │ vote_id (FK)     │        │
        │  │ id (PK)          │     │ option_id (FK)   │        │
        │  │ user_id (FK)     │     │ user_id (FK)     │        │
        │  │ type / title     │     └──────────────────┘        │
        │  │ is_read          │
        │  └──────────────────┘
        │
        │  ┌──────────────────┐
        │  │ calendars        │
        │  │──────────────────│
        │  │ user_id (FK)     │
        │  │ group_id (FK)    │
        └──│ preferences...   │
           └──────────────────┘
```

---

## Shared Library Structure

```
shared/
├── __init__.py
├── app.py              — FastAPI app factory (CORS, middleware, lifespan)
├── auth.py             — JWT token handling, AuthHandler (Dependency)
├── config.py           — Base settings class (pydantic-settings)
├── database.py         — Async SQLAlchemy engine + session factory
├── exceptions.py       — Common HTTP exceptions
├── logging.py          — JSON logger configuration
├── metrics.py          — Prometheus metrics
├── models/             — SQLAlchemy ORM models
│   ├── user.py
│   ├── group.py
│   ├── calendar.py
│   ├── idea.py
│   ├── vote.py
│   ├── meeting.py
│   ├── notification.py
│   └── __init__.py
├── schemas/            — Pydantic request/response schemas
│   ├── auth.py
│   ├── calendar.py
│   ├── group.py
│   ├── idea.py
│   ├── meeting.py
│   ├── notification.py
│   ├── user.py
│   ├── vote.py
│   └── __init__.py
└── rabbitmq/           — RabbitMQ client + event types
    ├── client.py       — RabbitMQClient class (publish/subscribe)
    ├── events.py       — EventType enum + exchange definitions
    └── __init__.py
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **FastAPI over Flask/Django** | Async-native, OpenAPI auto-docs, Pydantic validation, high performance |
| **SQLAlchemy 2.0 async** | Non-blocking DB access, native `async/await`, `selectinload` for relationships |
| **Per-service database tables** | Each service owns its tables (shared DB, separate schema boundaries) |
| **API Gateway proxy** | Lightweight reverse proxy (not a full API gateway like Kong) — single `httpx` client forwarding requests |
| **RabbitMQ for events** | Reliable delivery, dead-letter queues, persistent exchanges, easy to add consumers |
| **MUI over custom CSS** | Consistent component library, theming system, responsive utilities — reduces frontend maintenance |
| **Frontend nginx proxy** | Serves SPA + proxies `/api/*` to gateway — avoids CORS issues in production |
| **JSON logging to stdout** | Docker-friendly, ready for Loki/Grafana, no file rotation needed |
| **One `.env` for all services** | Simpler than per-service env files — all services load from the same file at runtime |
| **Telegram polling fallback** | No public HTTPS URL needed for local development — auto-fallback from webhook to `getUpdates` |
