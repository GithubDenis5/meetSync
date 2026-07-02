# MeetSync — Roadmap & Development Potential

## Current State (v1.0 — Deployed to Production)

MeetSync is a fully containerized microservice platform for organizing group leisure activities, now running in production. The current implementation covers:

- ✅ User registration & JWT auth with refresh tokens
- ✅ Group management with invite codes & roles (OWNER/ADMIN/MEMBER)
- ✅ Personal availability calendar (free/busy/maybe per day)
- ✅ Group availability overview — see who's free when
- ✅ Idea bank with emoji reactions (👍❤️🔥👎) and comments
- ✅ Full voting engine (random/popular/category) with auto-completion
- ✅ Meeting CRUD with RSVP (going/not_going/maybe)
- ✅ Real-time notifications via WebSocket
- ✅ Telegram bot (long-polling + webhook)
- ✅ External recommendations (Ticketmaster, OpenWeather, Google Places)
- ✅ Background scheduler for availability checks
- ✅ Modern responsive UI with dark/light theme
- ✅ Monitoring (Prometheus + Grafana)
- ✅ 18 Docker containers running with a single command

### Production Readiness (Completed v1.0)

- ✅ **HTTPS** — nginx TLS termination with HTTP → HTTPS redirect
- ✅ **Auto-migration** — database schema auto-deploys on first launch, skips if at head
- ✅ **SSL certificates** — self-signed (dev) + Let's Encrypt (prod) scripts
- ✅ **Production Make targets** — `make prod-deploy`, `make ssl-letsencrypt`, etc.
- ✅ **Notification service reliability** — fixed RabbitMQ DNS issue (password URL encoding for special chars)
- ✅ **Retry logic** — notification service connects to RabbitMQ with exponential backoff (10 attempts)
- ✅ **Container restart policy** — `restart: unless-stopped` on notification service
- ✅ **RabbitMQ healthcheck** — switched to `rabbitmq-diagnostics ping` (reliable)
- ✅ **Docker Buildx** — installed on production server for image building

---

## Short-term — v1.1 (Next 1-2 Months)

### 1. Prometheus Metrics for All Services

Currently, Prometheus scrapes all 11 microservices at `/metrics`, but most services return 404. Each service needs a proper `/metrics` endpoint with:

- Request count, latency, error rate histograms
- Active WebSocket connections (notification-service)
- RabbitMQ queue depths
- Database connection pool stats
- Python GC / memory metrics

**Implementation:** Use `prometheus-client` library in each service. Create a shared `metrics.py` module with standard metric definitions. Most services already have `prometheus-client` in their requirements.

Priority: **P0**

### 2. Structured Logging & Log Aggregation

Production logs are currently plain Python logging to stdout. Need:

- JSON-formatted logs (machine-parseable) — all services use `python-json-logger` already
- **Loki + Promtail** for log aggregation (complements Prometheus/Grafana)
- Correlation ID across service boundaries (propagated via HTTP headers)
- Centralized error tracking (Sentry)

**Implementation:** Add Loki and Promtail containers to docker-compose. Add shared log configuration to `shared/` package. Add request ID middleware to gateway.

Priority: **P0**

### 3. Recurring Availability Rules

Allow users to define repeating patterns:

- "Free every Monday"
- "Busy every Friday evening"
- "Free weekdays after 19:00"
- Specific date ranges (vacation mode)

This is the most requested feature and a natural extension of the calendar service.

**Implementation:** Add a `recurring_rules` table linked to calendars. Store iCal-style RRULE or simplified JSON rules. Expand the calendar service to compute effective availability by merging explicit dates with recurring rules.

Priority: **P1**

### 4. Image Upload

Support images for ideas, meetings, and user avatars:

- Drag-and-drop in the frontend
- Image optimization (resize, format conversion)
- Store on disk (Docker volume) or S3-compatible storage

**Implementation:** Add file upload endpoints, an image proxy service for resizing, and frontend upload components.

Priority: **P1**

### 5. Email Notifications

Add email as a secondary notification channel alongside WebSocket and Telegram:

- Email verification on registration
- Digest emails (weekly availability summary)
- Notification of new ideas/votes/meetings

**Implementation:** Add an optional email-service (or extend notification-service) using SendGrid / AWS SES / SMTP. New `EmailSent` event.

Priority: **P1**

### 6. Database Backup Strategy

Production PostgreSQL needs automated backups:

- Daily `pg_dump` to persistent volume or S3
- Point-in-time recovery (WAL archiving)
- Retention policy (7 daily, 4 weekly, 3 monthly)
- Restore script

**Implementation:** Add a `pg-backup` container with cron and `pg_dump`. Or use `wal-g` for WAL-based backups. Document restore procedure.

Priority: **P1**

