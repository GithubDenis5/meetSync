# MeetSync — Roadmap & Development Potential

## Current State (v1.0)

MeetSync is a fully containerized microservice platform for organizing group leisure activities. The current implementation covers:

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

---

## Short-term — v1.1 (Next 1-2 Months)

### 1. Recurring Availability Rules

Allow users to define repeating patterns:

- "Free every Monday"
- "Busy every Friday evening"
- "Free weekdays after 19:00"
- Specific date ranges (vacation mode)

This is the most requested feature and a natural extension of the calendar service.

**Implementation:** Add a `recurring_rules` table linked to calendars. Store iCal-style RRULE or simplified JSON rules. Expand the calendar service to compute effective availability by merging explicit dates with recurring rules.

### 2. Email Notifications

Add email as a secondary notification channel alongside WebSocket and Telegram:

- Email verification on registration
- Digest emails (weekly availability summary)
- Notification of new ideas/votes/meetings

**Implementation:** Add an optional email-service (or extend notification-service) using SendGrid / AWS SES / SMTP. New `EmailSent` event.

### 3. Image Upload

Support images for ideas, meetings, and user avatars:

- Drag-and-drop in the frontend
- Image optimization (resize, format conversion)
- Store on disk (Docker volume) or S3-compatible storage

**Implementation:** Add file upload endpoints, an image proxy service for resizing, and frontend upload components.

### 4. Enhanced Group Dashboard

Per-group statistics:

- Meeting attendance history
- Most popular ideas
- Member activity score
- Availability heatmap (who's free most often)
- "Best time to meet" recommendations

---

## Medium-term — v1.2 (3-6 Months)

### 5. Google Calendar Integration

Two-way sync with Google Calendar:

- Import existing events to mark busy time
- Export meetings as Google Calendar events
- OAuth 2.0 for Google account linking

**Implementation:** New `integration-service` or extend calendar-service. Use Google Calendar API with OAuth2. Architecture already supports this — calendar service is modular.

### 6. Push Notifications (Mobile)

Extend notifications to mobile devices:

- Progressive Web App (PWA) — service worker + push API
- Optionally: native mobile app (React Native / Flutter)

**Implementation:** Frontend already supports PWA basics. Add push subscription endpoints, VAPID keys, and extend notification-service.

### 7. CI/CD Pipeline

Full automation:

- GitHub Actions: lint → test → build → push → deploy
- Automatic Alembic migrations on deployment
- Integration tests in Docker Compose
- Staging environment

**Implementation:** `.github/workflows/` directory with separate workflows for test, build, and deploy.

### 8. Rate Limiting Improvements

Current: simple per-IP rate limiting (60 req/min). Planned upgrades:

- Per-user rate limits (authenticated users get higher limits)
- Per-endpoint limits (auth endpoints more restrictive)
- Distributed rate limiting via Redis (already in place — just needs smarter keys)
- Rate limit headers (X-RateLimit-Remaining, X-RateLimit-Reset)

### 9. Search

Full-text search across ideas and meetings:

- PostgreSQL tsvector columns
- Frontend search bar with real-time suggestions
- Filter by category, date, group, status

---

## Long-term — v2.0 (6-12 Months)

### 10. Mobile App

Native mobile applications:

- **React Native** (share types/API layer with web frontend)
- **Notifications:** Push (FCM/APNs)
- **Features:** Calendar, RSVP, ideas, Telegram deep links

### 11. Kubernetes Deployment

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

### 12. Localization (i18n)

Multi-language support:

- Russian (already partially supported in ТЗ)
- English (current primary)
- Interface language selector
- Locale-aware date formatting, timezones, number formatting

**Implementation:** Use `react-i18next` for frontend, Babel-style locale files for backend error messages.

### 13. Advanced Scheduling

ML-powered scheduling:

- Learn user availability patterns
- Suggest optimal meeting times based on historical data
- Automatic conflict resolution
- "Find the next N available slots across all members"
- Poll-based scheduling ("pick from these 3 dates")

### 14. Event History & Replay

Event sourcing for key flows:

- Store all RabbitMQ events in a dedicated `event_store` table
- Replay capability for recovery
- Audit trail for all actions
- Time-travel debugging ("what was the state on Monday?")

### 15. Webhooks for External Integrations

Allow external services to subscribe to MeetSync events:

- Custom webhook URLs per group
- Event type filtering
- Retry logic with exponential backoff
- Slack, Discord, Microsoft Teams integrations

---

## Long-term — v2.x (12+ Months)

### 16. Activity Feed

- Chronological feed of group activity (ideas, votes, meetings, RSVPs)
- Per-group and global views
- Pinned items
- Archived feed

### 17. Enhanced Groups

- Group categories (friends, work, family, hobby)
- Group discovery (public groups with join requests)
- Subgroups
- Group-level permissions (who can create meetings, who can start votes)

### 18. Premium Features (Monetization)

- **Free tier:** Up to 3 groups, basic features
- **Premium:** Unlimited groups, advanced analytics, Google Calendar sync, priority support
- **Subscription management via Stripe**

### 19. Performance & Reliability

- Database read replicas for calendar/ideas queries
- Redis caching layer for frequently accessed data
- Response compression (gzip/brotli)
- HTTP/2 for frontend
- CDN for static assets
- Database connection pooling (PgBouncer)
- End-to-end testing with Playwright
- Load testing (k6 / Locust)

### 20. Security Hardening

- Security headers (CSP, HSTS, X-Frame-Options)
- Rate limiting per user (vs per IP)
- 2FA / TOTP
- Audit logging
- SQL injection prevention scan
- Dependency vulnerability scanning (Dependabot / Snyk)

---

## Feature Priority Matrix

| Feature | Effort | Impact | Priority |
|---------|--------|--------|----------|
| Recurring availability | Medium | High | P0 — v1.1 |
| Image upload | Medium | High | P0 — v1.1 |
| Email notifications | Low | Medium | P1 — v1.1 |
| Enhanced group dashboard | Low | Medium | P1 — v1.1 |
| Google Calendar sync | High | High | P1 — v1.2 |
| CI/CD pipeline | Medium | High | P1 — v1.2 |
| Push notifications | Medium | High | P1 — v1.2 |
| Search | Medium | Medium | P1 — v1.2 |
| Rate limiting improvements | Low | Medium | P2 — v1.2 |
| Mobile app | Very High | Very High | P2 — v2.0 |
| Kubernetes | High | Medium | P2 — v2.0 |
| i18n | Medium | Medium | P2 — v2.0 |
| Advanced scheduling | High | High | P3 — v2.0 |
| Event history / replay | Medium | Medium | P3 — v2.0 |
| Webhooks | Medium | Medium | P3 — v2.0 |
| Activity feed | Medium | Low | P3 — v2.x |
| Premium features | High | Medium | P3 — v2.x |

---

## Architecture Evolution

### Current (v1.0)

```
Gateway → 11 microservices → PostgreSQL + Redis + RabbitMQ
Frontend → Gateway (proxy)
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
```

---

## Notes

- All priorities are estimates and should be revisited per quarter
- Features marked P0/v1.1 are high-impact, moderate-effort improvements
- Infrastructure features (CI/CD, K8s) enable faster development of all other features
- Google Calendar integration depends on proper OAuth 2.0 infrastructure
- Mobile app development should follow API stabilization (post v1.2)