### 7. Enhanced Group Dashboard

Per-group statistics:

- Meeting attendance history
- Most popular ideas
- Member activity score
- Availability heatmap (who's free most often)
- "Best time to meet" recommendations

Priority: **P2**

---

## Medium-term — v1.2 (3-6 Months)

### 8. CI/CD Pipeline

Full automation:

- GitHub Actions: lint → test → build → push → deploy
- Automatic Alembic migrations on deployment
- Integration tests in Docker Compose
- Staging environment

**Implementation:** `.github/workflows/` directory with separate workflows for test, build, and deploy. Current CI runs `ruff check` + `mypy` (both with `|| true` — make them strict).

Priority: **P1**

### 9. Google Calendar Integration

Two-way sync with Google Calendar:

- Import existing events to mark busy time
- Export meetings as Google Calendar events
- OAuth 2.0 for Google account linking

**Implementation:** New `integration-service` or extend calendar-service. Use Google Calendar API with OAuth2. Architecture already supports this — calendar service is modular.

Priority: **P1**

### 10. Push Notifications (Mobile)

Extend notifications to mobile devices:

- Progressive Web App (PWA) — service worker + push API
- Optionally: native mobile app (React Native / Flutter)

**Implementation:** Frontend already supports PWA basics. Add push subscription endpoints, VAPID keys, and extend notification-service.

Priority: **P1**

### 11. Rate Limiting Improvements

Current: simple per-IP rate limiting (60 req/min). Planned upgrades:

- Per-user rate limits (authenticated users get higher limits)
- Per-endpoint limits (auth endpoints more restrictive)
- Distributed rate limiting via Redis (already in place — just needs smarter keys)
- Rate limit headers (X-RateLimit-Remaining, X-RateLimit-Reset)

Priority: **P2**

### 12. Search

Full-text search across ideas and meetings:

- PostgreSQL tsvector columns
- Frontend search bar with real-time suggestions
- Filter by category, date, group, status

Priority: **P2**

### 13. Service Health & Startup Improvements

From production experience:

- Health endpoint consolidation (all services return DB, Redis, RabbitMQ status)
- Graceful shutdown for all services (handle SIGTERM properly)
- Startup dependency graph (currently uses `depends_on` + healthchecks — could be smarter)
- Auto-healing: if a service crashes N times in 5 minutes, alert instead of infinitely restarting
- `/ready` and `/live` probe separation for Kubernetes readiness

Priority: **P2**

---

## Long-term — v2.0 (6-12 Months)

### 14. Mobile App

Native mobile applications:

- **React Native** (share types/API layer with web frontend)
- **Notifications:** Push (FCM/APNs)
- **Features:** Calendar, RSVP, ideas, Telegram deep links

### 15. Kubernetes Deployment

Production-grade deployment:

- Helm charts for each service
- Horizontal Pod Autoscaling based on CPU/memory
- Service mesh (Istio or Linkerd)
- Blue-green deployments
- Database connection pooling (PgBouncer)
- Read replicas for PostgreSQL

```yaml
# Example scaling profile:
# auth-service:        2-4 replicas (CPU-bound auth)
# calendar-service:    3-6 replicas (most used)
# notification-service: 2-3 replicas (WebSocket connections)
# telegram-service:    1 replica (stateful polling)
```

### 16. Localization (i18n)

Multi-language support:

- Russian (already partially supported in ТЗ)
- English (current primary)
- Interface language selector
- Locale-aware date formatting, timezones, number formatting

**Implementation:** Use `react-i18next` for frontend, Babel-style locale files for backend error messages.

### 17. Advanced Scheduling

ML-powered scheduling:

- Learn user availability patterns
- Suggest optimal meeting times based on historical data
- Automatic conflict resolution
- "Find the next N available slots across all members"
- Poll-based scheduling ("pick from these 3 dates")

### 18. Event History & Replay

Event sourcing for key flows:

- Store all RabbitMQ events in a dedicated `event_store` table
- Replay capability for recovery
- Audit trail for all actions
- Time-travel debugging ("what was the state on Monday?")

### 19. Webhooks for External Integrations

Allow external services to subscribe to MeetSync events:

- Custom webhook URLs per group
- Event type filtering
- Retry logic with exponential backoff
- Slack, Discord, Microsoft Teams integrations

---

## Long-term — v2.x (12+ Months)

### 20. Activity Feed

- Chronological feed of group activity (ideas, votes, meetings, RSVPs)
- Per-group and global views
- Pinned items
- Archived feed

### 21. Enhanced Groups

- Group categories (friends, work, family, hobby)
- Group discovery (public groups with join requests)
- Subgroups
- Group-level permissions (who can create meetings, who can start votes)

### 22. Premium Features (Monetization)

- **Free tier:** Up to 3 groups, basic features
- **Premium:** Unlimited groups, advanced analytics, Google Calendar sync, priority support
- **Subscription management via Stripe**

### 23. Performance & Reliability

- Database read replicas for calendar/ideas queries
- Redis caching layer for frequently accessed data
- Response compression (gzip/brotli)
- HTTP/2 for frontend
- CDN for static assets
- Database connection pooling (PgBouncer)
- End-to-end testing with Playwright
- Load testing (k6 / Locust)

### 24. Security Hardening

- Security headers (CSP, HSTS, X-Frame-Options)
- Rate limiting per user (vs per IP)
- 2FA / TOTP
- Audit logging
- SQL injection prevention scan
- Dependency vulnerability scanning (Dependabot / Snyk)

---

## Feature Priority Matrix

| # | Feature | Effort | Impact | Priority |
|---|---------|--------|--------|----------|
| 1 | Prometheus metrics for all services | Low | High | P0 — v1.1 |
| 2 | Structured logging / Loki | Medium | High | P0 — v1.1 |
| 3 | Database backup strategy | Medium | High | P1 — v1.1 |
| 4 | Service health & startup improvements | Low | Medium | P1 — v1.1 |
| 5 | Recurring availability | Medium | High | P1 — v1.1 |
| 6 | Image upload | Medium | High | P1 — v1.1 |
| 7 | Email notifications | Low | Medium | P1 — v1.1 |
| 8 | CI/CD pipeline | Medium | High | P1 — v1.2 |
| 9 | Google Calendar sync | High | High | P1 — v1.2 |
| 10 | Push notifications | Medium | High | P1 — v1.2 |
| 11 | Search | Medium | Medium | P2 — v1.2 |
| 12 | Rate limiting improvements | Low | Medium | P2 — v1.2 |
| 13 | Enhanced group dashboard | Low | Medium | P2 — v1.1 |
| 14 | Mobile app | Very High | Very High | P2 — v2.0 |
| 15 | Kubernetes | High | Medium | P2 — v2.0 |
| 16 | i18n | Medium | Medium | P2 — v2.0 |
| 17 | Advanced scheduling | High | High | P3 — v2.0 |
| 18 | Event history / replay | Medium | Medium | P3 — v2.0 |
| 19 | Webhooks | Medium | Medium | P3 — v2.0 |
| 20 | Activity feed | Medium | Low | P3 — v2.x |
| 21 | Premium features | High | Medium | P3 — v2.x |

---

## Architecture Evolution

### Current (v1.0 — Production)

```
                          ┌──────────┐
                          │  nginx   │ TLS termination
                          │ :443/:80 │
                          └────┬─────┘
                               │
┌──────────────┐               │      ┌───────────────────┐
│   Frontend   │◄──────────────┘─────▶│     Gateway       │
│  React + MUI │                      │    (FastAPI)      │
└──────────────┘                      └────────┬──────────┘
                                               │
                     ┌─────────────────────────┼─────────────────────┐
                     ▼                         ▼                     ▼
              ┌──────────┐             ┌──────────────┐     ┌──────────────┐
              │PostgreSQL│             │    Redis     │     │   RabbitMQ   │
              │ + Volume  │             │   + Volume   │     │  + DLX       │
              └──────────┘             └──────────────┘     └──────────────┘
                     │                        │                     │
                     └────────────────────────┼─────────────────────┘
                                              │
                              ┌───────────────┴───────────────┐
                              │    11 Microservices +         │
                              │     Migration + Monitoring    │
                              └───────────────────────────────┘
                                              │
                                     ┌───────┴───────┐
                                     │  Prometheus   │
                                     │    Grafana    │
                                     └───────────────┘
```

### Planned (v2.0)

```
CDN → Frontend (load balanced)
                                ┌→ PostgreSQL Primary → Read Replicas
Gateway (multiple instances) → ─┼→ Redis Cluster
                                └→ RabbitMQ Cluster
      │
      ├→ Auth Service (2-4 replicas)
      ├→ Calendar Service (3-6 replicas)
      ├→ Integration Service (Google Calendar)
      ├→ Notification Service (2-3 replicas, WebSocket)
      ├── ... existing services scaled independently
      │
      └→ Logs → Loki → Grafana
      └→ Traces → Tempo / Jaeger
```

---

## Notes

- All priorities are estimates and should be revisited per quarter
- **P0 — v1.1 items** are production-hardening tasks discovered during initial deployment
- Features marked P1/v1.1 are high-impact, moderate-effort improvements
- Infrastructure features (CI/CD, K8s) enable faster development of all other features
- Google Calendar integration depends on proper OAuth 2.0 infrastructure
- Mobile app development should follow API stabilization (post v1.2)
